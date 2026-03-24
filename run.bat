@echo off
setlocal

:: Di chuyển vào thư mục dự án
cd /d "C:\Users\phank\PycharmProjects\Intro_AI_IT3160_20252"

:: Định nghĩa đường dẫn Tcl/Tk hệ thống (Cực kỳ quan trọng)
set TCL_LIBRARY=C:\Users\phank\AppData\Local\Programs\Python\Python313\tcl\tcl8.6
set TK_LIBRARY=C:\Users\phank\AppData\Local\Programs\Python\Python313\tcl\tk8.6

:: Kích hoạt môi trường ảo
call .venv\Scripts\activate
:: Di chuyển vào thư mục dự án (giả sử file .bat nằm ngoài thư mục này)
cd /d "INTRO_AI_IT3160_20252"

:: Kiểm tra nếu môi trường ảo tồn tại thì kích hoạt
if exist .venv\Scripts\activate (
    call .venv\Scripts\activate
) else (
    echo [CANH BAO] Khong tim thay thu muc .venv!
    pause
    exit /b
)

:: Cập nhật thư viện (Dùng python -m pip để tránh lỗi 'not recognized')
echo Dang kiem tra thu vien...
python -m pip install -r requirements.txt

cls

:: CHẠY ỨNG DỤNG (Bắt buộc phải có chữ python ở đầu)
echo Dang chay ung dung...
python src/app.py

:: Giữ cửa sổ mở để xem lỗi nếu có
pause