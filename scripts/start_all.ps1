$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root "env\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) { $python = "python" }

Start-Process -FilePath $python -ArgumentList "-m", "uvicorn", "app.sc01_viajes.main:app", "--port", "8081" -WorkingDirectory $root -WindowStyle Hidden
Start-Process -FilePath $python -ArgumentList "-m", "uvicorn", "app.sc02_reservas.main:app", "--port", "8082" -WorkingDirectory $root -WindowStyle Hidden
Start-Process -FilePath $python -ArgumentList "-m", "uvicorn", "app.sc03_pasajeros.main:app", "--port", "8083" -WorkingDirectory $root -WindowStyle Hidden
Start-Process -FilePath $python -ArgumentList "-m", "uvicorn", "app.sc04_pagos.main:app", "--port", "8084" -WorkingDirectory $root -WindowStyle Hidden
Start-Process -FilePath $python -ArgumentList "-m", "uvicorn", "app.sc05_pasajes.main:app", "--port", "8085" -WorkingDirectory $root -WindowStyle Hidden
Start-Process -FilePath $python -ArgumentList "-m", "uvicorn", "app.sc06_mantenimiento.main:app", "--port", "8086" -WorkingDirectory $root -WindowStyle Hidden
Write-Host "SC-01 a SC-06 iniciados en los puertos 8081 a 8086."
