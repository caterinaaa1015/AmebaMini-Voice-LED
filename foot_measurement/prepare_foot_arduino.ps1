param([switch]$Compile)
$ErrorActionPreference = 'Stop'
$taskRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('ameba_foot10_' + [guid]::NewGuid().ToString('N'))
$taskSketch = Join-Path $taskRoot 'ameba_foot_camera'
New-Item -ItemType Directory -Path $taskSketch -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'firmware\ameba_foot_camera\ameba_foot_camera.ino') -Destination $taskSketch
Write-Output 'Open this sketch in Arduino IDE (select the actual camera sensor):'
Write-Output (Join-Path $taskSketch 'ameba_foot_camera.ino')
if ($Compile) {
    $taskCli = Join-Path $env:LOCALAPPDATA 'Programs\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe'
    if (!(Test-Path -LiteralPath $taskCli)) { throw 'Arduino CLI not found. Use Arduino IDE with the sketch above.' }
    $taskOldLang = $env:LANG
    $taskOldLc = $env:LC_ALL
    $taskOldData = $env:ARDUINO_DIRECTORIES_DATA
    try {
        $env:LANG = 'C'
        $env:LC_ALL = 'C'
        $env:ARDUINO_DIRECTORIES_DATA = Join-Path $env:LOCALAPPDATA 'Arduino15'
        & $taskCli compile --fqbn 'realtek:AmebaPro2:Ameba_AMB82-MINI:04_CameraOption=f37,06_LoadNNModelSource=flash,07_SHOWNNLOGS=Disable' --build-path (Join-Path $taskRoot 'build') $taskSketch
        if ($LASTEXITCODE -ne 0) { throw 'Compilation failed. No board was flashed.' }
        Write-Output 'Compile-only succeeded for JXF37. No board was flashed.'
        Write-Output (Join-Path $taskRoot 'build\flash_ntz.bin')
    } finally {
        $env:LANG = $taskOldLang
        $env:LC_ALL = $taskOldLc
        $env:ARDUINO_DIRECTORIES_DATA = $taskOldData
    }
}
