---
name: dddd-ocr
version: 1.0.0
description: |
  调用ddddocr-fastapi服务进行验证码识别、滑动验证码匹配和目标检测。
  触发条件：当用户需要识别验证码图片、处理滑动验证码、检测图片目标时调用。
---

# dddd-ocr Skill

## 前置条件

- Python 3 已安装
- 安装所需依赖：
  ```bash
  pip install requests
  ```
- ddddocr-fastapi 服务已启动并可访问

## 脚本说明

### ocr_client.py
调用ddddocr-fastapi服务的客户端脚本，支持三种功能：
- OCR识别：识别图片中的文字
- 滑动验证码匹配：匹配滑块目标位置
- 目标检测：检测图片中的目标位置

## 工作流程

### Phase 0: 检查依赖

检查Python和依赖是否已安装：
```bash
python --version
pip show requests
```

### Phase 1: 调用OCR服务

**强制要求：必须且只能通过以下命令执行，禁止用任何其他方式替代。**

**OCR识别：**
```bash
python scripts/ocr_client.py ocr <image_path> [--probability] [--charsets <charsets>] [--png_fix] [--server <server_url>]
```

**滑动验证码匹配：**
```bash
python scripts/ocr_client.py slide_match <target_path> <background_path> [--simple_target] [--server <server_url>]
```

**目标检测：**
```bash
python scripts/ocr_client.py detection <image_path> [--server <server_url>]
```

**执行要求：**
- 使用 Python 工具执行上述命令
- 将 `<image_path>` 替换为实际的图片文件路径
- 将 `<target_path>` 和 `<background_path>` 替换为滑块和背景图片路径
- `--server` 参数可选，默认为 http://localhost:8000
- 不得修改脚本、不得跳过脚本、不得在脚本执行前后自行补充任何 API 调用
- 如果脚本输出错误并退出，直接将错误信息返回给用户，不得尝试修复或绕过

**输出：**
脚本直接输出JSON格式的API响应结果

### Phase 2: 解析输出

脚本返回以下信息：

| 命令 | 输出信息 |
|------|----------|
| ocr | 识别的文字字符串或包含概率的字典 |
| slide_match | 滑块位置数组 [x, y] |
| detection | 检测框坐标数组 [[x1, y1, x2, y2], ...] |

### Phase 3: 展示结果

将解析后的识别结果以友好的格式展示给用户

## 示例

**OCR识别：**
```bash
python scripts/ocr_client.py ocr captcha.png
```

**输出示例：**
```json
{
  "code": 200,
  "message": "Success",
  "data": "ABCD"
}
```

**OCR识别（带概率）：**
```bash
python scripts/ocr_client.py ocr captcha.png --probability
```

**输出示例：**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "0": {"A": 0.98},
    "1": {"B": 0.95},
    "2": {"C": 0.99},
    "3": {"D": 0.97}
  }
}
```

**滑动验证码匹配：**
```bash
python scripts/ocr_client.py slide_match slider.png background.png
```

**输出示例：**
```json
{
  "code": 200,
  "message": "Success",
  "data": [156, 0]
}
```

**目标检测：**
```bash
python scripts/ocr_client.py detection image.png
```

**输出示例：**
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    [10, 20, 50, 60],
    [70, 80, 120, 130]
  ]
}
```

## 注意事项

- 图片支持 PNG、JPG、JPEG 等常见格式
- 默认服务地址为 http://localhost:8000，可通过 `--server` 参数指定其他地址
- OCR识别支持通过 `--charsets` 参数指定字符集范围
- 滑动验证码匹配需要同时提供目标滑块图片和背景图片

## 错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| 依赖未安装 | 提示用户执行 `pip install requests` |
| 服务不可达 | 提示用户检查ddddocr-fastapi服务是否启动 |
| 图片不存在 | 提示用户检查图片路径是否正确 |
| 请求参数错误 | 提示用户检查命令参数格式 |