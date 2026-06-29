---
name: wct-skill-publish
description: WCT 技能市场发布。通过 API 将 skill 发布到 dc.iwhalecloud.com 技能市场，支持新建发布和版本更新。
  触发场景：发布 skill 到 WCT 市场、更新 WCT 技能、上传技能到 dc.iwhalecloud.com。
---

# wct-skill-publish Skill

## 前置条件

- 用户已在 Chrome 中登录 `https://dc.iwhalecloud.com`
- CDP Proxy 已启动（用于获取 Cookie，不需要浏览器交互）

## 工作流程

### Phase 0: 准备

1. 加载 `references/api-reference.md` 获取 API 详情
2. 确认 CDP Proxy 可用：`curl -s http://localhost:9223/health`
3. 确定要发布的 skill 路径：
   - 用户指定路径 → 使用
   - 否则询问用户要发布哪个 skill（检查 `.claude/skills/` 下可用 skill）
4. 读取 skill 的 SKILL.md，提取 YAML frontmatter（name、description）
5. 打包 skill 为 zip：
   ```bash
   cd /path/to/skill && zip -r /tmp/<skill-name>.zip . -x "*.zip" "*.DS_Store"
   ```
6. 从页面获取 Cookie：
   ```bash
   # 查找已打开的 dc.iwhalecloud.com tab
   curl -s http://localhost:9223/targets
   # 如果没有，用 /new 打开
   curl -s "http://localhost:9223/new?url=https://dc.iwhalecloud.com/skills/publish"
   # 获取 Cookie
   curl -s -X POST "http://localhost:9223/eval?target=<TARGET_ID>" -d 'document.cookie'
   ```

### Phase 1: 收集发布参数

向用户确认以下参数（尽可能从 SKILL.md 自动推断）：

| 参数 | 来源 | 说明 |
|------|------|------|
| skillName | SKILL.md `name` 字段 | 技能标识符 |
| name | SKILL.md 第一行 `# xxx` 或询问用户 | 显示名 |
| catgId | 询问用户选择类别 | 参考 api-reference.md 的类别映射 |
| description | SKILL.md `description` 字段 | 描述 |
| version | 默认 `"1.0"` 或询问 | 版本号 |
| tags | 询问用户 | 最多 3 个 |
| platforms | 根据 skill 内容推断或询问 | 至少 1 个 |

### Phase 2: 检查是否已存在

1. 调用 `GET /api/skillMarket/my/skills?limit=0&distinct=true` 获取已发布技能列表
2. 按 `skillName` 匹配是否已存在

### Phase 3: 上传文件

```bash
curl -s "https://dc.iwhalecloud.com/api/skillMarket/upload?version=<VERSION>" \
  -H "Cookie: <COOKIE>" \
  -H "X-XSRF-TOKEN: <TOKEN>" \
  -F "file=@/tmp/<skill-name>.zip"
```

从返回的 `data.filePath` 和 `data.skillInfo` 提取上传结果。

### Phase 4: 发布或更新

**新建发布**（skillName 不存在）：
```bash
curl -s "https://dc.iwhalecloud.com/api/skillMarket/publish" \
  -H "Cookie: <COOKIE>" \
  -H "Content-Type: application/json" \
  -H "X-XSRF-TOKEN: <TOKEN>" \
  -d '{
    "skillName": "<skillName>",
    "name": "<显示名>",
    "catgId": "<catgId>",
    "description": "<描述>",
    "version": "<版本号>",
    "tags": ["<标签1>"],
    "filePath": "<upload返回的路径>",
    "platforms": ["<平台ID>"]
  }'
```

**更新已存在技能**：
- 更新基本信息：`PUT /api/skillMarket/skill/{skillId}/basic-info`
- 发布新版本：`POST /api/skillMarket/skill/{skillId}/versions`

### Phase 5: 结果确认

- `code: 0` → 成功，报告发布结果
- `code: 非0` → 失败，报告错误信息
- 清理临时 zip 文件

## 严格禁止

- **不操作 DOM**：全部通过 API 完成，不使用 `/click`、`/eval` 操作表单元素
- **不跳过 CSRF**：必须从 Cookie 中提取 XSRF-TOKEN 并作为 header 发送
- **不上传非 skill 文件**：确认目录包含有效的 SKILL.md

## 关键决策点

| 场景 | 处理 |
|------|------|
| 无 dc.iwhalecloud.com tab | 用 `/new` 打开，获取 Cookie 后用 `/close` 关闭 |
| skill 已存在 | 询问用户：更新基本信息 / 发布新版本 / 取消 |
| upload 返回 code != 0 | 报告错误，检查 Cookie 是否有效 |
| zip 太大 (>50MB) | 警告用户，建议精简 |
| Cookie 过期 | 提示用户在 Chrome 中重新登录 dc.iwhalecloud.com |
