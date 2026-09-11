# 生成电子书书稿
# 把 ..\正文\ 里的 51 章转换成 GitBook / HonKit 能读的结构：
#   README.md（书名页）  SUMMARY.md（目录）  正文\chNN.md（每章一页）  卷X.md（分卷页）
# 正文改动之后，重新运行本脚本即可同步。用法：  .\生成电子书.ps1

$ErrorActionPreference = "Stop"
$out   = $PSScriptRoot
$proj  = Split-Path -Parent $out
$src   = Join-Path $proj "正文"
$pages = Join-Path $out "正文"
$enc   = [System.Text.UTF8Encoding]::new($false)

if (-not (Test-Path $pages)) { New-Item -ItemType Directory -Path $pages | Out-Null }

$volumeOf = @{}
foreach ($n in 1..7)   { $volumeOf[$n] = 1 }
foreach ($n in 8..13)  { $volumeOf[$n] = 2 }
foreach ($n in 14..23) { $volumeOf[$n] = 3 }
foreach ($n in 24..32) { $volumeOf[$n] = 4 }
foreach ($n in 33..51) { $volumeOf[$n] = 5 }

$volumeName  = @{ 1 = "卷一 · 灰"; 2 = "卷二 · 湮"; 3 = "卷三 · 渡"; 4 = "卷四 · 新岸"; 5 = "卷五 · 归" }
$volumeTheme = @{ 1 = "水，以及为水而死的人。"; 2 = "天不再给时间了。"; 3 = "人类最后一次为自己打仗，是为了离开。"; 4 = "梦是真的。"; 5 = "海还在。" }
$volumeFile  = @{ 1 = "卷一.md"; 2 = "卷二.md"; 3 = "卷三.md"; 4 = "卷四.md"; 5 = "卷五.md" }

$rows = @()
foreach ($f in (Get-ChildItem (Join-Path $src "*.md") | Sort-Object Name)) {
    if ($f.BaseName -notmatch '^第(\d+)章') { continue }
    $n = [int]$Matches[1]

    $text  = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8) -replace "`r`n", "`n"
    $lines = $text -split "`n"

    # 找到章标题那一行（## 第X章……），它前面的东西一律丢掉（旧卷标题等）
    $start = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^##\s+第.+章') { $start = $i; break }
    }
    if ($start -lt 0) { throw ("找不到章标题：" + $f.Name) }

    $title = $lines[$start] -replace '^##\s+', ''
    $body  = New-Object System.Collections.Generic.List[string]
    $body.Add('# ' + $title)
    for ($i = $start + 1; $i -lt $lines.Count; $i++) {
        $ln = $lines[$i]
        # 歌词/引文保留换行：行尾补两个空格
        if ($ln -match '^>\s') { $body.Add($ln.TrimEnd() + '  ') } else { $body.Add($ln) }
    }

    $file = 'ch{0:D2}.md' -f $n
    [System.IO.File]::WriteAllText((Join-Path $pages $file), ($body -join "`n").Trim() + "`n", $enc)
    $rows += [pscustomobject]@{ N = $n; Vol = $volumeOf[$n]; Title = $title; File = '正文/' + $file }
}

# 分卷页
foreach ($v in 1..5) {
    $t = "# " + $volumeName[$v] + "`n`n> " + $volumeTheme[$v] + "`n"
    [System.IO.File]::WriteAllText((Join-Path $out $volumeFile[$v]), $t, $enc)
}

# 目录
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('# 目录')
[void]$sb.AppendLine()
[void]$sb.AppendLine('* [书名页](README.md)')
foreach ($v in 1..5) {
    [void]$sb.AppendLine()
    [void]$sb.AppendLine('## ' + $volumeName[$v])
    [void]$sb.AppendLine()
    [void]$sb.AppendLine(('* [{0}]({1})' -f $volumeName[$v], $volumeFile[$v]))
    foreach ($r in ($rows | Where-Object { $_.Vol -eq $v })) {
        [void]$sb.AppendLine(('* [{0}]({1})' -f $r.Title, $r.File))
    }
}
[System.IO.File]::WriteAllText((Join-Path $out 'SUMMARY.md'), $sb.ToString(), $enc)

"已生成章节页 " + $rows.Count + " 个，目录 SUMMARY.md 就绪。"