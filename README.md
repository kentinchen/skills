# Local Skills Bundle

9 个常用技能的**一键安装插件包**，支持 **TraeWork（桌面/网页版）**、**TraeCode（IDE）**、**TraeCode CLI**。

- 源：[manifest.json](file:///d:/project/skills/manifest.json)
- Windows 安装器：[install.ps1](file:///d:/project/skills/install.ps1)
- Linux/macOS 安装器：[install.sh](file:///d:/project/skills/install.sh)
- 纯软链接脚本（高级用户）：[link-skills.ps1](file:///d:/project/skills/link-skills.ps1) / [link-skills.sh](file:///d:/project/skills/link-skills.sh)

---

## 包含的技能

| # | 目录名 | Skill 名 | 版本 | 用途 |
|---|--------|----------|------|------|
| 1 | cpolar-tunnel | cpolar-tunnel | 1.0.0 | cpolar SSH 隧道 / 单层 & 双层动态代理 |
| 2 | dddd-ocr | dddd-ocr | 1.0.0 | 图片验证码、滑动验证码、目标检测（ddddocr-fastapi） |
| 3 | knowbase-ingest | knowbase-ingest | 1.0.0 | Karpathy 风格个人知识库 Ingest 流水线 |
| 4 | nazha-skills | nazha-skills | 1.0.0 | 哪吒监控 (Nezha) 登录 & 服务器查询 |
| 5 | scop-report | scop-report | 1.0.0 | 黑鸭子 SCOP 组件扫描 + CVE 情报生成报告 |
| 6 | wct-skill-publish | wct-skill-publish | 1.0.0 | WCT 技能市场（dc.iwhalecloud.com）发布与更新 |
| 7 | yg-skills | yg-services | 2.0.0 | 云管 YG 系统：通知 / 工单 / 监控 / 资源 / 文件 / 账单 / 客户 |
| 8 | yw-skills | yw-services | 1.1.0 | 云网 YW 系统：SSO 登录 / APP token / 工单 / 系统清单 |
| 9 | zcm-task-add-comment | zcm-task-add-comment | 1.0.0 | 浩鲸研发云 ZCM 单子（需求/任务/缺陷）加评论 |

---

## 三种安装方式（任选其一）

### 方式 1：全局软链接（推荐，支持 9 个 Skill 自动同步源码改动）

> 优点：源仓库改代码 → 全局立刻生效，不用重复拷贝。
> Windows 下需要【管理员 PowerShell】或【开发者模式】（创符号链接权限）。

```powershell
# Windows  (右键"以管理员身份运行 PowerShell"，再执行)
powershell -ExecutionPolicy Bypass -File D:\project\skills\install.ps1
```

```bash
# Linux / macOS
chmod +x ./install.sh
./install.sh            # 默认软链接到 ~/.trae-cn/skills
```

---

### 方式 2：全局复制（权限受限 / 离线场景首选）

> 不依赖符号链接权限，双击即可安装，复制后完全离线可用。

```powershell
# Windows  (普通用户权限即可)
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Mode copy
```

```bash
# Linux / macOS
./install.sh copy
```

---

### 方式 3：项目级安装（仅对当前项目生效）

适合团队协作项目，把技能随仓库一起分发（别人克隆后也能一键装到项目 `.trae/skills/`）。

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Mode project -ProjectDir D:\work\my-project
```

```bash
# Linux / macOS
./install.sh project /absolute/path/to/my-project
```

安装后项目目录长这样：

```
my-project/
├── .trae/
│   └── skills/
│       ├── cpolar-tunnel/
│       ├── dddd-ocr/
│       └── ...
└── src/
```

---

## 安装后验证

1. **重启** TraeWork 或 TraeCode（Skills 是启动时扫描的）
2. 打开【设置 → 技能与命令 → 技能】，看到上面 9 个技能即表示安装成功
3. 在对话框输入 `/`，命令补全里会出现技能对应的 `/trigger` 命令
4. 或直接用自然语言描述（触发描述里的关键词即可）

---

## 分发为 ZIP 插件包

分享给别人的时候，在 `d:\project\skills\` 目录下打包即可：

```powershell
# Windows (7z)
7z a -tzip local-skills-bundle-v1.0.0.zip ^
  manifest.json README.md AGENTS.md ^
  install.ps1 install.sh link-skills.ps1 link-skills.sh ^
  cpolar-tunnel dddd-ocr knowbase-ingest nazha-skills ^
  scop-report wct-skill-publish yg-skills yw-skills zcm-task-add-comment
```

```bash
# Linux / macOS
zip -r local-skills-bundle-v1.0.0.zip \
  manifest.json README.md AGENTS.md \
  install.ps1 install.sh link-skills.ps1 link-skills.sh \
  cpolar-tunnel dddd-ocr knowbase-ingest nazha-skills \
  scop-report wct-skill-publish yg-skills yw-skills zcm-task-add-comment
```

对方解压后双击对应平台的 `install.*` 脚本即可一键安装。

---

## 进阶：打包为 VSIX（TraeCode / VS Code 插件）

如果你要做成真正的"插件市场安装"形式（`.vsix`），可以用论坛里的 Superpowers 插件做法：
参见 `vsix-scaffold/README.md`（含 `package.json`、`src/extension.js` 示例，打开工作区时自动把内嵌 skills 复制到项目 `.trae/skills/`，并提供 `Skills: Update from GitHub` 一键更新命令）。
