// extension.js — Cabin Panel VS Code extension
// Starts the panel_server subprocess and opens a webview that talks to it.
const vscode = require('vscode');
const cp = require('child_process');
const path = require('path');
const fs = require('fs');

const PANEL_PORT = parseInt(process.env.CABIN_PANEL_PORT || '7771', 10);

let serverProcess = null;
let panel = null;

function findPython(extensionRoot) {
  // extensionRoot is cabin-panel/; the venv lives in its parent (Mycroft/)
  const cabinRoot = path.join(extensionRoot, '..');
  const candidates = [
    path.join(cabinRoot, '.venv', 'Scripts', 'python.exe'),
    path.join(cabinRoot, '.venv', 'bin', 'python'),
    path.join(cabinRoot, '.venv', 'bin', 'python3'),
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  return 'python';
}

function startServer(workspaceRoot, extensionRoot) {
  if (serverProcess) return;
  const python  = findPython(extensionRoot);
  const cabinCwd = path.join(extensionRoot, '..');  // Mycroft/ — where cabin package lives
  serverProcess = cp.spawn(
    python,
    ['-m', 'cabin.panel_server', '--port', String(PANEL_PORT), '--root', workspaceRoot],
    { cwd: cabinCwd, stdio: ['ignore', 'pipe', 'pipe'] }
  );
  serverProcess.stdout.on('data', d => console.log('[cabin-panel]', d.toString().trim()));
  serverProcess.stderr.on('data', d => console.error('[cabin-panel]', d.toString().trim()));
  serverProcess.on('exit', code => {
    console.log(`[cabin-panel] server exited (${code})`);
    serverProcess = null;
  });
}

function stopServer() {
  if (serverProcess) {
    serverProcess.kill();
    serverProcess = null;
  }
}

function getWebviewContent(webview, extensionUri) {
  const u = (file) => webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'media', file));
  const nonce = Math.random().toString(36).slice(2);

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="Content-Security-Policy"
    content="default-src 'none';
             style-src ${webview.cspSource} 'unsafe-inline';
             script-src ${webview.cspSource} 'nonce-${nonce}';
             connect-src http://127.0.0.1:${PANEL_PORT};">
  <link rel="stylesheet" href="${u('style.css')}">
  <title>Cabin</title>
</head>
<body>
  <div id="cabin-panel"></div>
  <script nonce="${nonce}">window.__CABIN_SERVER__ = 'http://127.0.0.1:${PANEL_PORT}';</script>
  <script nonce="${nonce}" src="${u('components/hearth.js')}"></script>
  <script nonce="${nonce}" src="${u('components/notifications.js')}"></script>
  <script nonce="${nonce}" src="${u('components/forest.js')}"></script>
  <script nonce="${nonce}" src="${u('components/buckets.js')}"></script>
  <script nonce="${nonce}" src="${u('components/seam.js')}"></script>
  <script nonce="${nonce}" src="${u('layout.js')}"></script>
  <script nonce="${nonce}" src="${u('main.js')}"></script>
</body>
</html>`;
}

function openPanel(context) {
  if (panel) {
    panel.reveal(vscode.ViewColumn.Two);
    return;
  }

  panel = vscode.window.createWebviewPanel(
    'cabinPanel',
    'Cabin',
    vscode.ViewColumn.Two,
    {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.joinPath(context.extensionUri, 'media')],
      retainContextWhenHidden: true,
    }
  );

  panel.webview.html = getWebviewContent(panel.webview, context.extensionUri);

  panel.onDidDispose(() => { panel = null; }, null, context.subscriptions);
}

function activate(context) {
  // Commands are registered unconditionally — palette shows them, they work
  // even before a workspace folder is confirmed.
  context.subscriptions.push(
    vscode.commands.registerCommand('cabin.openPanel', () => {
      const root = getWorkspaceRoot();
      if (!root) {
        vscode.window.showWarningMessage('Cabin: open a workspace folder first.');
        return;
      }
      ensureServer(root, context.extensionUri.fsPath);
      openPanel(context);
    }),

    vscode.commands.registerCommand('cabin.sendHound', async () => {
      const root = getWorkspaceRoot();
      if (!root) {
        vscode.window.showWarningMessage('Cabin: open a workspace folder first.');
        return;
      }
      ensureServer(root, context.extensionUri.fsPath);
      const reason = await vscode.window.showInputBox({
        prompt: 'What should the hound look for? (optional)',
        placeHolder: 'leave blank for a general dusk sweep',
      });
      if (reason === undefined) return;
      try {
        const res = await fetch(`http://127.0.0.1:${PANEL_PORT}/hound`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reason: reason || '' }),
        });
        const data = await res.json();
        if (data.ok) {
          vscode.window.showInformationMessage('Hound returned. Pulse saved.');
          if (panel) panel.webview.html = getWebviewContent(panel.webview, context.extensionUri);
        } else {
          vscode.window.showWarningMessage(`Hound: ${data.error || 'no output'}`);
        }
      } catch (e) {
        vscode.window.showErrorMessage(`Cabin panel server unreachable: ${e.message}`);
      }
    })
  );

  // Auto-start server + open panel if this workspace has a .cabin/
  const root = getWorkspaceRoot();
  if (root) {
    ensureServer(root, context.extensionUri.fsPath);
    const cabinDir = path.join(root, '.cabin');
    if (fs.existsSync(cabinDir)) {
      setTimeout(() => openPanel(context), 1500);
    }
  }
}

function getWorkspaceRoot() {
  const folders = vscode.workspace.workspaceFolders;
  return folders && folders.length > 0 ? folders[0].uri.fsPath : null;
}

function ensureServer(workspaceRoot, extensionRoot) {
  if (!serverProcess) {
    startServer(workspaceRoot, extensionRoot);
  }
}

function deactivate() {
  stopServer();
}

module.exports = { activate, deactivate };
