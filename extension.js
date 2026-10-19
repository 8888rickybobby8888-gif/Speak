'use strict';
const vscode = require('vscode');
const path = require('path');
const { spawn } = require('child_process');

// The command to start Python with, as a list: the setting, then the interpreter
// picked in the Python extension, then plain "python".
async function findPython(uri) {
  const configured = vscode.workspace.getConfiguration('speak').get('pythonPath');
  if (configured) return [configured];
  try {
    const python = vscode.extensions.getExtension('ms-python.python');
    if (python) {
      const api = python.isActive ? python.exports : await python.activate();
      const details = api.settings.getExecutionDetails(uri);
      if (details && details.execCommand && details.execCommand.length) return details.execCommand;
    }
  } catch (e) {
    // fall through to the default
  }
  return ['python'];
}

const quote = part => (/\s/.test(part) && !part.startsWith('"') ? `"${part}"` : part);

function activeSpeakEditor() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.languageId !== 'speak') {
    vscode.window.showWarningMessage('Open a .speak file first.');
    return undefined;
  }
  return editor;
}

// Runs "speak.py --check-json" on the text and resolves with [{line, message}].
function checkText(python, runner, text) {
  return new Promise((resolve, reject) => {
    const [command, ...leading] = python;
    const child = spawn(command, [...leading, runner, '--check-json'], { windowsHide: true });
    let output = '';
    const timer = setTimeout(() => { child.kill(); reject(new Error('The check took too long.')); }, 15000);
    child.stdout.on('data', chunk => { output += chunk; });
    child.on('error', error => { clearTimeout(timer); reject(error); });
    child.on('close', () => {
      clearTimeout(timer);
      try { resolve(JSON.parse(output)); } catch (e) { reject(new Error('The check gave no answer.')); }
    });
    child.stdin.on('error', () => {});
    child.stdin.end(Buffer.from(text, 'utf8'));
  });
}

// "Did you mean "print"?" in a problem message becomes a quick fix.
const SUGGESTION = /"([^"]+)"[^"]*Did you mean "([^"]+)"\?/;

const escapeRegex = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

function activate(context) {
  const runner = path.join(context.extensionPath, 'src', 'speak.py');
  const adapter = path.join(context.extensionPath, 'src', 'debug_adapter.py');
  const diagnostics = vscode.languages.createDiagnosticCollection('speak');
  const versions = new Map();
  const timers = new Map();
  let warnedAboutPython = false;
  let terminal;

  async function check(document) {
    if (document.languageId !== 'speak') return;
    const key = document.uri.toString();
    if (!vscode.workspace.getConfiguration('speak').get('checkWhileTyping', true)) {
      diagnostics.delete(document.uri);
      return;
    }
    const version = (versions.get(key) || 0) + 1;
    versions.set(key, version);
    try {
      const python = await findPython(document.uri);
      const problems = await checkText(python, runner, document.getText());
      if (versions.get(key) !== version) return; // the text changed again while checking
      diagnostics.set(document.uri, problems.map(problem => {
        const lineNumber = Math.min(Math.max(problem.line - 1, 0), document.lineCount - 1);
        const line = document.lineAt(lineNumber);
        const range = new vscode.Range(lineNumber, line.firstNonWhitespaceCharacterIndex, lineNumber, line.text.length);
        const diagnostic = new vscode.Diagnostic(range, problem.message, vscode.DiagnosticSeverity.Error);
        diagnostic.source = 'Speak';
        return diagnostic;
      }));
    } catch (error) {
      if (!warnedAboutPython) {
        warnedAboutPython = true;
        vscode.window.showWarningMessage(
          `Speak could not check this file (${error.message}). Is Python installed? You can set "speak.pythonPath".`);
      }
    }
  }

  function checkSoon(document) {
    if (document.languageId !== 'speak') return;
    const key = document.uri.toString();
    clearTimeout(timers.get(key));
    timers.set(key, setTimeout(() => check(document), 350));
  }

  context.subscriptions.push(
    diagnostics,
    vscode.workspace.onDidOpenTextDocument(check),
    vscode.workspace.onDidSaveTextDocument(check),
    vscode.workspace.onDidChangeTextDocument(event => checkSoon(event.document)),
    vscode.workspace.onDidCloseTextDocument(document => {
      diagnostics.delete(document.uri);
      versions.delete(document.uri.toString());
    }),
    vscode.workspace.onDidChangeConfiguration(event => {
      if (event.affectsConfiguration('speak')) vscode.workspace.textDocuments.forEach(check);
    }),

    vscode.languages.registerCodeActionsProvider('speak', {
      provideCodeActions(document, range, codeContext) {
        const actions = [];
        for (const diagnostic of codeContext.diagnostics) {
          const match = SUGGESTION.exec(diagnostic.message);
          if (!match) continue;
          const [, wrong, suggestion] = match;
          const line = document.lineAt(diagnostic.range.start.line);
          const found = new RegExp(`\\b${escapeRegex(wrong)}\\b`).exec(line.text);
          if (!found) continue;
          const action = new vscode.CodeAction(`Change to "${suggestion}"`, vscode.CodeActionKind.QuickFix);
          action.edit = new vscode.WorkspaceEdit();
          action.edit.replace(document.uri,
            new vscode.Range(line.lineNumber, found.index, line.lineNumber, found.index + wrong.length), suggestion);
          action.diagnostics = [diagnostic];
          action.isPreferred = true;
          actions.push(action);
        }
        return actions;
      },
    }, { providedCodeActionKinds: [vscode.CodeActionKind.QuickFix] }),

    vscode.commands.registerCommand('speak.runFile', async () => {
      const editor = activeSpeakEditor();
      if (!editor) return;
      await editor.document.save();
      const python = (await findPython(editor.document.uri)).map(quote).join(' ');
      if (!terminal || terminal.exitStatus) terminal = vscode.window.createTerminal('Speak');
      terminal.show(true);
      const shell = (vscode.env.shell || '').toLowerCase();
      const prefix = shell.includes('powershell') || shell.includes('pwsh') ? '& ' : '';
      terminal.sendText(`${prefix}${python} "${runner}" "${editor.document.fileName}"`);
    }),

    vscode.commands.registerCommand('speak.debugFile', async () => {
      const editor = activeSpeakEditor();
      if (!editor) return;
      await editor.document.save();
      vscode.debug.startDebugging(undefined, {
        type: 'speak', request: 'launch', name: 'Debug Speak file', program: editor.document.fileName,
      });
    }),

    vscode.debug.registerDebugConfigurationProvider('speak', {
      // Lets F5 work on a .speak file without any launch.json.
      resolveDebugConfiguration(folder, config) {
        if (!config.type && !config.request && !config.name) {
          const editor = vscode.window.activeTextEditor;
          if (!editor || editor.document.languageId !== 'speak') return undefined;
          return { type: 'speak', request: 'launch', name: 'Debug Speak file', program: editor.document.fileName };
        }
        if (!config.program) config.program = '${file}';
        return config;
      },
    }),

    vscode.debug.registerDebugAdapterDescriptorFactory('speak', {
      async createDebugAdapterDescriptor() {
        const uri = vscode.window.activeTextEditor && vscode.window.activeTextEditor.document.uri;
        const [command, ...leading] = await findPython(uri);
        return new vscode.DebugAdapterExecutable(command, [...leading, adapter]);
      },
    }),

    vscode.window.onDidCloseTerminal(t => { if (t === terminal) terminal = undefined; })
  );

  vscode.workspace.textDocuments.forEach(check); // files that were already open
}

function deactivate() {}

module.exports = { activate, deactivate };
