# TraeWork / TraeCode 技能插件一键安装脚本 (Windows)
# 用法:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#       默认: 安装到全局 $env:USERPROFILE\.trae-cn\skills (软链接模式, 需管理员/开发者模式)
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -Mode copy
#       复制模式 (不依赖符号链接权限, 离线可用)
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -Mode project -ProjectDir D:\work\my-project
#       安装到指定项目的 .trae/skills (复制模式)
#
# 也可直接右键 install.ps1 -> 使用 PowerShell 运行 (首次建议选 copy 模式)

param(
    [ValidateSet("link","copy","project")]
    [string]$Mode = "link",
    [string]$ProjectDir = ""
)

$ErrorActionPreference = "Stop"

# ---- 源目录: 跟随脚本所在目录 ----
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkipDirs = @(".idea", ".lh", ".git")
$BS = [char]92

# ---- 颜色 ----
$C_CYAN  = "Cyan"
$C_GREEN = "Green"
$C_YELLOW= "Yellow"
$C_GRAY  = "Gray"
$C_RED   = "Red"
$C_DARKC = "DarkCyan"

# ---- 目标目录解析 ----
$ForceCopy = $false
$ModeLabel = ""
switch ($Mode) {
    "project" {
        if ([string]::IsNullOrWhiteSpace($ProjectDir)) {
            throw "[ERROR] project 模式需要传入 -ProjectDir 参数，例如 -ProjectDir D:\work\xxx"
        }
        $TargetRoot = Join-Path $ProjectDir ".trae\skills"
        $ForceCopy = $true
        $ModeLabel = "project(copy): $ProjectDir"
    }
    "copy" {
        $TargetRoot = Join-Path $env:USERPROFILE ".trae-cn\skills"
        $ForceCopy = $true
        $ModeLabel = "global(copy)"
    }
    default {
        $TargetRoot = Join-Path $env:USERPROFILE ".trae-cn\skills"
        $ForceCopy = $false
        $ModeLabel = "global(symlink)"
    }
}

Write-Host "===== TraeWork Skills Installer (Windows) =====" -ForegroundColor $C_CYAN
Write-Host ("Plugin root : " + $SourceRoot)
Write-Host ("Install mode: " + $ModeLabel)
Write-Host ("Target dir  : " + $TargetRoot)
Write-Host ""

# ---- 存在性检查 ----
if (-not (Test-Path -LiteralPath $SourceRoot -PathType Container)) {
    throw "[ERROR] Source root not found: $SourceRoot"
}
if (-not (Test-Path -LiteralPath $TargetRoot -PathType Container)) {
    Write-Host ("[CREATE] Target dir missing, creating: " + $TargetRoot) -ForegroundColor $C_YELLOW
    New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null
}

# ---- 枚举 Skill 目录 ----
$skillNames = @()
Get-ChildItem -LiteralPath $SourceRoot -Directory | ForEach-Object {
    $d = $_
    if ($SkipDirs -contains $d.Name) { return }
    if (Test-Path -LiteralPath (Join-Path $d.FullName "SKILL.md") -PathType Leaf) {
        $skillNames += $d.Name
    }
}
if ($skillNames.Count -eq 0) {
    Write-Warning ("No SKILL.md subdirs under " + $SourceRoot)
    exit 0
}
Write-Host ("[SCAN] Found " + $skillNames.Count + " skills:") -ForegroundColor $C_GREEN
foreach ($n in $skillNames) { Write-Host ("  - " + $n) }
Write-Host ""

# ---- 工具函数: 递归复制（跳过 __pycache__、.pyc 等） ----
function Copy-SkillDir([string]$src, [string]$dst) {
    if (Test-Path -LiteralPath $dst) {
        # 先清空目标同名内容 (但不删外层, 外层已经备份或不存在)
    }
    New-Item -ItemType Directory -Path $dst -Force | Out-Null
    # Robocopy 镜像复制, 跳过编译产物
    $rcLog = "$env:TEMP\trae_skill_copy_$([guid]::NewGuid().ToString('N')).log"
    & robocopy $src $dst /E /NFL /NDL /NJH /NJS /NP `
        /XD __pycache__ .git .idea `
        /XF *.pyc *.pyo *.log 2>&1 | Out-Null
    # robocopy 0-7 都算成功
    if ($LASTEXITCODE -le 7) { return $true } else { return $false }
}

# ---- 安装 ----
$succ = 0; $skip = 0; $fail = 0
foreach ($name in $skillNames) {
    $src = Join-Path $SourceRoot $name
    $dst = Join-Path $TargetRoot $name

    Write-Host ("[" + $name + "]") -ForegroundColor $C_CYAN -NoNewline
    Write-Host (" " + $src)

    $needInstall = $true

    # 目标存在处理
    if (Test-Path -LiteralPath $dst) {
        $item = Get-Item -LiteralPath $dst -Force
        if (-not $ForceCopy -and $item.LinkType -eq "SymbolicLink") {
            $nc = [System.IO.Path]::GetFullPath($item.Target).TrimEnd($BS)
            $ne = [System.IO.Path]::GetFullPath($src).TrimEnd($BS)
            if ($nc -ieq $ne) {
                Write-Host "  [SKIP] Symlink OK" -ForegroundColor $C_GRAY
                $skip++; $needInstall = $false
            } else {
                Write-Host "  [RECREATE] symlink target changed" -ForegroundColor $C_YELLOW
                Remove-Item -LiteralPath $dst -Force -Recurse
            }
        } else {
            $ts = Get-Date -Format "yyyyMMddHHmmss"
            $bak = $dst + ".bak." + $ts
            Write-Host ("  [BACKUP] Existing item -> " + $bak) -ForegroundColor $C_YELLOW
            Move-Item -LiteralPath $dst -Destination $bak -Force
        }
    }

    if (-not $needInstall) { continue }

    if ($ForceCopy) {
        try {
            $ok = Copy-SkillDir $src $dst
            if ($ok) {
                Write-Host "  [OK] Copied" -ForegroundColor $C_GREEN
                $succ++
            } else {
                Write-Host "  [FAIL] robocopy returned non-zero" -ForegroundColor $C_RED
                $fail++
            }
        } catch {
            Write-Host ("  [FAIL] " + $_.Exception.Message) -ForegroundColor $C_RED
            $fail++
        }
    } else {
        try {
            New-Item -ItemType SymbolicLink -Path $dst -Target $src -Force | Out-Null
            $v = Get-Item -LiteralPath $dst -Force
            if ($v.LinkType -eq "SymbolicLink") {
                Write-Host "  [OK] Symlinked" -ForegroundColor $C_GREEN
                $succ++
            } else {
                throw "post-check: not SymbolicLink"
            }
        } catch {
            $msg = $_.Exception.Message
            Write-Host ("  [FAIL] " + $msg) -ForegroundColor $C_RED
            if ($msg -like "*privilege*" -or $msg -like "* SeCreateSymbolicLinkPrivilege *") {
                Write-Host "      -> TIP: 权限不足, 切换 copy 模式重试:" -ForegroundColor DarkYellow
                Write-Host '         powershell -ExecutionPolicy Bypass -File .\install.ps1 -Mode copy' -ForegroundColor DarkYellow
            }
            $fail++
        }
    }
}

# ---- 汇总 ----
$fclr = if ($fail -gt 0) { $C_RED } else { $C_GRAY }
Write-Host ""
Write-Host "===== DONE =====" -ForegroundColor $C_CYAN
Write-Host ("  Success: " + $succ) -ForegroundColor $C_GREEN
Write-Host ("  Skipped: " + $skip) -ForegroundColor $C_GRAY
Write-Host ("  Failed : " + $fail) -ForegroundColor $fclr
Write-Host ""
Write-Host "Next step: Restart TraeWork / TraeCode, then Settings -> Skills & Commands -> Skills." -ForegroundColor $C_DARKC
if ($Mode -eq "project") {
    Write-Host "         项目模式: 请在 TraeCode 中重新打开该项目。" -ForegroundColor $C_DARKC
}
