# WCT 技能市场 API 参考

## 基础信息

- 域名：`dc.iwhalecloud.com`
- 认证：Cookie-based（`currentUserId`）+ CSRF token（`XSRF-TOKEN` cookie → `X-XSRF-TOKEN` header）
- Content-Type：upload 用 `multipart/form-data`，其他用 `application/json`
- 来源：从 fishx.js bundle 逆向 + 实测验证

## 认证 Cookie 获取

Cookie 从用户 Chrome 获取：
```bash
curl -s -X POST "http://localhost:9223/eval?target=<TARGET_ID>" -d 'document.cookie'
```

## API 端点

### 1. 获取类别列表

```
GET /api/skillMarket/categories/list
```

返回 `{ code: 0, data: [{ catgId, catgName, skillCount }] }`

### 2. 获取平台列表

```
GET /api/skillMarket/platforms
```

返回 `{ code: 0, data: [{ value: "claude-code", label: "Claude Code" }, ...] }`
需要登录态。

### 3. 获取我的技能

```
GET /api/skillMarket/my/skills?limit=0&distinct=true
```

返回已发布技能列表，含 `id` 字段。

### 4. 上传技能文件

```
POST /api/skillMarket/upload?version=<VERSION>
Content-Type: multipart/form-data

Body (FormData):
  file: <skill.zip>
```

返回：
```json
{
  "code": 0,
  "data": {
    "skillInfo": {
      "skillName": "...",
      "name": "...",
      "description": "..."
    },
    "filePath": "/uploads/skills/xxx.zip"
  }
}
```

- `skillInfo` 从 SKILL.md 的 YAML frontmatter 解析
- `filePath` 用于后续 publish

### 5. 发布技能（新建）

```
POST /api/skillMarket/publish
Content-Type: application/json

Body:
{
  "skillName": "scop-report",
  "name": "黑鸭子扫描报告",
  "catgId": "6",
  "description": "从 SCOP 平台提取软件组成分析数据...",
  "version": "1.0",
  "tags": ["国际OSS产品线"],
  "filePath": "/uploads/skills/xxx.zip",
  "platforms": ["claude-code"]
}
```

成功返回：`{ code: 0, message: "技能发布成功" }`，前端自动跳转到 `/skills`。

### 6. 更新技能基本信息（已存在技能的新版本）

```
PUT /api/skillMarket/skill/{skillId}/basic-info
Content-Type: application/json

Body:
{
  "icon": "",
  "name": "显示名",
  "catgId": "6",
  "tags": ["标签"],
  "description": "描述"
}
```

### 7. 发布新版本

```
POST /api/skillMarket/skill/{skillId}/versions
Content-Type: multipart/form-data

Body (FormData):
  file: <new_version.zip>
  version: "1.1"
  description: "更新说明"
```

## 类别 ID 映射

| catgId | 名称 |
|--------|------|
| 1 | 云雀研发云 |
| 2 | DeepWiki |
| 3 | 办公协作 |
| 4 | 内容创作 |
| 5 | 数据智能 |
| 6 | 安全合规 |
| 7 | 运维服务 |
| 8 | 系统集成 |
| 9 | 生活服务 |
| 10 | 其他类别 |

## 平台 ID 映射

| platform id | 显示名 |
|-------------|--------|
| claude-code | Claude Code |
| cursor | Cursor |
| gemini-cli | Gemini CLI |
| codex | Codex |
| openclaw | OpenClaw |

## 错误码

- `code: 0` — 成功
- `code: -1` — 未授权（需登录）
- `code: 非0` — 业务错误，message 字段有说明

## 关键字段约束

- `tags`: 最多 3 个，字符串数组 `["tag1", "tag2"]`
- `version`: 字符串，如 `"1.0"`
- `platforms`: 平台 ID 字符串数组，至少 1 个
- `skillName`: 技能标识符（字母、数字、连字符）
- `filePath`: upload 接口返回，必填
