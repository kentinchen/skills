<#
.SYNOPSIS
将巡检/签到/交班图片上传到极空间(zconnect.cn)对应目录（按 skill 命名规律自动路由）。

.DESCRIPTION
自动从文件名识别类别，按 skill 配置表计算目标目录与标准文件名，用已验证的文件上传
API（POST /v2/file/upload，curl.exe --data-binary）上传，成功后回读目录校验。

凭据来源（按优先级）：
  1. -Cookie 参数（明文传 cookie 字符串）
  2. 环境变量 ZSPACE_COOKIE
  3. 文件 ~/.jkj/cookie.txt（推荐，由登录后写入）

.EXAMPLE
# 上传一张巡检记录（自动识别 → 巡检日报/202609/城运云平台系统日常巡检记录20260901-15.jpg）
.\upload-zspace.ps1 -File "D:\tmp\城运云平台系统日常巡检记录20260901-15.jpg"

.EXAMPLE
# 上传时手动指定目录(相对 团队空间/阿里云/成都城运云) 与文件名
.\upload-zspace.ps1 -File "D:\tmp\scan.jpg" -TargetDir "签到表" -Name "签到表20260901.jpg"
#>
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$File,

    # 可选：手动指定相对目录(相对 /sata1/public/阿里云/成都城运云/)，默认按文件名自动识别
    [string]$TargetDir,

    # 可选：最终文件名，默认自动生成标准名
    [string]$Name,

    # 可选：直接传 cookie 字符串
    [string]$Cookie,

    # NAS 固定参数（登录页/ cookie 可查）
    [string]$NasId = "Z0400102LDZX5",
    [string]$Version = "2.3.2026080501",
    [string]$DeviceId = ""
)

$ErrorActionPreference = "Stop"

# ---------- 0. 路径常量 ----------
$PUBLIC_ROOT = "/sata1/public/阿里云/成都城运云"
$COOKIE_FILE = Join-Path $HOME ".jkj\cookie.txt"
$JKJ_FILE    = Join-Path $HOME ".jkj\jkj.yaml"

# ---------- 1. 校验本地文件 ----------
if (-not (Test-Path $File)) { throw "本地文件不存在: $File" }
$localInfo = Get-Item $File
$fileBytes = [System.IO.File]::ReadAllBytes($File)
$fileSize  = $localInfo.Length
if ($fileSize -eq 0) { throw "文件为空，拒绝上传: $File" }

# ---------- 2. 确定目标目录与文件名 ----------
$baseName = [System.IO.Path]::GetFileName($File)

# 从文件名解析日期 YYYYMMDD（命名规律里那种）
$m = [regex]::Match($baseName, '(\d{8})')
$dateStr = if ($m.Success) { $m.Groups[1].Value } else { Get-Date -Format "yyyyMMdd" }
$monthDir = $dateStr.Substring(0, 6)   # YYYYMM

if ([string]::IsNullOrEmpty($TargetDir)) {
    if ($baseName -match '巡检') {
        $TargetDir = "巡检日报/$monthDir"
    } elseif ($baseName -match '签到') {
        $TargetDir = "签到表"
    } elseif ($baseName -match '交班') {
        $TargetDir = "每日交接班记录及事件记录"
    } else {
        # 无法识别：默认放巡检日报当月（可再手动指定）
        Write-Warning "无法从文件名识别类别，默认归入 巡检日报/$monthDir；如不正确请用 -TargetDir 覆盖。"
        $TargetDir = "巡检日报/$monthDir"
    }
}

if ([string]::IsNullOrEmpty($Name)) {
    if ($baseName -match '巡检') {
        # 取 YYYYMMDD-HH 段，形如 20260901-15
        $hh = if ($baseName -match '(\d{8})-(\d{2})') { $matches[2] } else { Get-Date -Format "HH" }
        $Name = "城运云平台系统日常巡检记录${dateStr}-${hh}.jpg"
    } elseif ($baseName -match '签到') {
        $Name = "签到表${dateStr}.jpg"
    } elseif ($baseName -match '交班') {
        $Name = "交班表${dateStr}.jpg"
    } else {
        $Name = $baseName
    }
}

$targetFullPath = "$PUBLIC_ROOT/$TargetDir/$Name"

# ---------- 3. 获取 cookie / token ----------
if (-not [string]::IsNullOrEmpty($Cookie)) {
    $cookieStr = $Cookie
} elseif ($env:ZSPACE_COOKIE) {
    $cookieStr = $env:ZSPACE_COOKIE
} elseif (Test-Path $COOKIE_FILE) {
    $cookieStr = (Get-Content $COOKIE_FILE -Raw -ErrorAction Stop).Trim()
} else {
    throw "未找到登录 cookie。请先用浏览器登录 zconnect.cn 并把 document.cookie 写入 $COOKIE_FILE（或用 -Cookie / 环境变量 ZSPACE_COOKIE 传入）。"
}

# 从 cookie 提取 token / device_id / username / userid
$getCk = { param($c, $k) $m2 = [regex]::Match($c, "(?:^|;| )$k=([^;]+)"); if ($m2.Success) { [uri]::UnescapeDataString($m2.Groups[1].Value) } else { "" } }
$token    = & $getCk $cookieStr "zenithtoken"
$nasId    = if (& $getCk $cookieStr "nas_id") { & $getCk $cookieStr "nas_id" } else { $NasId }
$deviceId = if (-not [string]::IsNullOrEmpty($DeviceId)) { $DeviceId } else { & $getCk $cookieStr "device_id" }
$username = & $getCk $cookieStr "username"
$userid   = & $getCk $cookieStr "userid"
if ([string]::IsNullOrEmpty($token)) { throw "cookie 中未找到 zenithtoken（token 可能已过期），请重新登录刷新 $COOKIE_FILE。" }

# ---------- 4. 计算上传元数据 ----------
$sha1    = [System.Security.Cryptography.SHA1]::Create()
$uuid    = ([BitConverter]::ToString($sha1.ComputeHash($fileBytes)) -replace '-','').ToLower()
$modifyTime = [math]::Floor([double]::Parse($localInfo.LastWriteTime.ToFileTimeUtc()) / 10000000 - 11644473600)
$encodedPath = [uri]::EscapeDataString($targetFullPath)
$rnd   = [math]::Floor((Get-Date).ToFileTimeUtc()/10000).ToString() + "_" + (Get-Random -Maximum 9999).ToString()
$url   = "https://www.zconnect.cn/v2/file/upload?remote_port=8050&rnd=$rnd&webagent=v2"

# cookie 字符串统一（确保含必要键）
$cookieSend = "webagent=v2; nas_id=$nasId; zenithtoken=$token; username=$username; userid=$userid; plat=web; app=file; device=PC; version=$Version; device_id=$deviceId"

Write-Host "==> 上传: $($localInfo.Name) ($([math]::Round($fileSize/1MB,2)) MB)"
Write-Host "==> 目标: $targetFullPath"

# ---------- 5. 调用上传 API（curl.exe）----------
$args = @('-s','-X','POST', $url,
    '-H','Content-Type: application/octet-stream',
    '-H',"path: $encodedPath",
    '-H',"size: $fileSize",
    '-H',"uuid: $uuid",
    '-H','seek: 0',
    '-H','crtime: ',
    '-H',"modify_time: $modifyTime",
    '-H','rename: 0',
    '-H',"token: $token",
    '-H','plat: web',
    '-H',"nasid: $nasId",
    '-H',"version: $Version",
    '-H',"device_id: $deviceId",
    '-H','device: PC (Chrome/151.0.0.0)',
    '-H','remote-port: 8050',
    '-H','request-purpose: 4',
    '-H','device-type: web',
    '-H','split: 1',
    '-H',"Cookie: $cookieSend",
    '--data-binary',"@$File",
    '-w',"`nHTTP_CODE:%{http_code}",
    '--max-time','180')

$result = & curl.exe @args
Write-Host ""
Write-Host "==> 响应: $result"

if ($result -match '"code":"200"' -and $result -match '"path":"[^"]*' -and $result -match ([regex]::Escape([uri]::EscapeDataString($Name)))) {
    Write-Host ""
    Write-Host "✅ 上传成功: $targetFullPath"
} else {
    Write-Warning "⚠️ 响应未含明显成功标志，请检查上方输出（token 过期会是 login first/401）。"
}

# ---------- 6. 回读校验（可选，失败不影响主流程）----------
try {
    $listUrl  = "https://www.zconnect.cn/v2/file/list/stream?&webagent=v2"
    $listBody = "path=$([uri]::EscapeDataString((Split-Path $targetFullPath -Parent)))&start=0&num=100&sortby=mtime&ftype=0&app=file&order=desc&show_hidden=0&dup=0"
    $verify = & curl.exe -s -X POST $listUrl --data-binary $listBody -H 'Content-Type: application/x-www-form-urlencoded' -H "Cookie: $cookieSend" -H "token: $token" -H "plat: web" -H "nasid: $nasId" -H "version: $Version" -H "device_id: $deviceId"
    if ($verify -match [regex]::Escape($Name)) { Write-Host "✅ 目录校验通过：$Name 已出现在目标目录。" }
    else { Write-Warning "目录校验未确认到 $Name（可能缓存延迟）。" }
} catch {
    Write-Warning "目录校验跳过：$($_.Exception.Message)"
}