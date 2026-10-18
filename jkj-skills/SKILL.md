---
name: "zspace-xunjian"
description: "极空间(zconnect.cn)NAS巡检日报/签到表/交班表检查与上传。检查文件是否按时上传(默认1小时内,超时告警)，并按现有命名规律把本地文件上传到对应目录。当用户要求检查/核对上传情况、对按时上传告警、上传巡检记录/签到表/交班表时调用。"
---

# 极空间文件巡检与上传 (zspace-xunjian)

针对极空间私有云（https://www.zconnect.cn）上「团队空间/阿里云/成都城运云」下的日常巡检文件的按时检查与上传技能。

## 触发条件

用户提出以下任一需求时调用本技能：
- 检查/核对巡检日报、签到表、交班表是否按时上传，对未按时上传的文件告警
- 要求把本地文件上传到巡检日报、签到表、每日交接班记录及事件记录等目录
- 提到"按时上传""巡检检查""上传签到表/交班表/巡检记录"等

## 一、登录（自动）

1. 打开浏览器访问 `https://www.zconnect.cn/`。
2. 若已登录（URL 为 `/home/` 且可见"团队空间"），直接进入下一步。
3. 若跳转到登录页：读取本地凭据文件 `~/.jkj/jkj.yaml`（Windows: `C:\Users\Administrator\.jkj\jkj.yaml`），取其中的 `account` 与 `password` 填入登录表单并登录。
4. 登录后保持页面打开，后续操作基于同一浏览器会话（cookie 已持久化，通常无需短信验证；若遇到"新终端安全验证"，需提示用户提供短信/邮箱验证码）。

## 二、目录与命名规律（配置表）

文件均位于 **团队空间**（NAS 实际路径前缀 `/sata1/public`）：

| 类别 | 目标目录 | 文件名规律 | 预计生成时间(北京时间) |
|------|----------|-----------|------------------------|
| 巡检记录 | 阿里云/成都城运云/巡检日报/`YYYYMM`/ | `城运云平台系统日常巡检记录YYYYMMDD-HH.jpg`，HH ∈ {01, 09, 15, 21}，每天 4 张 | 每天 01:00 / 09:00 / 15:00 / 21:00 |
| 签到表 | 阿里云/成都城运云/签到表/ | `签到表YYYYMMDD.jpg`，每天 1 张 | 每天约 08:30–09:30 |
| 交班表 | 阿里云/成都城运云/每日交接班记录及事件记录/ | `交班表YYYYMMDD.jpg`，每天 1 张 | 每天傍晚约 18:00–22:00 |

- `YYYYMMDD` = 日期（如 `20260830`），`HH` = 两位小时（如 `09`）。
- 检查时以"今天/指定日期"对应的期望文件名是否存在为判断依据。

## 三、功能一：按时上传检查与告警

### 步骤
1. 确定检查日期（默认今天，可指定）。
2. 对配置表中的每个类别，按规则生成期望文件名清单：
   - 巡检记录：当天 4 张（HH=01/09/15/21）
   - 签到表：当天 1 张
   - 交班表：当天 1 张
3. 通过文件列表接口读取目标目录当前文件（见"四、接口"），判断每个期望文件是否存在及其修改时间。
4. **超时判定**（默认允许延迟 1 小时，可配置）：
   - 期望时间 + 延迟窗口（默认 60 分钟）已过，但对应文件**不存在** → 判定"未及时上传"，告警。
   - 文件存在但修改时间明显晚于期望时间 + 窗口 → 视为迟到，一并提示。
   - 尚未到"期望时间+窗口"的文件 → 正常，不告警。
5. 输出检查报告：正常文件列表 + 告警清单（类别、期望文件名、期望时间、现状）。

### 告警格式示例
```
⚠️ 巡检日报未及时上传：
  - 城运云平台系统日常巡检记录20260830-01.jpg  期望 2026-08-30 01:00（已超 9 小时）
  - 城运云平台系统日常巡检记录20260830-15.jpg  期望 2026-08-30 15:00（已超 1.5 小时）
✅ 其余 2 张已在窗口内上传
```

### ⚠️ 关键：不要截断脚本输出

`--list` 脚本返回的是 **按修改时间倒序** 的结果，**不是按日期分组**。使用 `tail -N` 截断输出会遗漏目标日期的文件（它们可能散落在列表中间）。

**正确做法**：获取完整输出，用 Python 按日期过滤：
```python
import subprocess, re
result = subprocess.run([
    'python', 'D:/projects/skills/jkj-skills/scripts/upload_xunjian.py',
    '--list', '/巡检日报/202610'
], capture_output=True, text=True)

# 过滤目标日期
target_date = '20261018'  # 例如今天
files = {}
for line in result.stdout.strip().split('\n'):
    match = re.search(r'(\d+)-(\d+)', line)
    if match:
        date_str = match.group(1)
        if date_str == target_date:
            name = line.split()[0]
            files[name] = line
```

**错误做法**：`python ... --list ... | tail -30`（会误报缺失）

## 四、功能二：上传文件到对应目录

### 首选方式：常驻脚本（API直传，已实测）

脚本位置：`D:\projects\skills\jkj-skills\scripts\upload_xunjian.py`（技能自带脚本，随本技能统一维护；依赖 Python + Pillow + curl.exe，凭据读 `~/.jkj/cookie.txt`）

```
python "D:\projects\skills\jkj-skills\scripts\upload_xunjian.py" --latest --wait 90          # 手机场景：自动取Trae附件目录最新图片
python "D:\projects\skills\jkj-skills\scripts\upload_xunjian.py" --file <路径> --type jiaoban # 指定文件，交班表
python "D:\projects\skills\jkj-skills\scripts\upload_xunjian.py" --file <路径> --time "2026-10-14 09:00:30"  # 手动指定北京时间
python "D:\projects\skills\jkj-skills\scripts\upload_xunjian.py" --list "/巡检日报/202610"    # 核对目录（显示北京时间）
python "D:\projects\skills\jkj-skills\scripts\upload_xunjian.py" --latest --dry              # 只解析目标名/时间，不上传
```

脚本自动完成：识别拍摄时间（--time > EXIF > 文件名 IMG/MVIMG_YYYYMMDD_HHMMSS > mtime）→ 按类别生成目标文件名 → 写EXIF → API上传（crtime/modify_time 按北京时间换算UTC）→ 文件列表核对。

### 手机拍照上传场景（免人工倒文件）

用户在手机 Trae App 发的图片，会**延迟同步**到本机 `C:\Users\Administrator\.trae-cn\attachments\`（通常几分钟内，文件名带原图时间戳如 `IMG_20261014_010113.jpg`）。流程：

1. 用户说"上传文件"但消息里没有附件路径时 → 运行 `--latest --wait 120` 轮询等待附件落盘。
2. 附件路径已随消息给出时 → 直接 `--file <路径>`。
3. 手机端上传持续失败（提示"部分文件上传失败"）时：让用户在PC端拖拽发送；仍不行才建议微信文件传输助手中转。
4. 脚本识别的时间与用户口述不符时，用 `--time` 显式指定。

### 注意事项

- **目标文件已存在时脚本会拒绝上传**（覆盖上传不会更新页面修改时间）。需先删除旧文件：删除API未找到，用浏览器在页面选中文件→删除→确认（或告知用户处理）。
- 上传接口 `POST https://www.zconnect.cn/v2/file/upload`，关键header：`path`(URL编码完整路径)/`size`/`uuid`(文件SHA1)/`crtime`/`modify_time`(UTC秒)/`rename: 0`/`token`/`nasid`/`Cookie`。
- 时区要点：页面显示按北京时间，`crtime`/`modify_time` 必须传 `calendar.timegm(北京时间-8h)` 的UTC秒；EXIF写本地时间字符串（不带时区）。
- 备用方式：浏览器自动化进入目标目录点"上传"（网页版流程），适合API cookie失效时。
- 上传后通过文件列表接口核对文件名、大小、修改时间（mt换算北京时间）。

## 五、文件列表接口

读取目录内容（已实测可用）：
- 请求：`POST https://www.zconnect.cn/v2/file/list/stream`
- Content-Type：`application/x-www-form-urlencoded`
- Body（字段含义：path=目录完整路径，ftype=0 表示全部类型，sortby=mtime 按修改时间，order=desc 倒序）：
  ```
  path=/sata1/public/阿里云/成都城运云/<子目录>...&start=0&num=1000&sortby=mtime&ftype=0&app=file&order=desc&show_hidden=0&dup=0
  ```
- 响应为 JSON 数组，字段：`n`=名称、`di`=是否目录(1/0)、`s`=字节大小、`mt`=修改时间(Unix 秒)、`ct`=创建时间。
- 实现时在页面上下文用 `fetch`（同源自动带 cookie）调用并解析。

## 六、通用要点

- 全程使用中文与用户沟通。
- 不读取、不展示、不保存任何明文密码；凭据仅从 `~/.jkj/jkj.yaml` 读取并仅用于登录。
- 目录路径、命名规律若与配置表不符，以页面实际显示为准并及时更新本技能配置。
