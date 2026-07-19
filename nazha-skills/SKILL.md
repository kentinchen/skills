# 哪吒监控 (Nezha) 技能

## 技能概述

本技能提供哪吒监控（Nezha）的 API 调用能力，支持登录认证和服务器列表查询。

## 服务列表

| 服务 | 脚本 | 说明 |
|------|------|------|
| 登录 | nazha_login.py | 登录哪吒监控系统，获取并保存 Token |
| 服务器列表 | server_service.py | 查询所有服务器列表及状态信息 |

## 配置文件

配置文件位置：`config/nazha_config.json`

```json
{
  "base_url": "http://localhost:8008",
  "username": "admin",
  "password": "your-password",
  "token": "JWT_TOKEN",
  "pat_token": "nzp_your_pat_token"
}
```

### 认证方式

支持两种认证方式：

1. **JWT Token** - 通过用户名密码登录获取，有过期时间，过期后会自动重新登录
2. **PAT (Personal Access Token)** - 在管理前端创建，更适合自动化场景，不会过期（除非手动吊销）

> **提示**: 推荐在自动化脚本中使用 PAT 认证，可以避免 Token 过期问题。

## 使用说明

### 1. 登录

**命令：**
```bash
python scripts/nazha_login.py <base_url> <username> <password>
```

**示例：**
```bash
python scripts/nazha_login.py http://localhost:8008 admin password
```

**说明：**
- 登录成功后，Token 和配置信息会自动保存到 `config/nazha_config.json`
- 后续其他脚本会自动读取配置文件中的 Token

### 2. 查询服务器列表

**命令：**
```bash
python scripts/server_service.py
```

**输出示例：**
```
服务器列表（共 5 台）:
----------------------------------------------------------------------------------------------------
ID       名称                 IP                   状态       CPU      内存        磁盘      
----------------------------------------------------------------------------------------------------
1        Server-01           192.168.1.101        在线       12.3%    45.6%       67.8%    
2        Server-02           192.168.1.102        离线       0.0%     0.0%        0.0%     
3        Server-03           192.168.1.103        在线       8.5%     32.1%       45.2%    
4        Server-04           192.168.1.104        在线       23.4%    67.8%       78.9%    
5        Server-05           192.168.1.105        在线       5.6%     28.9%       54.3%    
----------------------------------------------------------------------------------------------------
```

## API 参考

详细 API 文档请参考 [api-reference.md](references/api-reference.md)

## 文件结构

```
nazha-skills/
├── config/
│   └── nazha_config.json    # 配置文件（自动生成）
├── references/
│   ├── api-reference.md      # API 接口文档
│   └── nazha.openapi.json    # OpenAPI 规范文档
├── scripts/
│   ├── nazha_base.py         # 基础类（封装认证和API调用）
│   ├── nazha_login.py        # 登录脚本
│   ├── server_service.py     # 服务器列表查询脚本
│   ├── agent.sh
│   └── nezha.sh
└── SKILL.md                  # 技能文档
```