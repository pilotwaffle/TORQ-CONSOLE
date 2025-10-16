# PowerShell Integration Script for Final 3 Tools
# Integrates Terminal Commands, MCP Client, and Multi-Tool Composition into Prince Flowers

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "TORQ Console - Final Tools Integration" -ForegroundColor Cyan
Write-Host "Adding Terminal Commands, MCP Client, Multi-Tool Composition" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$filePath = "torq_console\agents\torq_prince_flowers.py"
$backupPath = "torq_console\agents\torq_prince_flowers.py.backup"

# Check if file exists
if (-not (Test-Path $filePath)) {
    Write-Host "ERROR: File not found: $filePath" -ForegroundColor Red
    exit 1
}

# Create backup
Write-Host "Creating backup..." -ForegroundColor Yellow
Copy-Item $filePath $backupPath -Force
Write-Host "Backup created: $backupPath" -ForegroundColor Green
Write-Host ""

# Read the file
Write-Host "Reading file..." -ForegroundColor Yellow
$content = Get-Content $filePath -Raw -Encoding UTF8

# Check if already integrated
if ($content -match "TERMINAL_COMMANDS_AVAILABLE") {
    Write-Host "WARNING: Tools already integrated!" -ForegroundColor Yellow
    Write-Host "File appears to already have the integration." -ForegroundColor Yellow
    $response = Read-Host "Do you want to proceed anyway? (yes/no)"
    if ($response -ne "yes") {
        Write-Host "Aborting." -ForegroundColor Red
        exit 0
    }
}

# Step 1: Add imports
Write-Host "Step 1: Adding imports..." -ForegroundColor Yellow

$importMarker = 'logging.warning("Browser Automation Tool not available")


class ReasoningMode(Enum):'

$newImports = @'
logging.warning("Browser Automation Tool not available")

# Terminal Commands Tool - Phase 1.8
try:
    from .tools.terminal_commands_tool import create_terminal_commands_tool
    TERMINAL_COMMANDS_AVAILABLE = True
except ImportError:
    TERMINAL_COMMANDS_AVAILABLE = False
    logging.warning("Terminal Commands Tool not available")

# MCP Client Tool - Phase 1.9
try:
    from .tools.mcp_client_tool import create_mcp_client_tool
    MCP_CLIENT_AVAILABLE = True
except ImportError:
    MCP_CLIENT_AVAILABLE = False
    logging.warning("MCP Client Tool not available")

# Multi-Tool Composition Tool - Phase 1.10
try:
    from .tools.multi_tool_composition_tool import create_multi_tool_composition_tool
    MULTI_TOOL_COMPOSITION_AVAILABLE = True
except ImportError:
    MULTI_TOOL_COMPOSITION_AVAILABLE = False
    logging.warning("Multi-Tool Composition Tool not available")


class ReasoningMode(Enum):
'@

if ($content -match [regex]::Escape($importMarker)) {
    $content = $content -replace [regex]::Escape($importMarker), $newImports
    Write-Host "  Imports added successfully" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Could not find import marker" -ForegroundColor Red
    exit 1
}

# Step 2: Add registry entries
Write-Host "Step 2: Adding registry entries..." -ForegroundColor Yellow

$browserEntry = @'
            'browser_automation': {
                'name': 'Browser Automation',
                'description': 'Automate web browser interactions using Playwright',
                'cost': 0.4,
                'success_rate': 0.85,
                'avg_time': 2.5,
                'dependencies': [],
                'composable': True,
                'requires_approval': False
            },
'@

$newEntries = @'
            'browser_automation': {
                'name': 'Browser Automation',
                'description': 'Automate web browser interactions using Playwright',
                'cost': 0.4,
                'success_rate': 0.85,
                'avg_time': 2.5,
                'dependencies': [],
                'composable': True,
                'requires_approval': False
            },
            'terminal_commands': {
                'name': 'Terminal Commands',
                'description': 'Execute whitelisted terminal commands with security controls',
                'cost': 0.2,
                'success_rate': 0.95,
                'avg_time': 1.0,
                'dependencies': [],
                'composable': True,
                'requires_approval': True,
                'security_level': 'high'
            },
            'mcp_client': {
                'name': 'MCP Client Integration',
                'description': 'Connect to MCP servers and invoke their tools and resources',
                'cost': 0.3,
                'success_rate': 0.90,
                'avg_time': 2.0,
                'dependencies': [],
                'composable': True,
                'requires_approval': False
            },
            'multi_tool_composition': {
                'name': 'Multi-Tool Composition',
                'description': 'Orchestrate complex workflows with multiple tools',
                'cost': 0.4,
                'success_rate': 0.92,
                'avg_time': 3.0,
                'dependencies': [],
                'composable': False,
                'requires_approval': False,
                'advanced': True
            },
'@

if ($content -match [regex]::Escape($browserEntry)) {
    $content = $content -replace [regex]::Escape($browserEntry), $newEntries
    Write-Host "  Registry entries added successfully" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Could not find browser_automation entry" -ForegroundColor Red
    exit 1
}

# Write the file
Write-Host "Step 3: Writing modified file..." -ForegroundColor Yellow
$content | Set-Content $filePath -Encoding UTF8 -NoNewline
Write-Host "  File written successfully" -ForegroundColor Green

# Verify file size
$newSize = (Get-Item $filePath).length
Write-Host "  New file size: $newSize bytes" -ForegroundColor Cyan

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Integration Phase 1 & 2 Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Steps completed:" -ForegroundColor Green
Write-Host "1. Imports added for 3 new tools" -ForegroundColor White
Write-Host "2. Registry entries added to available_tools" -ForegroundColor White
Write-Host ""
Write-Host "Next steps (manual):" -ForegroundColor Yellow
Write-Host "3. Add execute methods (_execute_terminal_commands, etc.)" -ForegroundColor White
Write-Host "4. Add routing logic in _execute_direct_reasoning" -ForegroundColor White
Write-Host ""
Write-Host "See 'add_final_tools_patch.txt' for detailed instructions" -ForegroundColor Cyan
Write-Host ""
Write-Host "To verify integration, run:" -ForegroundColor Cyan
Write-Host '  python -c "from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers; prince = TORQPrinceFlowers(); print(len(prince.available_tools))"' -ForegroundColor White
