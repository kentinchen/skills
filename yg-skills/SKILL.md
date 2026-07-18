---
name: yg-services
version: 2.0.0
description: |
  云管系统综合服务，支持查询通知清单、工单、监控、资源、文件、账单、客户等功能。
  触发条件：当用户需要查询yg系统或云管系统的通知、工单、监控、资源、文件、账单或客户信息时调用。
---

# 云管系统服务 Skill

## 前置条件

- Python 3 已安装
- 安装所需依赖：
  ```bash
  pip install requests pycryptodome pyyaml
  ```
- 已配置 `~/.yg-skills/config.yml` 文件，包含用户名、密码等配置
- ddddocr-fastapi 服务已启动（用于验证码识别）

## 服务列表

| 服务   | 脚本                  | 功能          |
|------|---------------------|-------------|
| 通知服务 | notice_service.py   | 查询通知清单、通知详情 |
| 工单服务 | task_service.py     | 查询待办工单、完成工单 |
| 监控服务 | monitor_service.py  | 查询监控概览、每天统计 |
| 资源服务 | resource_service.py | 查询资源变化、云商资源 |
| 文件服务 | file_service.py     | 查询文件列表、文件资源 |
| 账单服务 | billing_service.py  | 查询账单系数      |
| 客户服务 | customer_service.py | 查询用户画像、部门树  |

## 配置文件

配置文件路径：`~/.yg-skills/config.yml`

```yaml
username: your_username
password: your_password
sso_url: http://172.60.142.10
app_url: http://172.60.142.10
proxy: socks5://127.0.0.1:20808
app_code: 2a06bab333f5257deb664b8b16a30f23
login_device_info: a8799d06d5e4b4bf4b8efe54b5086f7c
```

## 通知服务

### 查询通知清单

```bash
python scripts/notice_service.py [--page-num <页码>] [--page-size <每页大小>] [--notice-type <通知类型>] [--app-username <APP用户名>]
```

**参数说明：**

| 参数                             | 说明                        | 默认值     |
|--------------------------------|---------------------------|---------|
| --page-num, --pageNum          | 页码                        | 1       |
| --page-size, --pageSize        | 每页大小                      | 5       |
| --notice-type, --noticeType    | 通知类型：1-普通公告，2-安全情报，3-资源变化 | 1       |
| --app-username, --app_username | APP用户名（用于获取APP token）     | 从配置文件读取 |

### 查询通知详情

```bash
python scripts/notice_service.py --notice-id <通知ID> [--app-username <APP用户名>]
```

**参数说明：**

| 参数                             | 说明       | 默认值     |
|--------------------------------|----------|---------|
| --notice-id, --noticeId        | 通知ID（必填） | 无       |
| --app-username, --app_username | APP用户名   | 从配置文件读取 |

## 工单服务

### 查询待办工单

```bash
python scripts/task_service.py --type todo [--page-num <页码>] [--page-size <每页大小>] [--instance-id <实例ID>] [--instance-name <实例名称>] [--task-id <任务ID>] [--task-name <任务名称>] [--app-username <APP用户名>]
```

**参数说明：**

| 参数                              | 说明                     | 默认值     |
|---------------------------------|------------------------|---------|
| --type                          | 查询类型：todo（待办），done（完成） | todo    |
| --page-num, --pageNum           | 页码                     | 1       |
| --page-size, --pageSize         | 每页大小                   | 10      |
| --instance-id, --instanceId     | 实例ID（筛选条件）             | None    |
| --instance-name, --instanceName | 实例名称（筛选条件）             | None    |
| --task-id, --taskId             | 任务ID（筛选条件）             | None    |
| --task-name, --taskName         | 任务名称（筛选条件）             | None    |
| --app-username, --app_username  | APP用户名                 | 从配置文件读取 |

### 查询完成工单

```bash
python scripts/task_service.py --type done [--page-num <页码>] [--page-size <每页大小>] [--app-username <APP用户名>]
```

## 监控服务

### 查询监控概览

```bash
python scripts/monitor_service.py --type overview [--app-username <APP用户名>]
```

### 查询每天统计

```bash
python scripts/monitor_service.py --type daily --supplier-code <供应商编码> --time <日期> [--app-username <APP用户名>]
```

**参数说明：**

| 参数                              | 说明                              | 默认值      |
|---------------------------------|---------------------------------|----------|
| --type                          | 查询类型：overview（监控概览），daily（每天统计） | overview |
| --supplier-code, --supplierCode | 供应商编码（每天统计时必填）                  | 无        |
| --time                          | 日期（每天统计时必填，格式：YYYY-MM-DD）       | 无        |
| --app-username, --app_username  | APP用户名                          | 从配置文件读取  |

## 资源服务

### 查询资源变化

```bash
python scripts/resource_service.py --type change --time <时间范围> --supplier <供应商> [--app-username <APP用户名>]
```

**参数说明：**

| 参数                             | 说明                                      | 默认值     |
|--------------------------------|-----------------------------------------|---------|
| --type                         | 查询类型：change（资源变化），supplier（云商资源）        | change  |
| --time                         | 时间范围（资源变化时必填，格式：YYYY-MM-DD--YYYY-MM-DD） | 无       |
| --supplier                     | 供应商（资源变化时必填）                            | 无       |
| --app-username, --app_username | APP用户名                                  | 从配置文件读取 |

### 查询云商资源

```bash
python scripts/resource_service.py --type supplier --supplier-code <供应商编码> [--date-offset <天数>] [--app-username <APP用户名>]
```

**参数说明：**

| 参数                              | 说明        | 默认值     |
|---------------------------------|-----------|---------|
| --supplier-code, --supplierCode | 供应商编码（必填） | 无       |
| --date-offset, --dateOffset     | 日期偏移天数    | 7       |
| --app-username, --app_username  | APP用户名    | 从配置文件读取 |

## 文件服务

### 查询文件列表

```bash
python scripts/file_service.py --type list --file-type <文件类型> [--page-num <页码>] [--page-size <每页大小>] [--app-username <APP用户名>]
```

**参数说明：**

| 参数                             | 说明                              | 默认值     |
|--------------------------------|---------------------------------|---------|
| --type                         | 查询类型：list（文件列表），resources（文件资源） | list    |
| --file-type, --fileType        | 文件类型（文件列表时必填：运维工具、业务模板、系统工具）    | 无       |
| --page-num, --pageNum          | 页码                              | 1       |
| --page-size, --pageSize        | 每页大小                            | 100     |
| --app-username, --app_username | APP用户名                          | 从配置文件读取 |

### 查询文件资源

```bash
python scripts/file_service.py --type resources --key <资源键> [--page-num <页码>] [--page-size <每页大小>] [--resource <资源类型>] [--app-username <APP用户名>]
```

**参数说明：**

| 参数                             | 说明                     | 默认值     |
|--------------------------------|------------------------|---------|
| --key                          | 资源键（必填，示例：ResourcesUp） | 无       |
| --resource                     | 资源类型                   | 7       |
| --page-num, --pageNum          | 页码                     | 1       |
| --page-size, --pageSize        | 每页大小                   | 100     |
| --app-username, --app_username | APP用户名                 | 从配置文件读取 |

## 账单服务

### 查询账单系数

```bash
python scripts/billing_service.py --cloud-supplier <云供应商编码> --time-tag <时间标签> [--page-num <页码>] [--page-size <每页大小>] [--app-username <APP用户名>]
```

**参数说明：**

| 参数                                | 说明                     | 默认值     |
|-----------------------------------|------------------------|---------|
| --cloud-supplier, --cloudSupplier | 云供应商编码（必填，示例：chengyun） | 无       |
| --time-tag, --timeTag             | 时间标签（必填，格式：YYYY-MM-DD） | 无       |
| --page-num, --pageNum             | 页码                     | 1       |
| --page-size, --pageSize           | 每页大小                   | 10      |
| --app-username, --app_username    | APP用户名                 | 从配置文件读取 |

## 客户服务

### 查询用户画像

```bash
python scripts/customer_service.py --type profile [--app-username <APP用户名>]
```

### 查询部门树

```bash
python scripts/customer_service.py --type dept [--app-username <APP用户名>]
```

**参数说明：**

| 参数                             | 说明                           | 默认值     |
|--------------------------------|------------------------------|---------|
| --type                         | 查询类型：profile（用户画像），dept（部门树） | profile |
| --app-username, --app_username | APP用户名                       | 从配置文件读取 |

## 执行要求

- 使用 Python 工具执行上述命令
- 不得修改脚本、不得跳过脚本、不得在脚本执行前后自行补充任何 API 调用
- 如果脚本输出错误并退出，直接将错误信息返回给用户，不得尝试修复或绕过

## 错误处理

| 错误场景     | 处理方式                                              |
|----------|---------------------------------------------------|
| 依赖未安装    | 提示用户执行 `pip install requests pycryptodome pyyaml` |
| 配置文件不存在  | 提示用户先运行登录脚本配置                                     |
| 用户名或密码错误 | 提示用户检查配置文件                                        |
| OCR服务不可达 | 提示用户检查ddddocr-fastapi服务是否启动                       |
| token失效  | 自动重新登录获取新token                                    |

## 示例

**查询通知清单：**

```bash
python scripts/notice_service.py --notice-type 1 --page-size 10
```

**查询待办工单：**

```bash
python scripts/task_service.py --type todo
```

**查询监控概览：**

```bash
python scripts/monitor_service.py --type overview
```

**查询资源变化：**

```bash
python scripts/resource_service.py --type change --time "2026-07-06--2026-07-12" --supplier "H3C_outside"
```

**查询文件列表：**

```bash
python scripts/file_service.py --type list --file-type "运维工具"
```

**查询账单系数：**

```bash
python scripts/billing_service.py --cloud-supplier "chengyun" --time-tag "2026-07-15"
```

**查询用户画像：**

```bash
python scripts/customer_service.py --type profile
```