# 哪吒监控 (Nezha) API 接口文档

基于 https://nezha.wiki/guide/api.html 生成

## 概述

哪吒监控 Dashboard 从 v1 起主要使用 `/api/v1` 路径。接口返回 JSON，适合自定义前端、机器人、自动化脚本和内部运维工具使用。

如果需要完整、随源码同步的接口列表，建议优先使用 Dashboard 内置 Swagger 文档。

## 获取完整 API 文档

Dashboard 在调试模式下会挂载 Swagger UI：

1. 编辑 Dashboard 配置文件，开启调试模式：
   ```yaml
   debug: true
   ```

2. 重启 Dashboard。

3. 查看 Dashboard 日志中的提示，默认地址类似：
   ```
   http://localhost:8008/swagger/index.html
   ```

> **警告**: `debug: true` 会额外暴露调试信息和 Swagger UI，不建议在公网生产环境长期开启。

## 认证方式

### 1. 登录获取 Token

**请求：**
```http
POST /api/v1/login
Content-Type: application/json
```

**请求体：**
```json
{
  "username": "admin",
  "password": "your-password"
}
```

**成功返回：**
```json
{
  "success": true,
  "data": {
    "token": "JWT_TOKEN",
    "expire": "2026-05-18T12:00:00+02:00"
  }
}
```

**后续请求头：**
```http
Authorization: Bearer JWT_TOKEN
```

### 2. Personal Access Token (PAT)

JWT 主要用于浏览器和管理前端的登录态；自动化脚本、CI、LLM 工具和 MCP 客户端建议使用 PAT。

**请求头格式：**
```http
Authorization: Bearer nzp_<secret>
```

**创建 PAT：**
在管理前端的 **系统设置 → API Tokens** 中创建和吊销 PAT。创建时需要填写：

| 字段 | 说明 |
|------|------|
| name | Token 名称，最长 128 个字符 |
| scopes | 权限列表，至少 1 项，最多 32 项 |
| server_ids | 可选的服务器 ID 白名单，最多 1000 项；留空表示不额外限制 |
| expires_in_days | 可选的过期天数，留空或 `0` 表示永不过期，最大值为 `3650` |

> **警告**: `/api/v1/api-tokens` 这组 Token 管理接口只能使用登录 JWT 调用，不能用 PAT 自己创建、更改或删除 PAT。

### 3. PAT 权限范围

PAT 使用 `nezha:{resource}:{verb}` 命名权限范围。

**资源名：**
- `server`
- `service`
- `alertrule`
- `cron`
- `ddns`
- `nat`
- `notification`
- `notification-group`
- `transfer`
- `admin`

**动作名：**
- `read`
- `write`
- `delete`
- `exec`

**常用 scope 示例：**

| Scope | 说明 |
|-------|------|
| `nezha:inventory:read` | 列出服务器与服务器分组 |
| `nezha:inventory:delete` | 删除服务器与服务器分组 |
| `nezha:server:read` | 查看单台服务器、读取其指标与文件 |
| `nezha:server:exec` | 创建在线终端或调用 MCP 的远程执行工具 |
| `nezha:cron:exec` | 手动触发计划任务 |
| `nezha:transfer:write` | 取消或重试服务器转移任务 |
| `nezha:admin:*` | 用户、WAF、在线用户、系统设置和维护等管理员资源 |

**通配 scope：**
- `nezha:<resource>:*`：允许某个资源下的所有动作
- `nezha:admin:*`：允许管理员资源，只有管理员可以签发
- `nezha:*`：完整权限，只有管理员可以签发

### 4. PAT 禁用接口

以下接口必须使用登录 JWT 调用，禁止使用 PAT：

| 接口 | 说明 |
|------|------|
| `POST /api/v1/refresh-token` | 刷新 Token |
| `GET /api/v1/profile` | 获取个人资料 |
| `POST /api/v1/profile` | 更新个人资料 |
| `POST /api/v1/oauth2/{provider}/unbind` | 解绑 OAuth2 |
| `GET /api/v1/api-tokens` | 获取 API Token 列表 |
| `POST /api/v1/api-tokens` | 创建 API Token |
| `DELETE /api/v1/api-tokens/{id}` | 删除 API Token |

### 5. 游客可访问接口

部分只读接口支持游客访问，但会受到站点配置和服务器隐藏设置限制：
- 开启 `force_auth` 后，游客不能访问服务器和服务监控数据
- 如果服务器启用了"对游客隐藏"，游客不能访问该服务器的数据
- 服务历史和服务器指标接口中，游客只能查询 `1d` 周期数据

## 返回格式

### 普通接口返回
```json
{
  "success": true,
  "data": {}
}
```

### 失败返回
```json
{
  "success": false,
  "error": "error message"
}
```

### 带分页的列表接口返回
```json
{
  "success": true,
  "data": {
    "value": [],
    "pagination": {
      "offset": 0,
      "limit": 10,
      "total": 100
    }
  }
}
```

## 常用接口

### 1. 获取系统设置

**请求：**
```http
GET /api/v1/setting
```

**说明：**
- 可用于读取站点名称、语言、前端模板、OAuth2 提供方、TSDB 是否启用等基础信息
- 未登录访问时只返回允许游客读取的配置

### 2. 获取服务器列表

**请求：**
```http
GET /api/v1/server
Authorization: Bearer JWT_TOKEN
```

**说明：**
- 返回当前用户有权限管理的服务器列表
- 管理员可见所有服务器，普通用户只能看到自己名下的服务器
- 如需实时状态流，请使用 WebSocket 接口

### 3. 获取服务器实时状态流

**请求：**
```http
GET /api/v1/ws/server
Authorization: Bearer JWT_TOKEN
```

**说明：**
- 返回 WebSocket 数据流，用于实时刷新服务器在线状态和资源占用
- 如果站点未开启 `force_auth`，游客也可以连接

### 4. 获取服务监控概览

**请求：**
```http
GET /api/v1/service
```

**说明：**
- 返回服务监控当前状态和周期流量统计
- 登录用户可以看到自己有权限查看的数据

### 5. 获取服务监控历史

**请求：**
```http
GET /api/v1/service/{id}/history?period=1d
```

**参数：**

| 参数 | 说明 |
|------|------|
| id | 服务监控 ID（必填） |
| period | 查询周期，可选 `1d`、`7d`、`30d`，默认 `1d` |

**返回示例：**
```json
{
  "success": true,
  "data": {
    "service_id": 1,
    "service_name": "HTTPS",
    "servers": [
      {
        "server_id": 1,
        "server_name": "Server 1",
        "stats": {
          "avg_delay": 68.2,
          "up_percent": 99.9,
          "total_up": 1440,
          "total_down": 1,
          "data_points": [
            {
              "ts": 1760000000000,
              "delay": 68.2,
              "status": 1
            }
          ]
        }
      }
    ]
  }
}
```

### 6. 获取服务器指标历史

**请求：**
```http
GET /api/v1/server/{id}/metrics?metric=cpu&period=1d
```

**参数：**

| 参数 | 说明 |
|------|------|
| id | 服务器 ID（必填） |
| metric | 指标名称（必填） |
| period | 查询周期，可选 `1d`、`7d`、`30d`，默认 `1d` |

**支持的 metric：**
- `cpu` - CPU 使用率
- `memory` - 内存使用率
- `swap` - 交换分区使用率
- `disk` - 磁盘使用率
- `net_in_speed` - 入站网络速度
- `net_out_speed` - 出站网络速度
- `net_in_transfer` - 入站网络流量
- `net_out_transfer` - 出站网络流量
- `load1` - 1分钟负载
- `load5` - 5分钟负载
- `load15` - 15分钟负载
- `tcp_conn` - TCP 连接数
- `udp_conn` - UDP 连接数
- `process_count` - 进程数
- `temperature` - 温度
- `uptime` - 运行时间
- `gpu` - GPU 使用率

**返回示例：**
```json
{
  "success": true,
  "data": {
    "server_id": 1,
    "server_name": "Server 1",
    "metric": "cpu",
    "data_points": [
      {
        "ts": 1760000000000,
        "value": 12.34
      }
    ]
  }
}
```

> **警告**: 该接口依赖 TSDB。未启用 TSDB 时，接口仍会返回成功，但 `data_points` 为空。

### 7. 获取服务下的服务器

**请求：**
```http
GET /api/v1/service/{id}/server
```

**说明：**
- 返回某个服务监控关联的服务器列表

### 8. 获取服务器下的服务监控

**请求：**
```http
GET /api/v1/server/{id}/service
```

**说明：**
- 返回某台服务器关联的服务监控列表

## 管理类接口

管理类接口均需要登录。使用 JWT 时按用户角色和资源归属判断权限；使用 PAT 时，还会额外校验所需 scope。

### 接口列表

| 功能 | 路径 | PAT scope |
|------|------|-----------|
| 用户和个人资料 | `/api/v1/profile`、`/api/v1/user`、`/api/v1/batch-delete/user` | 个人资料禁止 PAT；用户管理需要 `nezha:admin:*` |
| 服务器台账 | `GET /api/v1/server`、`/api/v1/batch-delete/server`、`GET /api/v1/server-group`、`/api/v1/batch-delete/server-group` | `nezha:inventory:read` / `delete` |
| 服务器 | `/api/v1/server/config`、`/api/v1/batch-move/server`、`/api/v1/force-update/server`、`PATCH /api/v1/server/{id}` | `nezha:server:read` / `write` |
| 服务器分组 | `POST /api/v1/server-group`、`PATCH /api/v1/server-group/{id}` | `nezha:server:write` |
| 服务器转移 | `/api/v1/transfer`、`/api/v1/transfer/{id}/cancel`、`/api/v1/transfer/{id}/retry`、`/api/v1/ws/transfer` | `nezha:transfer:read` / `write` |
| 通知方式 | `/api/v1/notification`、`/api/v1/batch-delete/notification` | `nezha:notification:read` / `write` / `delete` |
| 通知组 | `/api/v1/notification-group`、`/api/v1/batch-delete/notification-group` | `nezha:notification-group:read` / `write` / `delete` |
| 警报规则 | `/api/v1/alert-rule`、`/api/v1/batch-delete/alert-rule` | `nezha:alertrule:read` / `write` / `delete` |
| 服务监控 | `/api/v1/service/list`、`/api/v1/service`、`/api/v1/batch-delete/service` | `nezha:service:read` / `write` / `delete` |
| 定时任务 | `/api/v1/cron`、`/api/v1/cron/{id}/manual`、`/api/v1/batch-delete/cron` | `nezha:cron:read` / `write` / `exec` / `delete` |
| DDNS | `/api/v1/ddns`、`/api/v1/ddns/providers`、`/api/v1/batch-delete/ddns` | `nezha:ddns:read` / `write` / `delete` |
| NAT 规则 | `/api/v1/nat`、`/api/v1/batch-delete/nat` | `nezha:nat:read` / `write` / `delete` |
| 在线用户 | `/api/v1/online-user` | `nezha:admin:*` |
| WAF | `/api/v1/waf` | `nezha:admin:*` |
| 系统设置 | `PATCH /api/v1/setting` | `nezha:admin:*` |
| 维护模式 | `POST /api/v1/maintenance` | `nezha:admin:*` |

### REST 路由与 scope 对照

| 路由 | API Token 所需 scope |
|------|---------------------|
| `GET /api/v1/server`、`GET /api/v1/ws/server`、`GET /api/v1/server-group` | `nezha:inventory:read` |
| `POST /api/v1/batch-delete/server`、`POST /api/v1/batch-delete/server-group` | `nezha:inventory:delete` |
| `PATCH /api/v1/server/{id}`、`GET /api/v1/server/config/{id}`、`POST /api/v1/server/config`、`POST /api/v1/batch-move/server`、`POST /api/v1/force-update/server` | `nezha:server:write` |
| `POST /api/v1/file`、`GET /api/v1/ws/file/{id}` | 同时需要 `nezha:server:read`、`nezha:server:write`、`nezha:server:delete` |
| `GET /api/v1/transfer`、`GET /api/v1/ws/transfer` | `nezha:transfer:read` |
| `POST /api/v1/transfer/{id}/cancel`、`POST /api/v1/transfer/{id}/retry` | `nezha:transfer:write` |
| `/api/v1/user`、`/api/v1/waf`、`/api/v1/online-user`、`PATCH /api/v1/setting`、`POST /api/v1/maintenance` | `nezha:admin:*` |

## MCP 接入

Dashboard 提供独立的 MCP 入口：

**请求：**
```http
POST /mcp
Authorization: Bearer nzp_<secret>
```

**说明：**
- MCP 不在 `/api/v1` 下，并且只接受 PAT，不接受 JWT
- 启用前需要在 Dashboard 配置中打开 `enable_mcp`
- 文件传输类工具会使用 `GET /mcp/download/:token` 和 `POST /mcp/upload/:token` 作为临时传输地址

### MCP 工具权限

| 工具 | 所需 scope |
|------|-----------|
| `meta.whoami` | 任意有效 PAT |
| `server.list` | `nezha:inventory:read` |
| `server.get` | `nezha:server:read` |
| `server.exec` | `nezha:server:exec` |
| `fs.list` / `fs.read` / `fs.download_url` | `nezha:server:read` |
| `fs.write` / `fs.upload_url` | `nezha:server:write` |
| `fs.delete` | `nezha:server:delete` |

## 常见授权组合

| 场景 | 建议 scope |
|------|-----------|
| 外部看板只读展示服务器清单 | `nezha:inventory:read` |
| 外部看板读取服务器详情和指标 | `nezha:inventory:read`、`nezha:server:read` |
| MCP 客户端查询服务器和读取小文件 | `nezha:inventory:read`、`nezha:server:read` |
| MCP 客户端执行维护命令 | `nezha:inventory:read`、`nezha:server:read`、`nezha:server:exec`，并设置服务器 ID 白名单 |
| MCP 客户端写入或上传文件 | `nezha:server:read`、`nezha:server:write`，并设置服务器 ID 白名单 |
| CI/CD 只触发指定计划任务 | `nezha:cron:read`、`nezha:cron:exec` |
| 运维脚本管理服务监控 | `nezha:service:read`、`nezha:service:write`，需要删除时再加 `nezha:service:delete` |
| 管理员自动化维护设置 | `nezha:admin:*`，仅管理员 Token 可用 |

## 常见错误

| 状态码 | 含义 |
|--------|------|
| `401 Unauthorized` | Token 无效、已过期、所属用户不存在，或 `Authorization` 头格式错误 |
| `403 Forbidden` | Token 有效，但缺少当前接口需要的 scope，服务器不在白名单内，用户没有该服务器权限，或接口明确禁止 API Token 调用 |