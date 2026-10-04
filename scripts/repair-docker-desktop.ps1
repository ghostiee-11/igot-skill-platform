param([ValidateRange(15, 600)][int]$StartupTimeoutSeconds = 120)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'This recovery command is for Windows Docker Desktop only' }
$desktopPath = Join-Path $env:ProgramFiles 'Docker/Docker/Docker Desktop.exe'
if (-not (Test-Path -LiteralPath $desktopPath -PathType Leaf)) { throw 'Docker Desktop executable not found' }
$dockerCommandPath = (Get-Command docker -ErrorAction Stop).Source

function Test-LocalDockerEngine {
    $probeInfo = New-Object System.Diagnostics.ProcessStartInfo
    $probeInfo.FileName = $dockerCommandPath
    $probeInfo.Arguments = 'info --format {{.ServerVersion}}'
    $probeInfo.UseShellExecute = $false
    $probeInfo.CreateNoWindow = $true
    $probeInfo.RedirectStandardOutput = $true
    $probeInfo.RedirectStandardError = $true
    $probeProcess = New-Object System.Diagnostics.Process
    $probeProcess.StartInfo = $probeInfo
    try {
        [void]$probeProcess.Start()
        if (-not $probeProcess.WaitForExit(5000)) {
            # Stop only this command's own timed-out read-only probe.
            $probeProcess.Kill()
            return $false
        }
        return $probeProcess.ExitCode -eq 0
    } finally {
        $probeProcess.Dispose()
    }
}

Write-Host 'Stopping Docker Desktop before preserving its temporary runtime sockets'
docker desktop stop --force --timeout 20
if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop did not stop; no runtime directories were changed' }
$stopDeadline = [DateTime]::UtcNow.AddSeconds(15)
do {
    $desktopProcesses = @(Get-Process -Name 'Docker Desktop','com.docker.backend' -ErrorAction SilentlyContinue)
    if ($desktopProcesses.Count -eq 0) { break }
    Start-Sleep -Milliseconds 250
} while ([DateTime]::UtcNow -lt $stopDeadline)
if ($desktopProcesses.Count -gt 0) { throw 'Docker processes remain active; no runtime directories were changed' }

$backupSuffix = 'stale-igot-' + [DateTime]::UtcNow.ToString('yyyyMMddHHmmssfff')
$localAppDataPath = [System.IO.Path]::GetFullPath($env:LOCALAPPDATA)
$runtimeFolders = @(
    @{ Parent = (Join-Path $localAppDataPath 'Docker'); Name = 'run' },
    @{ Parent = $localAppDataPath; Name = 'docker-secrets-engine' }
)
foreach ($runtimeFolder in $runtimeFolders) {
    $expectedParentPath = [System.IO.Path]::GetFullPath($runtimeFolder.Parent)
    $runtimePath = [System.IO.Path]::GetFullPath((Join-Path $expectedParentPath $runtimeFolder.Name))
    if ([System.IO.Path]::GetDirectoryName($runtimePath) -ne $expectedParentPath) {
        throw 'Unexpected Docker runtime directory; recovery stopped'
    }
    if (Test-Path -LiteralPath $runtimePath -PathType Container) {
        # Preserve the entire small runtime directory because Windows can reject
        # access to the individual AF_UNIX socket. Never touch Docker/wsl or volumes.
        Rename-Item -LiteralPath $runtimePath -NewName ($runtimeFolder.Name + '.' + $backupSuffix)
        Write-Host "Preserved $runtimePath"
    }
}
Start-Process -FilePath $desktopPath -WindowStyle Hidden
$startupDeadline = [DateTime]::UtcNow.AddSeconds($StartupTimeoutSeconds)
do {
    if (Test-LocalDockerEngine) {
        Write-Host 'Docker engine is available. Start the platform with scripts/start-local.ps1 -SkipBuild.'
        return
    }
    Start-Sleep -Seconds 1
} while ([DateTime]::UtcNow -lt $startupDeadline)
throw 'Docker engine did not become available. Preserved runtime directories remain recoverable; inspect Desktop logs before retrying. No image, volume or WSL data was deleted.'
