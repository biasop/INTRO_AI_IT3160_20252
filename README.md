# Singapore MRT Path Finding

## 1. Giới thiệu

Đây là ứng dụng Python hỗ trợ tìm đường trên mạng lưới MRT/LRT tại Singapore thông qua giao diện bản đồ.

Người dùng có thể:

- chọn điểm bắt đầu và điểm kết thúc trực tiếp trên bản đồ,
- chọn thuật toán tìm đường,
- xem kết quả về quãng đường, số nút đã duyệt và thời gian chạy,
- đánh dấu các đoạn đường ray bị hỏng trong chế độ quản trị.

## 2. Chức năng chính

### Chế độ người dùng

- Chọn điểm `Start` và `End` trên bản đồ
- Chạy các thuật toán tìm đường
- Hiển thị đường đi trực quan trên bản đồ
- Hiển thị thống kê kết quả tìm đường

### Chế độ quản trị

- Hiển thị toàn bộ mạng lưới đường ray
- Chọn đoạn ray bị hỏng
- Theo dõi danh sách các đoạn ray đang bị đánh dấu hỏng

### Các thuật toán hiện có

- BFS
- DFS
- Dijkstra
- A*
- Bellman-Ford
- UCS

## 3. Cấu trúc thư mục

```text
INTRO_AI_IT3160_20252/
|- res/
|  |- mrt_graph.pkl
|  |- export.osm
|- src/
|  |- app.py
|  |- Graph.py
|  |- Algorithm.py
|  |- build_data.py
|- requirements.txt
|- run.bat
|- README.md
```

## 4. Mô tả các file chính

- [src/app.py](src/app.py)  
  File giao diện chính, xử lý chế độ `User` và `Admin`, hiển thị bản đồ và kết quả.

- [src/Graph.py](src/Graph.py)  
  Quản lý dữ liệu đồ thị gồm node, cạnh, đường đi chi tiết, các đoạn ray hỏng và các hàm load/save dữ liệu.

- [src/Algorithm.py](src/Algorithm.py)  
  Chứa các thuật toán tìm đường.

- [src/build_data.py](src/build_data.py)  
  Dùng để xử lý dữ liệu nguồn và xây dựng đồ thị.


## 5. Yêu cầu môi trường

- Python 3.12 hoặc Python 3.13
- Hệ điều hành Windows được hỗ trợ tốt nhất do project có sẵn `run.bat`
- Kết nối internet nếu cần gọi OSRM để tạo đường đi bộ từ điểm chọn đến ga gần nhất

## 6. Cài đặt

### Bước 1: Tạo môi trường ảo

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Bước 2: Cài thư viện

```powershell
pip install -r requirements.txt
```

## 7. Chạy chương trình

### Cách 1: Chạy bằng file batch

```powershell
run.bat
```

### Cách 2: Chạy trực tiếp bằng Python

```powershell
.venv\Scripts\activate
python src/app.py
```

## 8. Hướng dẫn sử dụng

### 8.1. Chế độ User

1. Mở ứng dụng.
2. Chọn `Chế độ User`.
3. Click lên bản đồ để chọn điểm bắt đầu.
4. Click lần hai để chọn điểm kết thúc.
5. Chọn thuật toán trong combobox.
6. Nhấn `Tìm đường`.
7. Xem kết quả hiển thị ở khung bên trái.

### 8.2. Chế độ Admin

1. Chọn `Chế độ Admin`.
2. Nhấn `Hiện mạng lưới Hover`.
3. Click vào một đoạn ray trên bản đồ để đánh dấu hỏng hoặc mở lại.
4. Xem danh sách các đoạn ray hỏng ở bảng bên trái.

## 9. Các thư viện sử dụng

Project hiện đang dùng các thư viện sau:

- `scipy`
- `osmnx`
- `tkintermapview`
- `customtkinter`
- `networkx`
- `requests`


## 10. Dữ liệu sử dụng

Project hiện dùng các file dữ liệu chính trong thư mục `res`:

- `mrt_graph.pkl`: dữ liệu đồ thị đã được lưu sẵn để tải nhanh
- `export.osm`: dữ liệu nguồn OSM

