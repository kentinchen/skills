# Batch-create TraeWork global Skills directory symbolic links.
# Links each skill subdir under D:\project\skills into $env:USERPROFILE\.trae-cn\skills.

$ErrorActionPreference = "Stop"

# ========== CONFIG ==========
$SourceRoot = "D:\project\skills"
$TargetRoot = Join-Path $env:USERPROFILE ".trae-cn\skills"

# Directory names to skip (not skills)
$SkipDirs = @(".idea", ".lh", ".git")
$BS = [char]92
# ============================

Write-Host "===== TraeWork Skills Symlink Batch Script =====" -ForegroundColor Cyan
Write-Host ("Source: " + $SourceRoot)
Write-Host ("Target: " + $TargetRoot)
Write-Host ""

# ---------- 1. Existence checks ----------
if (-not (Test-Path -LiteralPath $SourceRoot -PathType Container)) {
    Write-Error ("Source directory does not exist: " + $SourceRoot)
    exit 1
}

if (-not (Test-Path -LiteralPath $TargetRoot -PathType Container)) {
    Write-Host ("[CREATE] Target dir missing, creating: " + $TargetRoot) -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null
}

# ---------- 2. Enumerate source skill dirs ----------
$skillDirs = @()
Get-ChildItem -LiteralPath $SourceRoot -Directory | ForEach-Object {
    $d = $_
    if ($SkipDirs -contains $d.Name) { return }
    $skillMd = Join-Path $d.FullName "SKILL.md"
    if (Test-Path -LiteralPath $skillMd -PathType Leaf) {
        $skillDirs += $d
    }
}

if ($skillDirs.Count -eq 0) {
    Write-Warning ("No skill directories with SKILL.md found under " + $SourceRoot)
    exit 0
}

Write-Host ("[SCAN] Found " + $skillDirs.Count + " skill directories:") -ForegroundColor Green
foreach ($d in $skillDirs) {
    Write-Host ("  - " + $d.Name)
}
Write-Host ""

# ---------- 3. Create symlinks one by one ----------
$successCount = 0
$skipCount = 0
$failCount = 0

foreach ($dir in $skillDirs) {
    $linkPath = Join-Path $TargetRoot $dir.Name
    $targetPath = $dir.FullName

    Write-Host ("[" + $dir.Name + "]") -ForegroundColor Cyan -NoNewline
    Write-Host (" " + $targetPath)

    $needCreate = $true

    # Check if link path already exists
    if (Test-Path -LiteralPath $linkPath) {
        $item = Get-Item -LiteralPath $linkPath -Force

        if ($item.LinkType -eq "SymbolicLink") {
            $currentTarget = $item.Target
            $nc = [System.IO.Path]::GetFullPath($currentTarget).TrimEnd($BS)
            $ne = [System.IO.Path]::GetFullPath($targetPath).TrimEnd($BS)

            if ($nc -ieq $ne) {
                Write-Host "  [SKIP] Symlink exists and points correctly" -ForegroundColor Gray
                $skipCount++
                $needCreate = $false
            } else {
                Write-Host ("  [RECREATE] Wrong target: current=" + $currentTarget + " , expected=" + $targetPath) -ForegroundColor Yellow
                Remove-Item -LiteralPath $linkPath -Force -Recurse
                $needCreate = $true
            }
        } else {
            $ts = Get-Date -Format "yyyyMMddHHmmss"
            $backupPath = $linkPath + ".bak." + $ts
            Write-Host ("  [BACKUP] Non-link item exists, backed up to: " + $backupPath) -ForegroundColor Yellow
            Move-Item -LiteralPath $linkPath -Destination $backupPath -Force
            $needCreate = $true
        }
    }

    if (-not $needCreate) {
        continue
    }

    # Create symlink
    try {
        New-Item -ItemType SymbolicLink -Path $linkPath -Target $targetPath -Force | Out-Null

        $verify = Get-Item -LiteralPath $linkPath -Force
        if ($verify.LinkType -eq "SymbolicLink") {
            Write-Host ("  [OK] Symlink created -> " + $targetPath) -ForegroundColor Green
            $successCount++
        } else {
            throw "Post-create LinkType is not SymbolicLink"
        }
    } catch {
        $msg = $_.Exception.Message
        Write-Host ("  [FAIL] " + $msg) -ForegroundColor Red
        if ($msg -like "*required*privilege*" -or $msg -like "*privilege*" -or $msg -like "* SeCreateSymbolicLinkPrivilege *") {
            Write-Host "      -> TIP: Creating symlinks on Windows requires ADMIN PRIVILEGES or DEVELOPER MODE enabled." -ForegroundColor DarkYellow
            Write-Host "         Re-run this script as Administrator, or enable Developer Mode under" -ForegroundColor DarkYellow
            Write-Host "         Settings -> Update & Security -> For developers -> Developer Mode." -ForegroundColor DarkYellow
        }
        $failCount++
    }
}

# ---------- 4. Summary ----------
$failColor = "Gray"
if ($failCount -gt 0) { $failColor = "Red" }
Write-Host ""
Write-Host "===== DONE =====" -ForegroundColor Cyan
Write-Host ("  Success: " + $successCount) -ForegroundColor Green
Write-Host ("  Skipped: " + $skipCount) -ForegroundColor Gray
Write-Host ("  Failed : " + $failCount) -ForegroundColor $failColor
Write-Host ""
Write-Host "Next step: Restart TraeWork, then check Settings -> Skills & Commands -> Skills." -ForegroundColor DarkCyan
