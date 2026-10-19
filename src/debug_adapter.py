"""Debug adapter for Speak (Debug Adapter Protocol over stdin/stdout).

VS Code starts this. It asks VS Code to open a terminal that runs speak_debug.py,
so the program can print and ask for input normally, then relays between the two.
"""
import json
import os
import queue
import socket
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))


class DapError(Exception):
    pass


def same_file(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


class Adapter:
    def __init__(self):
        self.seq = 0
        self.write_lock = threading.Lock()
        self.target = None
        self.pending = {}
        self.target_id = 0
        self.program = ''
        self.no_debug = False
        self.stop_on_entry = False
        self.finished = False
        self.exiting = False

    # ------------------------------------------------------------------ DAP

    def send(self, message):
        with self.write_lock:
            self.seq += 1
            message['seq'] = self.seq
            body = json.dumps(message).encode('utf-8')
            sys.stdout.buffer.write(f'Content-Length: {len(body)}\r\n\r\n'.encode() + body)
            sys.stdout.buffer.flush()

    def event(self, name, body=None):
        self.send({'type': 'event', 'event': name, 'body': body or {}})

    def read_message(self):
        headers = {}
        while True:
            line = sys.stdin.buffer.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                break
            key, _, value = line.decode().partition(':')
            headers[key.lower()] = value.strip()
        return json.loads(sys.stdin.buffer.read(int(headers['content-length'])))

    def run(self):
        while not self.exiting:
            message = self.read_message()
            if message is None:
                break
            if message.get('type') == 'request':
                self.handle(message)

    def handle(self, request):
        command = request['command']
        handler = getattr(self, 'on_' + command, None)
        try:
            if handler is None:
                raise DapError(f'Speak does not support "{command}".')
            body = handler(request.get('arguments') or {})
            self.send({'type': 'response', 'request_seq': request['seq'], 'success': True,
                       'command': command, 'body': body or {}})
        except DapError as error:
            self.send({'type': 'response', 'request_seq': request['seq'], 'success': False,
                       'command': command, 'message': str(error),
                       'body': {'error': {'id': 1, 'format': str(error), 'showUser': True}}})

    # --------------------------------------------------------------- target

    def ask(self, command, **arguments):
        if self.target is None or self.finished:
            raise DapError('The Speak program has finished.')
        self.target_id += 1
        answer = queue.Queue(1)
        self.pending[self.target_id] = answer
        try:
            self.target.sendall((json.dumps({'id': self.target_id, 'cmd': command, **arguments}) + '\n').encode())
        except OSError:
            raise DapError('The Speak program has finished.') from None
        try:
            reply = answer.get(timeout=30)
        except queue.Empty:
            raise DapError('The Speak program did not answer. It may be waiting for input.') from None
        if not reply.get('ok'):
            raise DapError(reply.get('error') or 'Something went wrong.')
        return reply.get('body')

    def tell(self, command, **arguments):
        if self.target is None or self.finished:
            return
        try:
            self.target.sendall((json.dumps({'id': 0, 'cmd': command, **arguments}) + '\n').encode())
        except OSError:
            pass

    def listen_to_target(self):
        reader = self.target.makefile('rb')
        for line in reader:
            message = json.loads(line)
            if message.get('event') == 'stopped':
                self.event('stopped', {'reason': message['reason'], 'threadId': 1,
                                       'allThreadsStopped': True, 'text': message.get('text') or ''})
            elif message.get('event') == 'exited':
                self.finish(message.get('code', 0))
            elif 'id' in message and message['id'] in self.pending:
                self.pending.pop(message['id']).put(message)
        self.finish(0)

    def finish(self, code):
        if self.finished:
            return
        self.finished = True
        self.event('exited', {'exitCode': code})
        self.event('terminated')

    # ------------------------------------------------------------- requests

    def on_initialize(self, args):
        return {'supportsConfigurationDoneRequest': True, 'supportsEvaluateForHovers': True,
                'supportsTerminateRequest': True}

    def on_launch(self, args):
        if not args.get('program'):
            raise DapError('No program to run. Set "program" in your launch configuration.')
        self.program = os.path.abspath(args['program'])
        if not os.path.isfile(self.program):
            raise DapError(f'I could not find "{self.program}".')
        self.no_debug = bool(args.get('noDebug'))
        self.stop_on_entry = bool(args.get('stopOnEntry'))
        server = socket.socket()
        server.bind(('127.0.0.1', 0))
        server.listen(1)
        command = [sys.executable, os.path.join(HERE, 'speak_debug.py'), str(server.getsockname()[1]), self.program]
        if self.no_debug:
            command.append('--no-debug')
        self.send({'type': 'request', 'command': 'runInTerminal', 'arguments': {
            'kind': 'integrated', 'title': 'Speak', 'cwd': args.get('cwd') or os.path.dirname(self.program),
            'args': command}})
        server.settimeout(30)
        try:
            self.target, _ = server.accept()
        except socket.timeout:
            raise DapError('The Speak program did not start. Check that Python can run.') from None
        finally:
            server.close()
        threading.Thread(target=self.listen_to_target, daemon=True).start()
        self.event('initialized')

    def on_setBreakpoints(self, args):
        wanted = [b['line'] for b in args.get('breakpoints', [])]
        path = (args.get('source') or {}).get('path')
        if not wanted:
            self.ask('setBreakpoints', lines=[]) if path and same_file(path, self.program) else None
            return {'breakpoints': []}
        if not path or not same_file(path, self.program):
            return {'breakpoints': [{'verified': False, 'line': n,
                                     'message': 'Only the file being run can have breakpoints.'} for n in wanted]}
        return {'breakpoints': self.ask('setBreakpoints', lines=wanted)}

    def on_setExceptionBreakpoints(self, args):
        return {}

    def on_configurationDone(self, args):
        self.tell('run', stopOnEntry=self.stop_on_entry)

    def on_threads(self, args):
        return {'threads': [{'id': 1, 'name': 'Speak program'}]}

    def on_stackTrace(self, args):
        frames = self.ask('stackTrace')
        return {'stackFrames': frames, 'totalFrames': len(frames)}

    def on_scopes(self, args):
        return {'scopes': self.ask('scopes', frameId=args['frameId'])}

    def on_variables(self, args):
        return {'variables': self.ask('variables', ref=args['variablesReference'])}

    def on_evaluate(self, args):
        return self.ask('evaluate', expression=args['expression'], frameId=args.get('frameId'))

    def on_continue(self, args):
        self.tell('continue')
        return {'allThreadsContinued': True}

    def on_next(self, args):
        self.tell('next')

    def on_stepIn(self, args):
        self.tell('stepIn')

    def on_stepOut(self, args):
        self.tell('stepOut')

    def on_disconnect(self, args):
        self.tell('disconnect')
        self.exiting = True

    on_terminate = on_disconnect


if __name__ == '__main__':
    Adapter().run()
