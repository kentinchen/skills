# SSO API 参考文档

## 基本信息
- **API版本**: 1.0.0
- **基础URL**: 根据实际部署环境配置

## 通用请求头
所有接口均需携带以下请求头：

| 请求头 | 值 | 必填 |
|--------|-----|------|
| Authentication | 空字符串 | 是 |
| Content-Type | application/json | 是 |
| Sec-Fetch-Storage-Access | active | 是 |
| X-Request-With | XMLHttpRequest | 是 |

## 接口列表

### 1. 获取验证码
**GET** `/verify-server/kaptcha/generate`

**查询参数：**

| 参数 | 类型 | 必填 | 示例 |
|------|------|------|------|
| _t | string | 是 | 1784045070740 (时间戳) |

**响应示例：**

```json
{
  "resp_code": 200,
  "resp_msg": "生成图形验证码成功！",
  "datas": {
    "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...",
    "picCodeId": "f3d42eefe8d24d45b78a68f31c69d353"
  }
}
```

**响应字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| resp_code | integer | 响应码，200表示成功 |
| resp_msg | string | 响应消息 |
| datas.image | string | Base64编码的验证码图片 |
| datas.picCodeId | string | 验证码ID，用于后续登录 |

---

### 2. 获取登录类型
**GET** `/sso-server/wmh/getLoginType`

**查询参数：**

| 参数 | 类型 | 必填 | 示例 |
|------|------|------|------|
| accountType | string | 是 | 3 |
| appCode | string | 是 | 2a06bab333f5257deb664b8b16a30f23 |
| _t | string | 是 | 1784092268979 |

**响应示例：**

```json
{
  "resp_code": 200,
  "resp_msg": "success",
  "datas": ["zhdl"]
}
```

---

### 3. 获取公钥
**GET** `/sso-server/getPublicKey`

**查询参数：**

| 参数 | 类型 | 必填 | 示例 |
|------|------|------|------|
| _t | string | 是 | 1784092268982 |

**响应示例：**

```json
{
  "resp_code": 200,
  "resp_msg": "success",
  "datas": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC7EWwbNvNswNPHUkLTYzPqa72IIaAgqmHWmLRD1JJMVstOhUfA9/wJeFXPxFvRnDktETZzaJENwqOR50585VvqlbnZZB4ft6KSBByf7JTz6qxFzN/3ndMRDVzaa0ZCZG6KvEvd9rV9FX3spFTxRU66UEpLeVMrkw5D0AyAoNVApwIDAQAB"
}
```

**响应字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| datas | string | Base64编码的RSA公钥，用于加密用户名和密码 |

---

### 4. 获取验证码值
**GET** `/verify-server/kaptcha/getCode`

**查询参数：**

| 参数 | 类型 | 必填 | 示例 |
|------|------|------|------|
| picCodeId | string | 是 | 193be360d2c742868df099758e55e663 |
| _t | string | 是 | 1784045072925 |

**响应示例：**

```json
{
  "resp_code": 200,
  "resp_msg": "ok",
  "datas": "57ceee3fddab15b835259927b051c9d1"
}
```

---

### 5. 登录
**POST** `/sso-server/wmh/Internal/users`

**查询参数：**

| 参数 | 类型 | 必填 | 示例 |
|------|------|------|------|
| _t | string | 是 | 1784047419284 |

**请求体：**

```json
{
  "userName": "加密后的用户名",
  "passWord": "加密后的密码",
  "imgCode": "识别的验证码",
  "picCodeId": "验证码ID",
  "appCode": "2a06bab333f5257deb664b8b16a30f23",
  "state": null,
  "loginDeviceInfo": "设备信息"
}
```

**请求字段：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userName | string | 是 | RSA加密后的用户名 |
| passWord | string | 是 | RSA加密后的密码 |
| imgCode | string | 是 | 识别的验证码 |
| picCodeId | string | 是 | 获取验证码时返回的ID |
| appCode | string | 是 | 应用编码，固定值 |
| state | null | 是 | 状态，固定为null |
| loginDeviceInfo | string | 是 | 设备信息标识 |

**响应示例：**

```json
{
  "resp_code": 200,
  "resp_msg": "登录成功",
  "datas": { ... }
}
```

---

### 6. 密码策略验证
**GET** `/register-server/verify/passwordVerify`

**查询参数：**

| 参数 | 类型 | 必填 | 示例 |
|------|------|------|------|
| accountType | string | 是 | 3 |
| pwd | string | 是 | 加密后的密码 |
| _t | string | 是 | 1784092243460 |

**响应示例：**

```json
{
  "resp_code": 200,
  "resp_msg": "密码策略验证通过！",
  "datas": true
}
```

---

## 登录流程

1. **获取公钥** - 调用 `/sso-server/getPublicKey` 获取RSA公钥
2. **获取验证码** - 调用 `/verify-server/kaptcha/generate` 获取验证码图片和picCodeId
3. **识别验证码** - 使用OCR工具识别验证码图片
4. **加密用户名和密码** - 使用公钥加密用户名和密码
5. **登录** - 调用 `/sso-server/wmh/Internal/users` 提交登录请求

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 其他 | 失败，具体看resp_msg |