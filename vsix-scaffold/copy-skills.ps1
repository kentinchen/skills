$src = 'D:\project\skills'
$dst = 'D:\project\skills\vsix-scaffold\skills'
$names = @(
    'cpolar-tunnel','dddd-ocr','knowbase-ingest','nazha-skills',
    'scop-report','wct-skill-publish','yg-skills','yw-skills','zcm-task-add-comment'
)

New-Item -ItemType Directory -Path $dst -Force | Out-Null

foreach ($n in $names) {
    $s = Join-Path $src $n
    $d = Join-Path $dst $n
    if (Test-Path $d) { Remove-Item $d -Recurse -Force }
    & robocopy $s $d /E /NFL /NDL /NJH /NJS /NP /XD __pycache__ .git .idea /XF *.pyc *.pyo 2>&1 | Out-Null
    if ($LASTEXITCODE -le 7) {
        Write-Host ('  [OK] ' + $n) -ForegroundColor Green
    } else {
        Write-Host ('  [FAIL] ' + $n + ' exit=' + $LASTEXITCODE) -ForegroundColor Red
    }
}
