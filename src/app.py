import osmnx as ox
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import tkintermapview
from Graph import Graph
from Algorithm import *
import time
from pathlib import Path
import customtkinter as ctk

# Lấy đường dẫn của thư mục chứa file code hiện tại (thư mục src)
current_dir = Path(__file__).parent

# Chỉ cần trỏ vào file pkl
pkl_path = current_dir.parent / "res" / "mrt_graph.pkl"

g = Graph()
g.load_from_pickle(pkl_path) # Gọi hàm load siêu tốc

class App(ctk.CTk):
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.root.title("Singapore Path Finding")
        self.root.geometry("1000x600")

        # ===== STATE =====
        self.start_marker = None
        self.end_marker = None
        self.start_pos = None
        self.end_pos = None

        # ===== UI =====
        self.setup_ui()

    # ===== UI SETUP =====
    def setup_ui(self):
        # LEFT PANEL
        self.left_frame = ctk.CTkFrame(self.root, width=300, corner_radius=0, fg_color="lightgray")
        self.left_frame.pack(side="left", fill="y")
        self.left_frame.pack_propagate(False)

        # MAP (RIGHT)
        self.map_widget = tkintermapview.TkinterMapView(self.root, corner_radius=0)
        self.map_widget.pack(side="right", fill="both", expand=True)

        # Set Singapore
        self.map_widget.set_position(1.3521, 103.8198)
        self.map_widget.set_zoom(11)

        # Bind click
        self.map_widget.add_left_click_map_command(self.on_map_click)
        
        # Hiển thị menu ban đầu thay vì vào thẳng user
        self.show_initial_menu()

    # ===== HÀM HỖ TRỢ MENU =====
    def clear_left_frame(self):
        """Xóa toàn bộ các widget đang nằm trong khung trái để vẽ menu mới"""
        for widget in self.left_frame.winfo_children():
            widget.destroy()

    def show_initial_menu(self):
        """Menu chọn chế độ ban đầu"""
        self.clear_left_frame()

        ctk.CTkLabel(self.left_frame, text="CHỌN CHẾ ĐỘ", font=("Arial", 20, "bold")).pack(pady=(50, 20))

        ctk.CTkButton(self.left_frame, text="Chế độ Admin", command=self.show_admin_panel, width=200).pack(pady=10)
        ctk.CTkButton(self.left_frame, text="Chế độ User", command=self.show_user_panel, width=200).pack(pady=10)

    def show_admin_panel(self):
        """Giao diện dành cho Admin (Đang chờ phát triển)"""
        self.clear_left_frame()

        ctk.CTkLabel(self.left_frame, text="CHẾ ĐỘ ADMIN", font=("Arial", 18, "bold"), text_color="#dc3545").pack(pady=(20, 10))
        
        ctk.CTkButton(self.left_frame, text="Thêm ga tàu", width=200).pack(pady=10)
        ctk.CTkButton(self.left_frame, text="Chặn đường ray", width=200).pack(pady=10)

        # Nút Quay lại
        ctk.CTkButton(self.left_frame, text="← Quay lại", fg_color="gray", hover_color="#555555", width=200, command=self.show_initial_menu).pack(side="bottom", pady=20)

    def show_user_panel(self):
        """Giao diện tìm đường (User)"""
        self.clear_left_frame()

        # Tiêu đề
        ctk.CTkLabel(self.left_frame, text="CHẾ ĐỘ USER", font=("Arial", 18, "bold"), text_color="#1f6aa5").pack(pady=(20, 10))
        
        ctk.CTkLabel(self.left_frame, text="Chọn thuật toán", font=("Arial", 14)).pack(pady=5)

        # Combobox chọn thuật toán
        self.algo_var = ctk.StringVar(value="BFS")
        self.algo_box = ctk.CTkComboBox(self.left_frame, variable=self.algo_var, values=["BFS", "DFS", "Dijkstra", "A*"], width=200)
        self.algo_box.pack(pady=5)

        # Nút Run 
        ctk.CTkButton(self.left_frame, text="Tìm đường", fg_color="#28a745", hover_color="#218838", width=200, command=self.run_algorithm).pack(pady=(20, 5))

        # Nút Xóa bản đồ (Reset)
        ctk.CTkButton(self.left_frame, text="Xóa bản đồ", fg_color="#dc3545", hover_color="#c82333", width=200, command=self.clear_map).pack(pady=5)

        # Khung Thống kê
        self.stats_frame = ctk.CTkFrame(self.left_frame, corner_radius=10)
        self.stats_frame.pack(pady=20, fill="x", padx=15)

        ctk.CTkLabel(self.stats_frame, text="KẾT QUẢ", font=("Arial", 14, "bold")).pack(pady=(10, 5))

        self.distance_label = ctk.CTkLabel(self.stats_frame, text="Khoảng cách: --", anchor="w")
        self.distance_label.pack(fill="x", padx=10, pady=2)

        self.nodes_label = ctk.CTkLabel(self.stats_frame, text="Số nút đã duyệt: --", anchor="w")
        self.nodes_label.pack(fill="x", padx=10, pady=2)

        self.time_label = ctk.CTkLabel(self.stats_frame, text="Thời gian: --", anchor="w")
        self.time_label.pack(fill="x", padx=10, pady=(2, 10))

        # Nút Quay lại
        ctk.CTkButton(self.left_frame, text="← Quay lại", fg_color="gray", hover_color="#555555", width=200, command=self.show_initial_menu).pack(side="bottom", pady=20)


    # ===== EVENT: CLICK =====
    def on_map_click(self, coords):
        lat, lon = coords
        if not (1.13 <= lat <= 1.47 and 103.59 <= lon <= 104.05):
            print("Ngoài phạm vi Singapore!")
            messagebox.showwarning("Lỗi", "Vui lòng chọn vị trí trong phạm vi Singapore!")
            return
            
        if self.start_marker is None:
            self.start_pos = (lat, lon)
            self.start_marker = self.map_widget.set_marker(lat, lon, text="Start")
            print("Start:", self.start_pos)

        elif self.end_marker is None:
            self.end_pos = (lat, lon)
            self.end_marker = self.map_widget.set_marker(lat, lon, text="End")
            print("End:", self.end_pos)
        else:
            self.reset_map(lat, lon)

    # ===== RESET & XỬ LÝ =====
    def reset_map(self, lat, lon):
        self.map_widget.delete_all_marker()
        self.map_widget.delete_all_path()
        self.start_marker = self.map_widget.set_marker(lat, lon, text="Start")
        self.start_pos = (lat, lon)

        self.end_marker = None
        self.end_pos = None
        
        # Reset lại Label nếu giao diện User đang mở
        if hasattr(self, 'distance_label') and self.distance_label.winfo_exists():
            self.distance_label.configure(text="Khoảng cách: --")
            self.nodes_label.configure(text="Số nút đã duyệt: --")
            self.time_label.configure(text="Thời gian: --")

        print("Reset → Start:", self.start_pos)
        
    def clear_map(self):
        """Hàm dọn dẹp sạch sẽ toàn bộ bản đồ"""
        self.map_widget.delete_all_marker()
        self.map_widget.delete_all_path()
        self.start_marker = None
        self.end_marker = None
        self.start_pos = None
        self.end_pos = None
        
        if hasattr(self, 'distance_label') and self.distance_label.winfo_exists():
            self.distance_label.configure(text="Khoảng cách: --")
            self.nodes_label.configure(text="Số nút đã duyệt: --")
            self.time_label.configure(text="Thời gian: --")

    def run_algorithm(self):
        if not self.start_pos or not self.end_pos:
            print("Chưa chọn đủ điểm!")
            messagebox.showwarning("Thiếu điểm", "Vui lòng click chọn điểm Start và End trên bản đồ trước khi Tìm đường!")
            return

        # Thêm vị trí Start/Dest vào đồ thị
        g.add_chosen_location(self.start_pos, self.end_pos)

        # --- CHỌN THUẬT TOÁN DỰA TRÊN COMBOBOX ---
        selected_algo = self.algo_var.get()

        if selected_algo == "BFS":
            algo = BFS()
        elif selected_algo == "DFS":
            algo = DFS()
        elif selected_algo == "Dijkstra":
            algo = Dijkstra() 
        elif selected_algo == "A*":
            algo = AStar()    
        else:
            algo = BFS() 

        # 2. Bắt đầu đo thời gian
        start_time = time.perf_counter()

        # 3. Chạy thuật toán đã chọn
        total_nodes, distance, path = algo.run("Start", "Dest", g)

        # 4. Kết thúc đo thời gian
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000

        # 5. Cập nhật UI
        if path:
            self.draw_path(path)
            self.distance_label.configure(text=f"Khoảng cách: {distance:.2f} km")
            self.nodes_label.configure(text=f"Số nút đã duyệt: {total_nodes}")
            self.time_label.configure(text=f"Thời gian tìm kiếm: {execution_time:.3f} ms")
        else:
            self.distance_label.configure(text="Khoảng cách: Không tìm thấy!")
            self.nodes_label.configure(text="Số nút đã duyệt: 0")
            self.time_label.configure(text="Thời gian: -- ms")
            messagebox.showinfo("Kết quả", "Không tìm thấy đường đi giữa 2 điểm này trên mạng lưới MRT!")

    def draw_path(self, path):
        # 1. Xóa đường đi cũ
        self.map_widget.delete_all_path()
        if hasattr(self, 'station_markers'):
            for marker in self.station_markers:
                marker.delete()
        self.station_markers = []
        if not path:
            return

        path_coords = []

        for i in range(len(path) - 1):
            u = path[i]
            v = path[i + 1]
            detailed_nodes = g.edge_paths.get((u, v), [u, v]) #nếu ko có thì lấy luôn [u, v] SẼ CẢI TIẾN TRƯỜNG HỢP ĐI BỘ
            
            path_coords = [] #List các toạ độ
            for node_id in detailed_nodes:
                if node_id in g.nodes:
                    path_coords.append(g.nodes[node_id])
            
            if len(path_coords) > 1:
                self.map_widget.set_path(path_coords, color="#3498db", width=4)
            if u not in ["Start", "Dest"]:
                name = g.names.get(u, "Ga Tàu")
                lat, lon = g.nodes[u]
                marker = self.map_widget.set_marker(lat, lon, text=name, marker_color_circle="#e74c3c")
                self.station_markers.append(marker)


# ===== MAIN =====
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()