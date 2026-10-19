"""Runs one Speak program under the debugger.

Started in a VS Code terminal by debug_adapter.py:
    python speak_debug.py <port> <program.speak> [--no-debug]
It connects back to the adapter over a local socket. Messages are JSON lines.
While the program is paused, this process answers questions (stack, variables...)
from the adapter; while it runs, it only listens for new breakpoints.
"""
import json
import os
import select
import socket
import sys
import time
import types

import speak


class Debugger:
    def __init__(self, connection, path, line_map):
        self.sock = connection
        self.buffer = b''
        self.path = path
        self.line_map = line_map
        self.valid_lines = sorted(set(line_map))
        self.breakpoints = set()
        self.mode = 'run'          # run | in | over | out
        self.step_depth = 0
        self.entry_pending = False
        self.current = None
        self.frames = []
        self.refs = {}
        self.next_ref = 1
        self.last_poll = 0.0
        self.previous = None

    # ------------------------------------------------------------ transport

    def send(self, message):
        self.sock.sendall((json.dumps(message) + '\n').encode('utf-8'))

    def next_message(self, block=True):
        while b'\n' not in self.buffer:
            if not block and not select.select([self.sock], [], [], 0)[0]:
                return None
            data = self.sock.recv(65536)
            if not data:
                os._exit(1)  # the adapter went away
            self.buffer += data
        line, self.buffer = self.buffer.split(b'\n', 1)
        return json.loads(line)

    def reply(self, message, body=None, error=None):
        if error is not None:
            self.send({'id': message['id'], 'ok': False, 'error': error})
        else:
            self.send({'id': message['id'], 'ok': True, 'body': body})

    # -------------------------------------------------------------- control

    def wait_for_run(self):
        while True:
            message = self.next_message()
            if message['cmd'] == 'run':
                self.mode = 'in' if message.get('stopOnEntry') else 'run'
                self.entry_pending = self.mode == 'in'
                self.reply(message, {})
                return
            self.handle(message)

    def serve(self):
        """Answers questions until the user resumes the program."""
        while True:
            if self.handle(self.next_message()):
                return

    def poll(self):
        """While running: pick up breakpoint changes without stopping."""
        message = self.next_message(block=False)
        while message is not None:
            self.handle(message)
            message = self.next_message(block=False)

    def depth(self, frame):
        count = 0
        while frame is not None:
            if frame.f_code.co_filename == '<speak>':
                count += 1
            frame = frame.f_back
        return count

    def tracer(self, frame, event, arg):
        return self.on_line if frame.f_code.co_filename == '<speak>' else None

    def on_line(self, frame, event, arg):
        if event != 'line':
            return self.on_line
        now = time.monotonic()
        if now - self.last_poll > 0.2:
            self.last_poll = now
            self.poll()
        line = self.line_map[frame.f_lineno - 1]
        if (id(frame), line) == self.previous:
            return self.on_line  # the same Speak line again (it compiled to several Python lines)
        self.previous = (id(frame), line)
        reason = None
        if self.mode == 'in':
            reason = 'entry' if self.entry_pending else 'step'
        elif self.mode == 'over' and self.depth(frame) <= self.step_depth:
            reason = 'step'
        elif self.mode == 'out' and self.depth(frame) < self.step_depth:
            reason = 'step'
        if line in self.breakpoints:
            reason = 'breakpoint'
        if reason:
            self.entry_pending = False
            self.pause_at(frame, reason)
        return self.on_line

    def pause_at(self, frame, reason, text=None):
        self.current = frame
        self.frames = []
        self.refs = {}
        self.next_ref = 1
        self.send({'event': 'stopped', 'reason': reason, 'text': text})
        self.serve()

    # ------------------------------------------------------------- commands

    def handle(self, message):
        """Runs one command. Returns True when the program should resume."""
        command = message['cmd']
        if command == 'setBreakpoints':
            self.breakpoints = set()
            results = []
            for wanted in message['lines']:
                actual = next((n for n in self.valid_lines if n >= wanted), None)
                if actual is None:
                    results.append({'verified': False, 'line': wanted})
                else:
                    self.breakpoints.add(actual)
                    results.append({'verified': True, 'line': actual})
            self.reply(message, results)
        elif command == 'continue':
            self.mode = 'run'
            return True
        elif command == 'stepIn':
            self.mode = 'in'
            return True
        elif command == 'next':
            self.mode = 'over'
            self.step_depth = self.depth(self.current)
            return True
        elif command == 'stepOut':
            self.mode = 'out'
            self.step_depth = self.depth(self.current)
            return True
        elif command == 'disconnect':
            os._exit(0)
        elif command == 'stackTrace':
            self.reply(message, self.stack_trace())
        elif command == 'scopes':
            frame = self.frames[message['frameId']]
            ref = self.new_ref(('scope', frame))
            self.reply(message, [{'name': 'Variables', 'variablesReference': ref, 'expensive': False}])
        elif command == 'variables':
            self.reply(message, self.variables(message['ref']))
        elif command == 'evaluate':
            self.evaluate(message)
        else:
            self.reply(message, error=f'Unknown command {command}')
        return False

    def stack_trace(self):
        self.frames = []
        frame = self.current
        while frame is not None:
            if frame.f_code.co_filename == '<speak>':
                self.frames.append(frame)
            frame = frame.f_back
        result = []
        for index, frame in enumerate(self.frames):
            name = getattr(frame.f_code, 'co_qualname', frame.f_code.co_name)
            result.append({
                'id': index,
                'name': 'program' if name == '<module>' else name,
                'line': self.line_map[frame.f_lineno - 1],
                'column': 1,
                'source': {'name': os.path.basename(self.path), 'path': self.path},
            })
        return result

    # ------------------------------------------------------------ variables

    def new_ref(self, what):
        ref = self.next_ref
        self.next_ref += 1
        self.refs[ref] = what
        return ref

    def render(self, value):
        try:
            text = '"' + value + '"' if isinstance(value, str) else speak._show(value)
        except Exception:  # noqa: BLE001
            text = '<unprintable>'
        text = ' '.join(text.split())
        if text.startswith('<__main__.') and ' object at ' in text:
            text = type(value).__name__ + ' object'
        return text if len(text) <= 120 else text[:117] + '...'

    def expandable(self, value):
        if isinstance(value, (list, tuple, dict, set)):
            return self.new_ref(('value', value)) if len(value) else 0
        skip = (types.ModuleType, types.FunctionType, types.MethodType, types.BuiltinFunctionType, type)
        if hasattr(value, '__dict__') and not isinstance(value, skip) and vars(value):
            return self.new_ref(('value', value))
        return 0

    def entry(self, name, value):
        return {'name': str(name), 'value': self.render(value), 'type': type(value).__name__,
                'variablesReference': self.expandable(value)}

    def variables(self, ref):
        kind, thing = self.refs[ref]
        if kind == 'scope':
            is_module = thing.f_code.co_name == '<module>'
            hidden = (types.ModuleType, types.FunctionType, type)
            items = [(k, v) for k, v in thing.f_locals.items()
                     if not k.startswith('_') and not (is_module and isinstance(v, hidden))]
            return [self.entry(k, v) for k, v in items]
        if isinstance(thing, dict):
            return [self.entry(speak._inner(k), v) for k, v in list(thing.items())[:100]]
        if isinstance(thing, (list, tuple, set)):
            return [self.entry(f'[{i}]', v) for i, v in enumerate(list(thing)[:100])]
        return [self.entry(k, v) for k, v in vars(thing).items() if not k.startswith('_')]

    def evaluate(self, message):
        index = message.get('frameId')
        frame = self.frames[index] if index is not None and index < len(self.frames) else self.current
        try:
            python = speak.compile_expression(message['expression'])
            value = eval(python, frame.f_globals, frame.f_locals)  # noqa: S307 - the user's own expression
        except speak.SpeakError as error:
            self.reply(message, error=str(error))
            return
        except Exception as error:  # noqa: BLE001
            self.reply(message, error=speak.explain(error))
            return
        self.reply(message, {'result': self.render(value), 'variablesReference': self.expandable(value)})


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except (AttributeError, ValueError):
            pass
    port, path = int(argv[1]), os.path.abspath(argv[2])
    no_debug = '--no-debug' in argv
    connection = socket.create_connection(('127.0.0.1', port))
    sys.path.insert(0, os.path.dirname(path))
    os.chdir(os.path.dirname(path))

    def finish(code):
        try:
            connection.sendall((json.dumps({'event': 'exited', 'code': code}) + '\n').encode())
            connection.close()
        except OSError:
            pass
        return code

    try:
        with open(path, encoding='utf-8') as handle:
            source = handle.read()
        python, line_map = speak.compile_speak(source)
        code = speak.compile_python(python, line_map)
    except speak.SpeakError as error:
        where = f'Line {error.line}: ' if error.line else ''
        print(f'\nSpeak problem in {os.path.basename(path)}\n{where}{error}', file=sys.stderr)
        return finish(1)

    debugger = Debugger(connection, path, line_map)
    debugger.wait_for_run()
    namespace = speak.build_namespace(path)
    if not no_debug:
        sys.settrace(debugger.tracer)
    status = 0
    try:
        exec(code, namespace)
    except (SystemExit, KeyboardInterrupt):
        status = 1
    except Exception as error:  # noqa: BLE001 - reported in plain English
        sys.settrace(None)
        message, line, frame = speak.explain_error(error, python, line_map)
        where = f'Line {line}: ' if line else ''
        print(f'\nSpeak problem in {os.path.basename(path)}\n{where}{message}', file=sys.stderr)
        if frame is not None and not no_debug:
            debugger.pause_at(frame, 'exception', message)
        status = 1
    finally:
        sys.settrace(None)
    return finish(status)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
