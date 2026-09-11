# 用本机 Chrome 把封面 HTML 渲染成 PNG
# 用法：.\生成封面.ps1          渲染全部方案
#       .\生成封面.ps1 B        只渲染方案 B
param([string]$Only = "")

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chrome)) { $chrome = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" }

$variants = if ($Only) { @($Only) } else { @("A", "B", "C") }

foreach ($v in $variants) {
    $src = Join-Path $PSScriptRoot "封面-$v.html"
    if (-not (Test-Path $src)) { Write-Output "跳过（没有 $src）"; continue }
    $out = Join-Path $PSScriptRoot "封面-$v.png"
    Start-Process $chrome -ArgumentList @(
        "--headless=new",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        "--window-size=1600,2400",
        "--screenshot=$out",
        ([System.Uri]::new($src).AbsoluteUri)
    ) -Wait -WindowStyle Hidden
    Add-Type -AssemblyName System.Drawing
    $img = [System.Drawing.Image]::FromFile($out)
    "封面-$v.png  {0} x {1}" -f $img.Width, $img.Height
    $img.Dispose()
}