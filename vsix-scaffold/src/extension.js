const vscode = require('vscode');
const path   = require('path');
const fs     = require('fs');

const SKILL_NAMES = [
  'cpolar-tunnel','dddd-ocr','knowbase-ingest','nazha-skills',
  'scop-report','wct-skill-publish','yg-skills','yw-skills','zcm-task-add-comment'
];

function copyDirRecursive(src, dst) {
  if (!fs.existsSync(dst)) fs.mkdirSync(dst, { recursive: true });
  for (const ent of fs.readdirSync(src, { withFileTypes: true })) {
    if (ent.name === '__pycache__' || ent.name.endsWith('.pyc')) continue;
    const s = path.join(src, ent.name);
    const d = path.join(dst, ent.name);
    if (ent.isDirectory()) copyDirRecursive(s, d);
    else fs.copyFileSync(s, d);
  }
}

function installSkillsToWorkspace(wsRoot) {
  const pluginSkills = path.join(__dirname, '..', 'skills');
  const projectSkills = path.join(wsRoot, '.trae', 'skills');
  fs.mkdirSync(projectSkills, { recursive: true });
  let ok = 0;
  for (const name of SKILL_NAMES) {
    copyDirRecursive(path.join(pluginSkills, name), path.join(projectSkills, name));
    ok++;
  }
  return ok;
}

function activate(context) {
  const ws = vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0]
    ? vscode.workspace.workspaceFolders[0].uri.fsPath : null;
  if (ws) {
    try {
      const n = installSkillsToWorkspace(ws);
      vscode.window.showInformationMessage('Skills Bundle: Installed ' + n + ' skills to .trae/skills');
    } catch (e) {
      vscode.window.showErrorMessage('Skills Bundle install failed: ' + e.message);
    }
  }

  context.subscriptions.push(
    vscode.commands.registerCommand('localSkillsBundle.installToWorkspace', () => {
      const ws = vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0]
        ? vscode.workspace.workspaceFolders[0].uri.fsPath : null;
      if (!ws) return vscode.window.showWarningMessage('No workspace opened');
      const n = installSkillsToWorkspace(ws);
      vscode.window.showInformationMessage('Installed ' + n + ' skills. Restart TraeCode to load.');
    }),

    vscode.commands.registerCommand('localSkillsBundle.updateFromRepo', async () => {
      const src = await vscode.window.showInputBox({
        prompt: 'Local skills repo root (containing SKILL.md subdirs)',
        value: 'D:\\project\\skills'
      });
      if (!src || !fs.existsSync(src)) return vscode.window.showErrorMessage('Invalid path');
      const pluginSkills = path.join(__dirname, '..', 'skills');
      SKILL_NAMES.forEach(function(n) {
        copyDirRecursive(path.join(src, n), path.join(pluginSkills, n));
      });
      vscode.window.showInformationMessage('Updated bundled skills from repo.');
    })
  );
}

exports.activate = activate;
exports.deactivate = function() {};
