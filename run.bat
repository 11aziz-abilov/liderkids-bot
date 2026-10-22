@echo off
chcp 65001 > nul
echo ========================================================
echo   LiderKids - Ota-ona paneli Telegram boti
echo ========================================================
echo.

if not exist venv (
    echo [1/3] Virtual muhit yaratilmoqda...
    python -m venv venv
)

echo [2/3] Kutubxonalar tekshirilmoqda...
call .\venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

echo [3/3] Bot ishga tushirilmoqda...
echo.
python main.py
pause
