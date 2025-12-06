# Quick Fix Checklist - PowerShell Version
# Run: .\diagnose_env.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🔍 Quick Fix Checklist - Environment Variable Diagnostics" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Check if .env exists
Write-Host "`n1️⃣  Check if .env exists:" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
if (Test-Path ".env") {
    $envFile = Get-Item ".env"
    Write-Host "   ✅ .env file found: $($envFile.FullName)" -ForegroundColor Green
    Write-Host "   Size: $($envFile.Length) bytes" -ForegroundColor Gray
} else {
    Write-Host "   ❌ .env file NOT FOUND" -ForegroundColor Red
    Write-Host "   💡 Create it in the project root directory" -ForegroundColor Yellow
    exit 1
}

# 2. Check .env content (be careful not to expose keys!)
Write-Host "`n2️⃣  Check .env content (first 20 chars only for security):" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
$envContent = Get-Content ".env" -ErrorAction SilentlyContinue
if ($envContent) {
    $neoVars = $envContent | Where-Object { $_ -match "NEO" -and $_ -notmatch "^#" }
    if ($neoVars) {
        Write-Host "   Found NEO-related variables:" -ForegroundColor Green
        foreach ($line in $neoVars) {
            if ($line -match "=") {
                $parts = $line -split "=", 2
                $varName = $parts[0].Trim()
                $varValue = $parts[1].Trim()
                if ($varValue) {
                    $display = if ($varValue.Length -gt 20) { $varValue.Substring(0, 20) + "..." } else { $varValue }
                    Write-Host "   ✅ $varName : $display" -ForegroundColor Green
                } else {
                    Write-Host "   ⚠️  $varName : (empty value)" -ForegroundColor Yellow
                }
            }
        }
    } else {
        Write-Host "   ❌ No NEO-related variables found in .env" -ForegroundColor Red
    }
} else {
    Write-Host "   ❌ Could not read .env file" -ForegroundColor Red
}

# 3. Test loading in Python
Write-Host "`n3️⃣  Test loading in Python:" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
try {
    $pythonTest = python -c "from dotenv import load_dotenv; import os; load_dotenv(); pk = os.getenv('NEO_PRIVATE_KEY'); print('✅ NEO_PRIVATE_KEY loaded:', pk[:10] + '...' if pk else 'NOT SET')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   $pythonTest" -ForegroundColor Green
    } else {
        Write-Host "   ❌ python-dotenv is NOT installed" -ForegroundColor Red
        Write-Host "   💡 Install with: pip install python-dotenv" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Error running Python test: $_" -ForegroundColor Red
}

# 4. Check python-dotenv installation
Write-Host "`n4️⃣  Check python-dotenv installation:" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
try {
    $pipCheck = pip show python-dotenv 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ python-dotenv is installed" -ForegroundColor Green
        $version = ($pipCheck | Select-String "Version:").ToString()
        Write-Host "   $version" -ForegroundColor Gray
    } else {
        Write-Host "   ❌ python-dotenv is NOT installed" -ForegroundColor Red
        Write-Host "   💡 Install with: pip install python-dotenv" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Error checking pip: $_" -ForegroundColor Red
}

# 5. Verify project structure
Write-Host "`n5️⃣  Verify project structure:" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
$root = Get-Location
Write-Host "   Project root: $root" -ForegroundColor Gray
Write-Host "   api_server.py: $(if (Test-Path 'api_server.py') { '✅ Found' } else { '❌ Not found' })" -ForegroundColor $(if (Test-Path 'api_server.py') { 'Green' } else { 'Red' })
Write-Host "   generated_contracts/: $(if (Test-Path 'generated_contracts') { '✅ Found' } else { '❌ Not found' })" -ForegroundColor $(if (Test-Path 'generated_contracts') { 'Green' } else { 'Red' })
Write-Host "   .env: $(if (Test-Path '.env') { '✅ Found' } else { '❌ Not found' })" -ForegroundColor $(if (Test-Path '.env') { 'Green' } else { 'Red' })

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "✅ Diagnostic Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`n💡 If issues found:" -ForegroundColor Yellow
Write-Host "   1. Create .env file in project root if missing" -ForegroundColor Gray
Write-Host "   2. Install python-dotenv: pip install python-dotenv" -ForegroundColor Gray
Write-Host "   3. Verify NEO_PRIVATE_KEY is set in .env" -ForegroundColor Gray
Write-Host "   4. Restart backend server after changing .env" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan

