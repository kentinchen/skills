# VSIX 插件骨架（用于 TraeCode / VS Code 市场分发）

> 如果你想把本插件包**上架到 VS Code / TraeCode 插件市场**，让别人在扩展面板里搜索并一键安装，这一节提供最小可运行骨架。
> 参考社区实践：[【Code With SOLO】用 SOLO 做一个把 superpowers 娶回 TRAE 家的插件](https://forum.trae.cn/t/topic/16485)

## 目录结构

```
local-skills-bundle-vsix/
├── package.json          # vsix 清单 (name / publisher / contributes / activationEvents)
├── README.md             # 面向插件市场的英文说明
├── CHANGELOG.md
├── LICENSE.txt
├── icon.png              # 128x128
├── src/
│   └── extension.js      # 入口: onStartupFinished 时把 skills/ 复制到项目 .trae/skills
├── scripts/
│   └── update-from-repo.js   # 命令: Skills Bundle: Update from D:\project\skills
└── skills/               # 复制整个 9 个 skill 目录进来, 打包进 vsix (离线可用)
    ├── cpolar-tunnel/
    ├── dddd-ocr/
    └── ...
```

## package.json 最小样例

```json
{
  "name": "local-skills-bundle",
  "displayName": "Local Skills Bundle",
  "description": "9 local skills (cpolar, ddddocr, knowbase-ingest, nezha, scop, wct, yg, yw, zcm) with one-click install to project .trae/skills on open.",
  "version": "1.0.0",
  "publisher": "your-publisher-id",
  "engines": { "vscode": "^1.85.0" },
  "categories": ["Other", "Machine Learning"],
  "activationEvents": ["onStartupFinished"],
  "main": "./src/extension.js",
  "contributes": {
    "commands": [
      {
        "command": "localSkillsBundle.installToWorkspace",
        "title": "Skills Bundle: Install to Current Workspace (.trae/skills)"
      },
      {
        "command": "localSkillsBundle.updateFromRepo",
        "title": "Skills Bundle: Update from Local Repo"
      }
    ]
  },
  "scripts": {
    "package": "vsce package --out local-skills-bundle.vsix",
    "publish": "vsce publish"
  },
  "devDependencies": {
    "@types/vscode": "^1.85.0",
    "vsce": "^2.15.0"
  }
}
```

## src/extension.js 入口逻辑

```js
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
  // 每次打开工作区自动安装（幂等，会覆盖为打包版本）
  const ws = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
  if (ws) {
    try {
      const n = installSkillsToWorkspace(ws);
      vscode.window.showInformationMessage(`Skills Bundle: Installed ${n} skills to .trae/skills`);
    } catch (e) {
      vscode.window.showErrorMessage(`Skills Bundle install failed: ${e.message}`);
    }
  }

  context.subscriptions.push(
    vscode.commands.registerCommand('localSkillsBundle.installToWorkspace', () => {
      const ws = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
      if (!ws) return vscode.window.showWarningMessage('No workspace opened');
      const n = installSkillsToWorkspace(ws);
      vscode.window.showInformationMessage(`Installed ${n} skills. Restart TraeCode to load.`);
    }),

    vscode.commands.registerCommand('localSkillsBundle.updateFromRepo', async () => {
      const src = await vscode.window.showInputBox({
        prompt: 'Local skills repo root (containing SKILL.md subdirs)',
        value: 'D:\\project\\skills'
      });
      if (!src || !fs.existsSync(src)) return vscode.window.showErrorMessage('Invalid path');
      const pluginSkills = path.join(__dirname, '..', 'skills');
      SKILL_NAMES.forEach(n => copyDirRecursive(path.join(src, n), path.join(pluginSkills, n)));
      vscode.window.showInformationMessage('Updated bundled skills from repo.');
    })
  );
}

exports.activate = activate;
```

## 打包/发布命令

```bash
# 安装 vsce (一次即可)
npm install -g @vscode/vsce

# 在 vsix-scaffold/ 目录
npm install
vsce package          # 生成 local-skills-bundle-1.0.0.vsix
vsce publish          # 发布到 VS Code / TraeCode 市场
```

生成的 `.vsix` 文件可以直接发给别人：在 TraeCode 里打开扩展面板 → `...` 菜单 → **Install from VSIX…**，选择文件即可完成安装。**插件激活后会自动把 9 个 Skill 复制到当前打开项目的 `.trae/skills/`，不用手动拷贝。**

## 方案对比（选哪个？）

| 方案 | 适合场景 | 优点 | 缺点 |
|---|---|---|---|
| ① ZIP + `install.ps1/.sh`（本文默认） | 本地 / 小团队 / 内网分享 | 零构建、零依赖、支持软链接同步源仓库 | 对方需手动解压 + 跑脚本 |
| ② `.vsix` 插件 | 上架 TraeCode 市场 / 大范围分发 | 安装体验最好（IDE 内搜索安装），打开项目自动安装 | 要打包、要 publisher ID、TraeWork 桌面版不直接吃 vsix |
| ③ Git 仓库 + README 指引 | 团队内部、版本号/更新频繁 | 更新方便、可追溯 | 同事需要 Git 基础 |

**建议**：目前直接用方案 ① 即可（README 里已经写好 ZIP 打包命令），需要面向大量 TraeCode 用户分发时再走方案 ②。
