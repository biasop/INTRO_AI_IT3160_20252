@echo off
:: Ép CMD dùng UTF-8 để không bị lỗi ký tự tia sét
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
setlocal

cd /d "%~dp0"
echo [INFO] Dang o thu muc: %CD%

:: Kích hoạt môi trường ảo
if exist ".venv\Scripts\activate" (
    echo [INFO] Kich hoat moi truong ao .venv...
    call ".venv\Scripts\activate"
) else (
    echo [LỖI] Khong tim thay thu muc .venv! Vui long tao moi truong ao truoc.
    pause
    exit /b
)

:: =================================================================
:: TỰ ĐỘNG TÌM ĐƯỜNG DẪN TCL/TK (Giải quyết triệt để lỗi init.tcl)
:: =================================================================
echo [INFO] Dang thiet lap duong dan Tcl/Tk tu dong...
FOR /F "tokens=*" %%F IN ('python -c "import sys, os; print(os.path.join(sys.base_prefix, 'tcl', 'tcl8.6'))"') DO SET TCL_LIBRARY=%%F
FOR /F "tokens=*" %%F IN ('python -c "import sys, os; print(os.path.join(sys.base_prefix, 'tcl', 'tk8.6'))"') DO SET TK_LIBRARY=%%F

echo [INFO] Dang kiem tra thu vien...
python -m pip install -r requirements.txt

cls
echo [INFO] Dang chay ung dung...
python src/app.py

pause