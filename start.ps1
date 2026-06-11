Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "Launching app (PySide6)..." -ForegroundColor Green
python run_pyside6.py