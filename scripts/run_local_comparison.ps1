param(
    [string]$Model = "qwen3:8b",
    [string]$BaseUrl = "http://localhost:11434/v1",
    [string]$ApiKey = "ollama",
    [ValidateSet("prompt", "workflow")]
    [string]$Mode = "prompt",
    [int]$MaxTokens = 160,
    [int]$Timeout = 180,
    [int]$Runs = 1,
    [switch]$SkipVerifier
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Model: $Model"
Write-Host "Base URL: $BaseUrl"
Write-Host "Mode: $Mode"

if ($Mode -eq "workflow") {
    $argsList = @(
        "agent\compare_agent_workflows.py",
        "--base-url", $BaseUrl,
        "--api-key", $ApiKey,
        "--model", $Model,
        "--max-tokens", $MaxTokens,
        "--timeout", $Timeout
    )
    if ($SkipVerifier) {
        $argsList += "--skip-verifier"
    }
    python @argsList
} else {
    python agent\compare_token_usage.py --base-url $BaseUrl --api-key $ApiKey --model $Model --runs $Runs
}
