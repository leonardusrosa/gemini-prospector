param(
    [switch]$PrintOnly
)

$ErrorActionPreference = 'Stop'

$openDesignRoot = Join-Path $env:LOCALAPPDATA 'Programs\Open Design release-stable-win'
$openDesignExe = Join-Path $openDesignRoot 'Open Design.exe'
$daemonCli = Join-Path $openDesignRoot 'resources\app\prebundled\daemon\daemon-cli.mjs'
$antigravityConfig = Join-Path $HOME '.gemini\antigravity\mcp_config.json'

if (-not (Test-Path -LiteralPath $openDesignExe -PathType Leaf)) {
    throw "OpenDesign executable not found at: $openDesignExe"
}
if (-not (Test-Path -LiteralPath $daemonCli -PathType Leaf)) {
    throw "OpenDesign daemon CLI not found at: $daemonCli"
}

$env:ELECTRON_RUN_AS_NODE = '1'

$installArgs = @($daemonCli, 'mcp', 'install', 'antigravity')
if ($PrintOnly) {
    $installArgs += '--print'
}

Write-Host "OpenDesign executable: $openDesignExe"
Write-Host "Antigravity MCP config: $antigravityConfig"
Write-Host ("Mode: " + $(if ($PrintOnly) { 'print-only' } else { 'install/merge' }))

& $openDesignExe @installArgs
if ($LASTEXITCODE -ne 0) {
    throw "OpenDesign MCP installer exited with code $LASTEXITCODE"
}

if ($PrintOnly) {
    exit 0
}

if (-not (Test-Path -LiteralPath $antigravityConfig -PathType Leaf)) {
    throw "Installer completed but Antigravity MCP config was not found at: $antigravityConfig"
}

$config = Get-Content -LiteralPath $antigravityConfig -Raw | ConvertFrom-Json
if (-not $config.mcpServers) {
    throw 'Antigravity MCP config does not contain mcpServers after installation.'
}

$server = $config.mcpServers.'open-design'
if (-not $server) {
    throw 'OpenDesign installer did not register mcpServers.open-design.'
}

if (-not $server.command -or -not $server.args) {
    throw 'mcpServers.open-design exists but its command/args are incomplete.'
}

Write-Host 'OpenDesign MCP registration verified: mcpServers.open-design'
Write-Host 'Restart/reload the Antigravity Agent session if the MCP tools are not immediately visible.'
