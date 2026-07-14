# ddddocr-fastapi API 参考文档

## 基本信息

- **API 标题**: ocr
- **版本**: 1.0.0
- **开发环境地址**: http://172.60.142.10:8000

## 通用响应格式

所有接口返回统一的 JSON 格式：

```json
{
  "code": 200,
  "message": "Success",
  "data": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码，200 表示成功，其他表示失败 |
| message | string | 响应消息 |
| data | any | 返回数据，成功时包含结果 |

---

## API 接口列表

### 1. OCR 识别

**路径**: `POST /ocr`

**描述**: 对图片进行 OCR 文字识别

**请求方式**: POST

**Content-Type**: `multipart/form-data`

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| file | binary | 否 | - | 图片文件（与 image 二选一） |
| image | string | 否 | - | Base64 编码的图片字符串（与 file 二选一） |
| probability | boolean | 否 | false | 是否返回识别概率 |
| charsets | string | 否 | - | 指定字符集 |
| png_fix | boolean | 否 | false | 是否进行 PNG 修复 |

**示例请求**:

```bash
# 使用文件上传
curl -X POST http://172.60.142.10:8000/ocr \
  -F "file=@captcha.png" \
  -F "probability=true"

# 使用 Base64 编码
curl -X POST http://172.60.142.10:8000/ocr \
  -F "image=data:image/png;base64,iVBORw0KGgo..." \
  -F "probability=false"
```

**成功响应**:

```json
{
  "code": 200,
  "message": "Success",
  "data": "ABCD"
}
```

**失败响应**:

```json
{
  "code": 400,
  "message": "Either file or image must be provided",
  "data": null
}
```

---

### 2. 滑动验证码匹配

**路径**: `POST /slide_match`

**描述**: 对滑动验证码进行目标匹配，返回目标位置

**请求方式**: POST

**Content-Type**: `multipart/form-data`

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| target_file | binary | 否 | - | 目标滑块图片文件（与 target 二选一） |
| target | string | 否 | - | Base64 编码的目标滑块图片字符串（与 target_file 二选一） |
| background_file | binary | 否 | - | 背景图片文件（与 background 二选一） |
| background | string | 否 | - | Base64 编码的背景图片字符串（与 background_file 二选一） |
| simple_target | boolean | 否 | false | 是否使用简单目标模式 |

**示例请求**:

```bash
curl -X POST http://172.60.142.10:8000/slide_match \
  -F "target_file=@slider.png" \
  -F "background_file=@background.png" \
  -F "simple_target=false"
```

**成功响应**:

```json
{
  "code": 200,
  "message": "Success",
  "data": [156, 0]
}
```

**失败响应**:

```json
{
  "code": 400,
  "message": "Both target and background must be provided",
  "data": null
}
```

---

### 3. 目标检测

**路径**: `POST /detection`

**描述**: 对图片进行目标检测，返回检测框坐标

**请求方式**: POST

**Content-Type**: `multipart/form-data`

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| file | binary | 否 | - | 图片文件（与 image 二选一） |
| image | string | 否 | - | Base64 编码的图片字符串（与 file 二选一） |

**示例请求**:

```bash
curl -X POST http://172.60.142.10:8000/detection \
  -F "file=@image.png"
```

**成功响应**:

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

**失败响应**:

```json
{
  "code": 400,
  "message": "Either file or image must be provided",
  "data": null
}
```

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |

## 注意事项

1. 图片支持通过文件上传或 Base64 编码字符串两种方式传入
2. Base64 编码图片可以包含 `data:image/` 前缀，也可以直接传入纯 Base64 字符串
3. OCR 识别支持通过 `charsets` 参数指定字符集范围
4. 滑动验证码匹配需要同时提供目标图片和背景图片