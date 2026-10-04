param([switch]$SkipBuild)

$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
Push-Location $repoPath
try {
    if (-not (Test-Path -LiteralPath '.env')) {
        Copy-Item -LiteralPath '.env.example' -Destination '.env'
    }
    docker info --format '{{.ServerVersion}}'
    if ($LASTEXITCODE -ne 0) {
        throw 'Start Docker Desktop with Linux containers before running this script. See LOCAL_SETUP.md for socket-error recovery.'
    }
    $composeArgs = @('compose', '--env-file', '.env', '-f', 'infra/compose/docker-compose.yml')
    docker @composeArgs config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Compose configuration validation failed' }
    if (-not $SkipBuild) {
        # Build sequentially to avoid exhausting memory on a 16 GB Windows host.
        Write-Host 'Stopping local services during image builds; database volumes are retained'
        docker @composeArgs stop
        if ($LASTEXITCODE -ne 0) { throw 'Could not stop the stack before rebuilding' }
        $env:COMPOSE_PARALLEL_LIMIT = '1'
        foreach ($service in @('identity', 'learning', 'assessment', 'competency', 'ai', 'content', 'lab-workspace-image', 'lab-target-demo-image', 'labs', 'gateway', 'frontend')) {
            Write-Host "Building $service"
            docker @composeArgs build $service
            if ($LASTEXITCODE -ne 0) { throw "Build failed for $service; existing volumes are preserved" }
        }
    }
    docker @composeArgs up -d --no-build --wait --wait-timeout 240
    if ($LASTEXITCODE -ne 0) { throw 'Startup failed; inspect Compose status and logs before retrying' }
    Write-Host 'Platform ready: http://localhost:3000'
} finally {
    Pop-Location
}
