# Windows PowerShell 5.1+ or PowerShell 7. All options go to the shared patcher.
# Usage: .\patch-cfw.ps1 "C:\Downloads\fwdc243b.bin" [-o "C:\Output\fwdc243b.bin"]
$ErrorActionPreference = 'Stop'
$pythonCommand = $null
$pythonPrefix = @()
if ($env:PYTHON) {
    $pythonCommand = $env:PYTHON
} else {
    foreach ($candidate in @('python', 'python3', 'py')) {
        $found = Get-Command $candidate -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $pythonCommand = $found.Source
            if ($candidate -eq 'py') { $pythonPrefix = @('-3') }
            break
        }
    }
}
if (-not $pythonCommand) {
    [Console]::Error.WriteLine('Python 3 is required. Install Python or set PYTHON to its executable path.')
    exit 2
}
try {
    & $pythonCommand @pythonPrefix (Join-Path $PSScriptRoot 'native-cfw/patch.py') @args
    exit $LASTEXITCODE
} catch {
    [Console]::Error.WriteLine('CFW patcher: ' + $_.Exception.Message)
    exit 2
}
