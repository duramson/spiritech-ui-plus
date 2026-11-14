<#
.SYNOPSIS
Installs duramson UI+ into a Spiritech client, updates it, or takes it out again.

.DESCRIPTION
The Windows twin of install.py, for players without Python: it reads the same patches and writes the same files and
the same ui-plus.json, so either one can update or undo what the other installed. install.bat starts it.

UI+ ships none of Project Rubi-Ka's files, only patches: its changes to their files. This reads the files from your
own client and patches them there. The Core files are patched in place, each kept as it was beside it as
<name>.ui-plus-backup; each window is copied from the client's bundled package, patched, and put into the per-user
package folder (%LOCALAPPDATA%\ProjectRubiKa\ui-packages) as ui-plus-<name>.

.EXAMPLE
.\install.ps1
A menu.
.EXAMPLE
.\install.ps1 -Install
Install, or update to this copy's version.
.EXAMPLE
.\install.ps1 -Uninstall
Put the client's own files back and remove UI+'s packages.
.EXAMPLE
.\install.ps1 -Status -Client "D:\Games\PRK-AO-Native\client"
What is installed, in a client the installer doesn't find by itself.
#>
param([switch]$Install, [switch]$Uninstall, [switch]$Status, [string]$Client)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$Here = $PSScriptRoot
$Title = 'duramson UI+ for Spiritech'
$MadeFor = '0.2.1'   # the client version the patches were made against
$StateName = 'ui-plus.json'
$BackupSuffix = '.ui-plus-backup'
$Prefix = 'ui-plus-'
$StockName = 'stock-package.txt'
$Skip = @('.DS_Store', 'Thumbs.db', 'desktop.ini')
$NoNl = [string][char]0   # marks a last line without a line break while patching
$Utf8 = New-Object System.Text.UTF8Encoding($false)
$StrictUtf8 = New-Object System.Text.UTF8Encoding($false, $true)
$SettingsName = 'ui_plus_settings.xml'   # in UI\Packages\Core: the settings the installer asks for, read by Core's Lua
$DefaultTooltipDelay = 1000   # milliseconds the pointer rests before a tooltip shows, about the original client's wait

function Say([string]$Text = '') { Write-Host $Text }

function Join([string]$Base) {
    $path = $Base
    foreach ($part in $args) { $path = [IO.Path]::Combine($path, [string]$part) }
    return $path
}

function Get-Version {
    $path = Join $Here 'VERSION'
    if (Test-Path -LiteralPath $path) { return ([IO.File]::ReadAllText($path)).Trim() }
    return 'dev'
}

function Get-Sha([byte[]]$Data) {
    $hash = [Security.Cryptography.SHA256]::Create().ComputeHash($Data)
    return -join ($hash | ForEach-Object { $_.ToString('x2') })
}

# ---- text files: patched with LF line breaks, written back the way the file had them ---------------------------------

function ConvertFrom-FileBytes([byte[]]$Data) {
    $bom = $Data.Length -ge 3 -and $Data[0] -eq 0xEF -and $Data[1] -eq 0xBB -and $Data[2] -eq 0xBF
    $offset = 0
    if ($bom) { $offset = 3 }
    $text = $StrictUtf8.GetString($Data, $offset, $Data.Length - $offset)
    $crlf = $text.Contains("`r`n")
    return @{ Text = $text.Replace("`r`n", "`n"); Crlf = $crlf; Bom = $bom; Created = $false }
}

function ConvertTo-FileBytes([string]$Text, [bool]$Crlf, [bool]$Bom) {
    if ($Crlf) { $Text = $Text.Replace("`n", "`r`n") }
    $body = $Utf8.GetBytes($Text)
    if ($Bom) { $body = [byte[]](@(0xEF, 0xBB, 0xBF) + $body) }
    return , ([byte[]]$body)
}

function Test-NoNl([string]$Line) {
    return $Line.Length -gt 0 -and $Line[$Line.Length - 1] -eq [char]0
}

function Split-Lines([string]$Text) {
    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($part in $Text.Split([char]"`n")) { $lines.Add($part) }
    if ($lines[$lines.Count - 1].Length -eq 0) { $lines.RemoveAt($lines.Count - 1) }
    else { $lines[$lines.Count - 1] = $lines[$lines.Count - 1] + $NoNl }
    return , $lines
}

function Join-Lines($Lines) {
    if ($Lines.Count -gt 0 -and (Test-NoNl $Lines[$Lines.Count - 1])) {
        $text = [string]::Join("`n", $Lines.ToArray())
        return $text.Substring(0, $text.Length - 1)
    }
    $builder = New-Object System.Text.StringBuilder
    foreach ($line in $Lines) { [void]$builder.Append($line).Append("`n") }
    return $builder.ToString()
}

# ---- unified diffs ---------------------------------------------------------------------------------------------------

# Each hunk is read by its line counts, so a context line whose leading space an editor removed still counts.
function Get-Hunks([string]$Diff) {
    $lines = $Diff.Replace("`r`n", "`n").Split([char]"`n")
    $hunks = New-Object System.Collections.Generic.List[object]
    $i = 0
    while ($i -lt $lines.Length) {
        $match = [regex]::Match($lines[$i], '^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
        $i++
        if (-not $match.Success) { continue }
        $oldCount = 1
        if ($match.Groups[2].Success) { $oldCount = [int]$match.Groups[2].Value }
        $newCount = 1
        if ($match.Groups[4].Success) { $newCount = [int]$match.Groups[4].Value }
        $marks = New-Object System.Collections.Generic.List[string]
        $texts = New-Object System.Collections.Generic.List[string]
        while ($oldCount -gt 0 -or $newCount -gt 0 -or
               ($i -lt $lines.Length -and $lines[$i].StartsWith('\', [StringComparison]::Ordinal))) {
            if ($i -ge $lines.Length) { throw 'a change in the patch ends early' }
            $line = $lines[$i]
            $i++
            if ($line.StartsWith('\', [StringComparison]::Ordinal)) {
                if ($texts.Count -gt 0) { $texts[$texts.Count - 1] = $texts[$texts.Count - 1] + $NoNl }
                continue
            }
            if ($line.Length -eq 0) { $mark = ' '; $text = '' }
            else { $mark = [string]$line[0]; $text = $line.Substring(1) }
            if ($mark -cne ' ' -and $mark -cne '-' -and $mark -cne '+') { throw "the patch has a line it can't read: $line" }
            if ($mark -cne '+') { $oldCount-- }
            if ($mark -cne '-') { $newCount-- }
            $marks.Add($mark)
            $texts.Add($text)
        }
        if ($oldCount -lt 0 -or $newCount -lt 0) { throw "a change in the patch doesn't match its line counts" }
        $hunks.Add(@{ OldStart = [int]$match.Groups[1].Value; NewStart = [int]$match.Groups[3].Value
                      Marks = $marks; Texts = $texts })
    }
    return , $hunks
}

# Old with the diff applied (or taken out, -Reverse). Each change must find its lines exactly, at most shifted.
function Invoke-Patch([string]$Old, [string]$Diff, [bool]$Reverse = $false) {
    $a = Split-Lines $Old
    $out = New-Object System.Collections.Generic.List[string]
    $pos = 0
    $shift = 0
    foreach ($hunk in (Get-Hunks $Diff)) {
        $start = $hunk.OldStart
        $added = '+'
        $removed = '-'
        if ($Reverse) { $start = $hunk.NewStart; $added = '-'; $removed = '+' }
        $want = New-Object System.Collections.Generic.List[string]
        $give = New-Object System.Collections.Generic.List[string]
        for ($k = 0; $k -lt $hunk.Texts.Count; $k++) {
            if ($hunk.Marks[$k] -cne $added) { $want.Add($hunk.Texts[$k]) }
            if ($hunk.Marks[$k] -cne $removed) { $give.Add($hunk.Texts[$k]) }
        }
        $expected = $start
        if ($want.Count -gt 0) { $expected = $start - 1 }
        $best = -1
        for ($at = $pos; $at -le $a.Count - $want.Count; $at++) {
            $fits = $true
            for ($k = 0; $k -lt $want.Count; $k++) {
                if (-not [string]::Equals($a[$at + $k], $want[$k])) { $fits = $false; break }
            }
            if ($fits -and ($best -lt 0 -or
                            [Math]::Abs($at - $expected - $shift) -lt [Math]::Abs($best - $expected - $shift))) {
                $best = $at
            }
        }
        if ($best -lt 0) { throw "the change at line $start doesn't fit" }
        for ($k = $pos; $k -lt $best; $k++) { $out.Add($a[$k]) }
        foreach ($line in $give) { $out.Add($line) }
        $pos = $best + $want.Count
        $shift = $best - $expected
    }
    for ($k = $pos; $k -lt $a.Count; $k++) { $out.Add($a[$k]) }
    return (Join-Lines $out)
}

# ---- where things are ------------------------------------------------------------------------------------------------

function Test-Client([string]$Path) {
    return [bool]$Path -and (Test-Path -LiteralPath (Join $Path 'UI' 'Packages' 'Core') -PathType Container)
}

# The client folder from what the user gave: the client folder itself, the launcher folder holding it,
# PRK.Client.exe, the macOS PRK Launcher app, or a folder with the launcher's LauncherSettings.json.
function Resolve-Client([string]$Given) {
    if (-not $Given) { return $null }
    $path = $Given.Trim().Trim('"', "'")
    if ($path.StartsWith('~')) { $path = $HOME + $path.Substring(1) }
    try { $path = [IO.Path]::GetFullPath($path) } catch { return $null }
    if (Test-Path -LiteralPath $path -PathType Leaf) { $path = [IO.Path]::GetDirectoryName($path) }
    foreach ($candidate in @($path, (Join $path 'client'), (Join $path 'Contents' 'MacOS' 'client'))) {
        if (Test-Client $candidate) { return $candidate }
    }
    $settings = Join $path 'LauncherSettings.json'
    if (Test-Path -LiteralPath $settings -PathType Leaf) {
        try {
            $clientPath = ([IO.File]::ReadAllText($settings) | ConvertFrom-Json).ClientPath
            if (Test-Client $clientPath) { return $clientPath }
        } catch { }
    }
    return $null
}

function Get-Candidates {
    $list = New-Object System.Collections.Generic.List[string]
    if ($env:UIPLUS_CLIENT) { $list.Add($env:UIPLUS_CLIENT) }
    $folder = $Here   # wherever this copy sits: inside the game folder, or beside it
    for ($k = 0; $k -lt 4 -and $folder; $k++) {
        $list.Add($folder)
        $list.Add((Join $folder 'PRK-AO-Native'))
        $folder = [IO.Path]::GetDirectoryName($folder)
    }
    if (Get-Variable -Name IsMacOS -ValueOnly -ErrorAction SilentlyContinue) {
        $list.Add('/Applications/PRK Launcher.app')
        $list.Add((Join $HOME 'Applications' 'PRK Launcher.app'))
    }
    if ($env:OS -eq 'Windows_NT') {
        foreach ($drive in [IO.DriveInfo]::GetDrives()) {
            foreach ($sub in @('Games\PRK-AO-Native', 'PRK-AO-Native', 'Program Files\PRK-AO-Native',
                               'Program Files (x86)\PRK-AO-Native')) {
                $list.Add((Join $drive.RootDirectory.FullName $sub))
            }
        }
    }
    foreach ($base in @($env:LOCALAPPDATA, $HOME)) {
        if ($base) {
            foreach ($sub in @('PRK-AO-Native', 'Games', 'Desktop', 'Downloads')) {
                if ($sub -eq 'PRK-AO-Native') { $list.Add((Join $base $sub)) }
                else { $list.Add((Join $base $sub 'PRK-AO-Native')) }
            }
        }
    }
    return , $list
}

function Find-Client {
    foreach ($candidate in (Get-Candidates)) {
        $found = Resolve-Client $candidate
        if ($found) { return $found }
    }
    return $null
}

# The per-user package folder the client reads besides its own UI\Addons.
function Get-PackageDir {
    if (Get-Variable -Name IsMacOS -ValueOnly -ErrorAction SilentlyContinue) {
        $base = Join $HOME 'Library' 'Application Support'
    } elseif (Get-Variable -Name IsLinux -ValueOnly -ErrorAction SilentlyContinue) {
        $base = $env:XDG_DATA_HOME
        if (-not $base) { $base = Join $HOME '.local' 'share' }
    } else {
        $base = $env:LOCALAPPDATA
    }
    return (Join $base 'ProjectRubiKa' 'ui-packages')
}

function Get-ClientVersion([string]$ClientDir) {
    $path = Join $ClientDir 'version.txt'
    if (Test-Path -LiteralPath $path) { return ([IO.File]::ReadAllText($path)).Trim() }
    return 'unknown'
}

function Read-State([string]$ClientDir) {
    $path = Join $ClientDir $StateName
    $state = @{ version = $null; core = @{}; packages = @{}; fonts = @(); tooltip_delay = $DefaultTooltipDelay }
    if (Test-Path -LiteralPath $path) {
        $json = [IO.File]::ReadAllText($path) | ConvertFrom-Json
        $state.version = $json.version
        if ($json.PSObject.Properties['tooltip_delay']) { $state.tooltip_delay = [int]$json.tooltip_delay }
        # the fonts install.py put in (fonts\pixelfont.py), kept for its uninstall; an install from before
        # Notum Grotesk 200 recorded only "font": true
        if ($json.PSObject.Properties['fonts']) {
            $state.fonts = @($json.fonts)
        } elseif ($json.PSObject.Properties['font'] -and $json.font) {
            $state.fonts = @('Notum Grotesk')
        }
        foreach ($entry in $json.core.PSObject.Properties) {
            $state.core[$entry.Name] = @{ sha = $entry.Value.sha; diff = $entry.Value.diff
                                         created = [bool]$entry.Value.created }
        }
        foreach ($entry in $json.packages.PSObject.Properties) {
            $state.packages[$entry.Name] = @{ folder = $entry.Value.folder; id = $entry.Value.id }
        }
    }
    return $state
}

function Save-State([string]$ClientDir, $State) {
    $path = Join $ClientDir $StateName
    if ($State.core.Count -gt 0 -or $State.packages.Count -gt 0) {
        $data = @{ version = $State.version; core = $State.core; packages = $State.packages
                   tooltip_delay = $State.tooltip_delay }
        if ($State.fonts.Count -gt 0) { $data.fonts = @($State.fonts) }
        $json = $data | ConvertTo-Json -Depth 6
        [IO.File]::WriteAllText($path, $json.Replace("`r`n", "`n") + "`n", $Utf8)
    } elseif (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path
    }
}

function Get-FilesOf([string]$Root) {
    $map = @{}
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return , $map }
    $full = (Get-Item -LiteralPath $Root).FullName.TrimEnd('\', '/')
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force)) {
        if ($Skip -contains $file.Name) { continue }
        $map[$file.FullName.Substring($full.Length + 1).Replace('\', '/')] = $file.FullName
    }
    return , $map
}

function Get-RepoCore {
    $root = Join $Here 'core'
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { return }
    Get-ChildItem -LiteralPath $root -Filter '*.diff' -File | Sort-Object Name
}

function Get-RepoPackages {
    $root = Join $Here 'packages'
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { return }
    Get-ChildItem -LiteralPath $root -Directory | Sort-Object Name | Where-Object { (Get-FilesOf $_.FullName).Count -gt 0 }
}

# ---- Core: patched in place ------------------------------------------------------------------------------------------

# Whether a Core file is UI+'s own, one the client doesn't have: it gets no kept copy, and uninstalling deletes it.
# Earlier installers took such a file for the client's own when installing again and kept an empty copy of it, so an
# empty kept copy means the same.
function Test-MadeByUiPlus($Entry, [string]$Backup) {
    return ([bool]$Entry.created -or
            ((Test-Path -LiteralPath $Backup) -and (Get-Item -LiteralPath $Backup).Length -eq 0))
}

# The client's own file for a Core patch, without UI+'s changes: the kept copy while the installed file is still
# UI+'s, else the file in the client with UI+'s last changes taken out where they are still in it. Nothing, for a
# file UI+ makes.
function Get-CoreBase([string]$ClientDir, $State, [string]$Name) {
    $target = Join $ClientDir 'UI' 'Packages' 'Core' $Name
    $backup = $target + $BackupSuffix
    $entry = $null
    if ($State.core.ContainsKey($Name)) { $entry = $State.core[$Name] }
    $made = $null -ne $entry -and (Test-MadeByUiPlus $entry $backup)
    if (-not (Test-Path -LiteralPath $target)) {
        return @{ Text = ''; Crlf = $false; Bom = $false; Created = ($null -eq $entry -or $made) }
    }
    $data = [IO.File]::ReadAllBytes($target)
    if ($entry -and -not $made -and (Test-Path -LiteralPath $backup) -and (Get-Sha $data) -eq $entry.sha) {
        return (ConvertFrom-FileBytes ([IO.File]::ReadAllBytes($backup)))
    }
    $file = ConvertFrom-FileBytes $data
    # UI+'s own file, or changed since UI+ installed it: a client update, or another mod editing UI+'s file
    if ($entry) {
        try {
            $file.Text = Invoke-Patch $file.Text $entry.diff $true
            $file.Created = $made -and [string]::IsNullOrEmpty($file.Text)
        } catch { }
    }
    return $file
}

function Get-CorePlan([string]$ClientDir, $State) {
    $plan = New-Object System.Collections.Generic.List[object]
    foreach ($diffFile in @(Get-RepoCore)) {
        $name = $diffFile.Name.Substring(0, $diffFile.Name.Length - '.diff'.Length)
        $diff = [IO.File]::ReadAllText($diffFile.FullName, $Utf8).Replace("`r`n", "`n")
        $base = Get-CoreBase $ClientDir $State $name
        try {
            $new = Invoke-Patch $base.Text $diff
        } catch {
            $problem = $_.Exception.Message
            try {   # UI+'s changes are in it although nothing records them (ui-plus.json was deleted)
                $base.Text = Invoke-Patch $base.Text $diff $true
                $new = Invoke-Patch $base.Text $diff
            } catch {
                throw "UI/Packages/Core/${name}: $problem. The client's file is not the one this version of UI+ was made for (client $MadeFor)."
            }
        }
        $plan.Add(@{ Name = $name; Diff = $diff; Base = $base; New = $new })
    }
    return , $plan
}

function Write-Core([string]$ClientDir, $State, $Plan) {
    $changed = 0
    foreach ($item in $Plan) {
        $target = Join $ClientDir 'UI' 'Packages' 'Core' $item.Name
        $backup = $target + $BackupSuffix
        if (-not $item.Base.Created) {
            $data = ConvertTo-FileBytes $item.Base.Text $item.Base.Crlf $item.Base.Bom
            if (-not (Test-Path -LiteralPath $backup) -or (Get-Sha ([IO.File]::ReadAllBytes($backup))) -ne (Get-Sha $data)) {
                [IO.File]::WriteAllBytes($backup, $data)
            }
        } elseif (Test-Path -LiteralPath $backup) {
            # a kept copy of a file UI+ made: the empty one an earlier installer left
            Remove-Item -LiteralPath $backup
            Say ("  removed UI/Packages/Core/$($item.Name)$BackupSuffix " +
                 "(UI+ made that file, the client has none to keep)")
            $changed++
        }
        $data = ConvertTo-FileBytes $item.New $item.Base.Crlf $item.Base.Bom
        if (-not (Test-Path -LiteralPath $target) -or (Get-Sha ([IO.File]::ReadAllBytes($target))) -ne (Get-Sha $data)) {
            [IO.File]::WriteAllBytes($target, $data)
            Say "  patched UI/Packages/Core/$($item.Name)"
            $changed++
        }
        $State.core[$item.Name] = @{ sha = (Get-Sha $data); diff = $item.Diff; created = [bool]$item.Base.Created }
    }
    return $changed
}

function Remove-Core([string]$ClientDir, $State, [string]$Name) {
    $target = Join $ClientDir 'UI' 'Packages' 'Core' $Name
    $backup = $target + $BackupSuffix
    $entry = $State.core[$Name]
    $State.core.Remove($Name)
    $made = Test-MadeByUiPlus $entry $backup
    if (-not (Test-Path -LiteralPath $target)) {
        if (Test-Path -LiteralPath $backup) { Remove-Item -LiteralPath $backup }
        return
    }
    $data = [IO.File]::ReadAllBytes($target)
    if ((Get-Sha $data) -eq $entry.sha) {
        if ($made) {
            Remove-Item -LiteralPath $target
            if (Test-Path -LiteralPath $backup) { Remove-Item -LiteralPath $backup }
            Say "  removed UI/Packages/Core/$Name"
        } elseif (Test-Path -LiteralPath $backup) {
            [IO.File]::WriteAllBytes($target, [IO.File]::ReadAllBytes($backup))
            Remove-Item -LiteralPath $backup
            Say "  put back the client's UI/Packages/Core/$Name"
        }
        return
    }
    $file = ConvertFrom-FileBytes $data
    try {
        $base = Invoke-Patch $file.Text $entry.diff $true
        if ($made -and [string]::IsNullOrEmpty($base)) {
            Remove-Item -LiteralPath $target
            Say "  removed UI/Packages/Core/$Name"
        } else {
            [IO.File]::WriteAllBytes($target, (ConvertTo-FileBytes $base $file.Crlf $file.Bom))
            Say "  took UI+'s changes out of UI/Packages/Core/$Name (it changed since UI+ installed it)"
        }
    } catch {
        Say "  left UI/Packages/Core/${Name}: it changed since UI+ installed it and has none of UI+'s changes left"
    }
    if (Test-Path -LiteralPath $backup) { Remove-Item -LiteralPath $backup }
}

# ---- packages: forked from the client's bundled ones -----------------------------------------------------------------

# {relative path: bytes} of a UI+ package: the bundled package it names, patched, plus UI+'s own files.
function Get-PackageFiles([string]$ClientDir, $Source) {
    $files = @{}
    $stockFile = Join $Source.FullName $StockName
    $stock = $null
    if (Test-Path -LiteralPath $stockFile) { $stock = ([IO.File]::ReadAllText($stockFile)).Trim() }
    if ($stock) {
        $stockDir = Join $ClientDir 'UI' 'Packages' $stock
        if (-not (Test-Path -LiteralPath $stockDir -PathType Container)) {
            throw "packages/$($Source.Name): the client has no bundled package $stock"
        }
        $stockFiles = Get-FilesOf $stockDir
        foreach ($rel in @($stockFiles.Keys)) { $files[$rel] = [IO.File]::ReadAllBytes($stockFiles[$rel]) }
    }
    $own = Get-FilesOf $Source.FullName
    foreach ($rel in @($own.Keys | Sort-Object)) {
        if ($rel -eq $StockName) { continue }
        if ($stock -and $rel.EndsWith('.diff', [StringComparison]::Ordinal)) {
            $target = $rel.Substring(0, $rel.Length - '.diff'.Length)
            if (-not $files.ContainsKey($target)) { throw "packages/$($Source.Name): $stock has no $target" }
            $file = ConvertFrom-FileBytes $files[$target]
            $diff = [IO.File]::ReadAllText($own[$rel], $Utf8)
            try {
                $files[$target] = ConvertTo-FileBytes (Invoke-Patch $file.Text $diff) $file.Crlf $file.Bom
            } catch {
                throw "UI/Packages/$stock/${target}: $($_.Exception.Message). The client's file is not the one this version of UI+ was made for (client $MadeFor)."
            }
        } else {
            $files[$rel] = [IO.File]::ReadAllBytes($own[$rel])
        }
    }
    return , $files
}

function Get-PackageId($Files) {
    if (-not $Files.ContainsKey('package.xml')) { return $null }
    $match = [regex]::Match($Utf8.GetString($Files['package.xml']), '<Package\b[^>]*\bid="([^"]+)"')
    if ($match.Success) { return $match.Groups[1].Value }
    return $null
}

# Other package folders with the same id: the client refuses every package of a duplicated id.
function Assert-NoClash([string]$ClientDir, [string]$Name, $Files) {
    $id = Get-PackageId $Files
    if (-not $id) { return }
    $folder = Join (Get-PackageDir) ($Prefix + $Name)
    $others = @()
    foreach ($root in @((Get-PackageDir), (Join $ClientDir 'UI' 'Addons'))) {
        if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
        foreach ($dir in @(Get-ChildItem -LiteralPath $root -Directory -Force)) {
            $manifest = Join $dir.FullName 'package.xml'
            if ($dir.FullName.TrimEnd('\', '/') -ne $folder -and (Test-Path -LiteralPath $manifest -PathType Leaf) -and
                (Get-PackageId @{ 'package.xml' = [IO.File]::ReadAllBytes($manifest) }) -ceq $id) {
                $others += $dir.FullName
            }
        }
    }
    if ($others.Count -gt 0) {
        throw "packages/${Name}: another folder has the package id $id, so the client would refuse both: $($others -join ', '). Remove it (an older copy of UI+?) and run this again."
    }
}

function Write-Package([string]$ClientDir, $State, [string]$Name, $Files) {
    $folder = Join (Get-PackageDir) ($Prefix + $Name)
    $changed = 0
    $same = $false
    if (Test-Path -LiteralPath $folder -PathType Container) {
        $current = Get-FilesOf $folder
        if ($current.Count -eq $Files.Count) {
            $same = $true
            foreach ($rel in @($Files.Keys)) {
                if (-not $current.ContainsKey($rel) -or
                    (Get-Sha ([IO.File]::ReadAllBytes($current[$rel]))) -ne (Get-Sha $Files[$rel])) { $same = $false; break }
            }
        }
    }
    if (-not $same) {
        $staging = $folder + '.new'
        if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
        foreach ($rel in @($Files.Keys)) {
            $path = Join $staging $rel.Replace('/', [string][IO.Path]::DirectorySeparatorChar)
            [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path))
            [IO.File]::WriteAllBytes($path, $Files[$rel])
        }
        if (Test-Path -LiteralPath $folder) { Remove-Item -LiteralPath $folder -Recurse -Force }
        Move-Item -LiteralPath $staging -Destination $folder
        Say "  installed the $Name window as $folder"
        $changed = 1
    }
    $State.packages[$Name] = @{ folder = ($Prefix + $Name); id = (Get-PackageId $Files) }
    return $changed
}

function Remove-Package($State, [string]$Name) {
    $folder = Join (Get-PackageDir) $State.packages[$Name].folder
    $State.packages.Remove($Name)
    if (Test-Path -LiteralPath $folder -PathType Container) {
        Remove-Item -LiteralPath $folder -Recurse -Force
        Say "  removed $folder"
    }
}

# ---- commands --------------------------------------------------------------------------------------------------------

# ---- settings: one file in Core, read by its Lua ---------------------------------------------------------------------

# The question before installing: how long the pointer rests on a button before its tooltip shows, in milliseconds.
# Only asked when someone is there to answer; otherwise the last answer stays.
function Read-TooltipDelay($State) {
    $current = $State.tooltip_delay
    if ([Console]::IsInputRedirected) { return $current }
    Say 'Spiritech shows a tooltip the moment the pointer touches a button; the original client waited until the'
    Say 'pointer had rested there for about a second. UI+ makes them wait (not yet the item tooltips in the'
    Say 'inventory, bags, bank and Wear window, which the client draws itself).'
    $shown = ($current / 1000).ToString([Globalization.CultureInfo]::InvariantCulture)
    while ($true) {
        $answer = (Read-Host "Seconds before a tooltip shows, 0 for at once [$shown]").Trim()
        if (-not $answer) { Say; return $current }
        $seconds = 0.0
        $number = [double]::TryParse($answer.Replace(',', '.'), [Globalization.NumberStyles]::Float,
                                     [Globalization.CultureInfo]::InvariantCulture, [ref]$seconds)
        if ($number -and $seconds -ge 0 -and $seconds -le 5) {
            Say
            return [int][Math]::Round($seconds * 1000)
        }
        Say 'A number of seconds from 0 to 5, please.'
    }
}

# ui_plus_settings.xml, the same bytes install.py writes. Lua can read a view's size but not its text, so each
# setting is a view's width.
function Get-SettingsXml($State) {
    return "<?xml version=`"1.0`" encoding=`"utf-8`"?>`n<root>`n" +
        "  <!-- duramson UI+'s settings, written by its installer: run it again to change them. The width of`n" +
        "       tooltip_delay is how many milliseconds the pointer rests on a view before its tooltip shows`n" +
        "       (tooltip_delay.lua); 0 shows them at once, as Spiritech does. -->`n" +
        "  <View name=`"tooltip_delay`" min_size=`"Point($($State.tooltip_delay),0)`" />`n" +
        "</root>`n"
}

function Write-Settings([string]$ClientDir, $State) {
    $path = Join $ClientDir 'UI' 'Packages' 'Core' $SettingsName
    $data = $Utf8.GetBytes((Get-SettingsXml $State))
    if ((Test-Path -LiteralPath $path) -and (Get-Sha ([IO.File]::ReadAllBytes($path))) -eq (Get-Sha $data)) {
        return 0
    }
    [IO.File]::WriteAllBytes($path, $data)
    Say "  wrote UI/Packages/Core/$SettingsName"
    return 1
}

function Remove-Settings([string]$ClientDir) {
    $path = Join $ClientDir 'UI' 'Packages' 'Core' $SettingsName
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path
        Say "  removed UI/Packages/Core/$SettingsName"
    }
}

function Invoke-Install([string]$ClientDir) {
    $state = Read-State $ClientDir
    $state.tooltip_delay = Read-TooltipDelay $state
    Say "Installing $Title $(Get-Version) into $ClientDir"
    $clientVersion = Get-ClientVersion $ClientDir
    if ($clientVersion -ne $MadeFor) {
        Say "  note: this is client $clientVersion, UI+ was made for $MadeFor. It installs what still fits and stops at anything that doesn't."
    }
    try {   # everything is worked out before anything is written
        $core = Get-CorePlan $ClientDir $state
        $packages = New-Object System.Collections.Generic.List[object]
        foreach ($source in @(Get-RepoPackages)) {
            $packages.Add(@{ Name = $source.Name; Files = (Get-PackageFiles $ClientDir $source) })
        }
        foreach ($package in $packages) { Assert-NoClash $ClientDir $package.Name $package.Files }
    } catch {
        throw "Nothing was changed. $($_.Exception.Message)"
    }
    $changed = (Write-Core $ClientDir $state $core) + (Write-Settings $ClientDir $state)
    foreach ($package in $packages) { $changed += Write-Package $ClientDir $state $package.Name $package.Files }
    $repoCore = @(Get-RepoCore | ForEach-Object { $_.Name.Substring(0, $_.Name.Length - '.diff'.Length) })
    foreach ($name in @($state.core.Keys)) { if ($repoCore -notcontains $name) { Remove-Core $ClientDir $state $name } }
    $repoPackages = @(Get-RepoPackages | ForEach-Object { $_.Name })
    foreach ($name in @($state.packages.Keys)) { if ($repoPackages -notcontains $name) { Remove-Package $state $name } }
    $state.version = Get-Version
    Save-State $ClientDir $state
    if ($changed -eq 0) { Say '  nothing to change: this version is installed' }
    Say
    Say 'Done. It loads at your next character login (log out to character select and back in).'
    Say '- The window frame changes every window by itself. The client''s own screens (Options, login) take it'
    Say '  after a restart of the game.'
    Say '- Pick UI+''s windows in Options > Interface & HUD > UI packages, where they show as'
    Say "  `"External [duramson.<window>] - UI+`": $($repoPackages -join ', ')."
}

function Invoke-Uninstall([string]$ClientDir) {
    $state = Read-State $ClientDir
    if ($state.core.Count -eq 0 -and $state.packages.Count -eq 0) {
        Say 'UI+ is not installed in this client.'
        return
    }
    Say "Removing $Title from $ClientDir"
    foreach ($name in @($state.core.Keys | Sort-Object)) { Remove-Core $ClientDir $state $name }
    foreach ($name in @($state.packages.Keys | Sort-Object)) { Remove-Package $state $name }
    Remove-Settings $ClientDir
    Save-State $ClientDir $state
    Say 'Done. The client''s own UI is back at your next character login (the Options and login screens after a'
    Say 'restart). If you picked UI+''s windows in Options, the client falls back to its own ones.'
    if ($state.fonts.Count -gt 0) {
        Say "$($state.fonts -join ' and ') stay installed: fonts\pixelfont.py uninstall removes them (it needs Python)."
    }
}

function Show-Status([string]$ClientDir) {
    $state = Read-State $ClientDir
    Say "Client: $ClientDir (version $(Get-ClientVersion $ClientDir); UI+ $(Get-Version) was made for $MadeFor)"
    if ($state.core.Count -eq 0 -and $state.packages.Count -eq 0) {
        Say 'UI+ is not installed.'
        return
    }
    Say "UI+ $($state.version) is installed:"
    foreach ($name in @($state.core.Keys | Sort-Object)) {
        $target = Join $ClientDir 'UI' 'Packages' 'Core' $name
        if (-not (Test-Path -LiteralPath $target) -or (Get-Sha ([IO.File]::ReadAllBytes($target))) -ne $state.core[$name].sha) {
            Say "  Core ${name}: changed since it was installed (a client update?): install again"
        } else {
            Say "  Core ${name}: installed"
        }
    }
    foreach ($source in @(Get-RepoPackages)) {
        if ($state.packages.ContainsKey($source.Name)) {
            Say "  window $($source.Name): installed as $(Join (Get-PackageDir) $state.packages[$source.Name].folder)"
        } else {
            Say "  window $($source.Name): not installed yet"
        }
    }
    if ($state.tooltip_delay -gt 0) {
        Say "  tooltips: after $(($state.tooltip_delay / 1000).ToString([Globalization.CultureInfo]::InvariantCulture)) s"
    } else {
        Say '  tooltips: at once, as Spiritech shows them'
    }
}

function Select-Client {
    Say 'The game wasn''t found by itself.'
    if ($env:OS -eq 'Windows_NT') {
        try {
            Add-Type -AssemblyName System.Windows.Forms
            $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
            $dialog.Description = 'Pick the Spiritech client folder (the one with PRK.Client.exe in it)'
            if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
                $found = Resolve-Client $dialog.SelectedPath
                if ($found) { return $found }
                Say 'That''s not a Spiritech client folder.'
            }
        } catch { }
    }
    while ($true) {
        Say 'Drag the client folder (the one with PRK.Client.exe in it) into this window, then press Enter.'
        Say 'Nothing and Enter quits.'
        $given = Read-Host '>'
        if (-not $given) { return $null }
        $found = Resolve-Client $given
        if ($found) { return $found }
        Say 'That''s not a Spiritech client folder.'
    }
}

function Show-Menu($ClientDir) {
    Say "$Title $(Get-Version)"
    Say
    if (-not $ClientDir) { $ClientDir = Select-Client }
    if (-not $ClientDir) { return }
    Say "Game: $ClientDir (version $(Get-ClientVersion $ClientDir))"
    Say
    Say '  1) Install / update'
    Say '  2) Uninstall (back to the client''s own UI)'
    Say '  3) Status'
    Say '  4) Quit'
    $choice = Read-Host 'Pick one [1]'
    if (-not $choice) { $choice = '1' }
    Say
    try {
        switch ($choice) {
            '1' { Invoke-Install $ClientDir }
            '2' { Invoke-Uninstall $ClientDir }
            '3' { Show-Status $ClientDir }
        }
    } catch {
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

try {
    $clientDir = $null
    if ($Client) {
        $clientDir = Resolve-Client $Client
        if (-not $clientDir) { throw "$Client is not a Spiritech client folder (the one with PRK.Client.exe and UI in it)." }
    } else {
        $clientDir = Find-Client
    }
    if ($Install -or $Uninstall -or $Status) {
        if (-not $clientDir) { throw 'The game wasn''t found. Name the client folder with -Client PATH.' }
        if ($Install) { Invoke-Install $clientDir }
        elseif ($Uninstall) { Invoke-Uninstall $clientDir }
        else { Show-Status $clientDir }
    } else {
        Show-Menu $clientDir
    }
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
