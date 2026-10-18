<#
.SYNOPSIS
校验/规范化极空间登录 cookie，供 upload-zspace.ps1 复用。不实际发起上传。

.DESCRIPTION
- 读取 cookie（-Cookie 参数 / 环境变量 ZSPACE_COOKIE / 文件 ~/.jkj/cookie.txt）
- 校验必要字段：zenithtoken、nas_id、device_id、username、userid
- 将规范化后的 Cookie 一行写入 ~/.jkj/cookie.txt（供上传脚本复用）
- 从 zenithtoken 解析并展示过期时间

.EXAMPLE
# 校验并规范化当前 cookie.txt，刷新过期时间提示
.\get-zspace-cookie.ps1

.EXAMPLE
# 用浏览器中复制的 document.cookie 覆盖写入
.\get-zspace-cookie.ps1 -Cookie "webagent=v2; zenithtoken=xxx; ..." -Force
#>
param(
    # 直接传 document.cookie 原始字符串（含 URL 编码的 zenithtoken）
    [string]$Cookie,
    # 覆盖写入 cookie.txt（默认仅在字段缺失或文件不存在时写入）
    [switch]$Force,
    [string]$NasId = "Z0400102LDZX5"
)

$ErrorActionPreference = "Stop"
$COOKIE_FILE = Join-Path $HOME ".jkj\cookie.txt"

# ---------- 1. 获取 cookie 来源 ----------
if (-not [string]::IsNullOrEmpty($Cookie)) {
    $src = $Cookie
    Write-Host "来源: -Cookie 参数"
} elseif ($env:ZSPACE_COOKIE) {
    $src = $env:ZSPACE_COOKIE
    Write-Host "来源: 环境变量 ZSPACE_COOKIE"
} elseif (Test-Path $COOKIE_FILE) {
    $src = (Get-Content $COOKIE_FILE -Raw -ErrorAction Stop).Trim()
    Write-Host "来源: $COOKIE_FILE"
} else {
    Write-Host "未找到 cookie（文件 $COOKIE_FILE 不存在）。"
    Write-Host ""
    Write-Host "【如何获取 cookie】PowerShell 无法解密 Chrome 的加密 cookie 存储，"
    Write-Host "请用浏览器自动化(MCP chrome-devtools)在已登录的 zconnect.cn 页面执行："
    Write-Host "    evaluate_script: return document.cookie;"
    Write-Host "把返回的完整 cookie 字符串作为 -Cookie 传入本脚本，或直接写入："
    Write-Host "    $COOKIE_FILE"
    exit 0
}

# ---------- 2. 字段提取 ----------
function Get-Ck([string]$c, [string]$k) {
    $m2 = [regex]::Match($c, "(?:^|;| )$k=([^;]+)")
    if ($m2.Success) { try { [uri]::UnescapeDataString($m2.Groups[1].Value) } catch { $m2.Groups[1].Value } } else { "" }
}

$token    = Get-Ck $src "zenithtoken"
$nasIdX   = Get-Ck $src "nas_id"
$deviceId = Get-Ck $src "device_id"
$username = Get-Ck $src "username"
$userid   = Get-Ck $src "userid"
$nasId    = if ($nasIdX) { $nasIdX } else { $NasId }

Write-Host ""
Write-Host "字段校验:"
Write-Host "  nas_id     = $nasId"
Write-Host "  device_id  = $deviceId"
Write-Host "  username   = $username"
Write-Host "  userid     = $userid"
Write-Host "  zenithtoken= $($(if($token){'<OK, '+$token.Length+' chars>'}else{'<缺失>'}))"
Write-Host ""

if ([string]::IsNullOrEmpty($token)) {
    Write-Warning "zenithtoken 缺失，cookie 无效。请刷新后重试。"
    exit 1
}

# ---------- 3. 过期时间解析（zenithtoken 形如 115<base64形 data>'$'20260830...'$'...） ----------
try {
    # token 中的数字时间戳（Unix 秒）可能作为数字段存在；此处做尽力解析
    $tsMatch = [regex]::Match($token, '[0-9]{10}')
    if ($tsMatch.Success) {
        $exp = ([DateTimeOffset]::FromUnixTimeSeconds([int64]$tsMatch.Value)).ToLocalTime()
        Write-Host "token 时间戳≈ $($exp.ToString('yyyy-MM-dd HH:mm:ss')) (尽力解析，可能为签发时间)"
    }
} catch { }

# ---------- 4. 写入规范化 cookie ----------
$cookieDir = Split-Path $COOKIE_FILE -Parent
if (-not (Test-Path $cookieDir)) { New-Item -ItemType Directory -Path $cookieDir -Force | Out-Null }

if ($Force -or (-not (Test-Path $COOKIE_FILE)) -or ([string]::IsNullOrEmpty((Get-Content $COOKIE_FILE -Raw)))) {
    $normalized = "webagent=v2; nas_id=$nasId; zenithtoken=$token; username=$username; userid=$userid; plat=web; app=file; device=PC; device_id=$deviceId"
    if ($Force) { $normalized = $src }  # 用户显式传入则保留原始串（最稳妥）
    Set-Content -Path $COOKIE_FILE -Value $normalized -Encoding UTF8 -NoNewline
    Write-Host "已写入规范 cookie: $COOKIE_FILE"
} else {
    Write-Host "cookie.txt 已存在且有效，未覆盖（如需覆盖加 -Force）。"
}
Write-Host "完成。可直接运行 upload-zspace.ps1 上传。"