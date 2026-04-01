
import osmnx as ox
import threading
import tkinter as tk
from tkinter import ttk
import tkintermapview
from Graph import Graph
from Algorithm import *
import time

g =  Graph()
g.load_from_json(r"C:\Users\phank\PycharmProjects\INTRO_AI_IT3160_20252\res\mrt_graph.json")

class App:
    def __init__(self, root):
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
        self.left_frame = tk.Frame(self.root, width=300, bg="lightgray")
        self.left_frame.pack(side="left", fill="y")

        tk.Label(
            self.left_frame,
            text="Chọn thuật toán",
            bg="lightgray",
            font=("Arial", 14)
        ).pack(pady=10)

        self.algo_var = tk.StringVar()
        self.algo_box = ttk.Combobox(
            self.left_frame,
            textvariable=self.algo_var,
            values=["BFS", "DFS", "Dijkstra", "A*"]
        )
        self.algo_box.pack(pady=10)
        self.algo_box.current(0)

        tk.Button(
            self.left_frame,
            text="Run",
            command=self.run_algorithm
        ).pack(pady=20)

        # MAP (RIGHT)
        self.map_widget = tkintermapview.TkinterMapView(self.root)
        self.map_widget.pack(side="right", fill="both", expand=True)

        # Set Singapore
        self.map_widget.set_position(1.3521, 103.8198)
        self.map_widget.set_zoom(11)

        # Bind click
        self.map_widget.add_left_click_map_command(self.on_map_click)
        self.stats_frame = tk.LabelFrame(
            self.left_frame,
            text="Kết quả",
            bg="lightgray",
            font=("Arial", 12, "bold"),
            pady=10
        )
        self.stats_frame.pack(pady=20, fill="x", padx=10)

        self.distance_label = tk.Label(self.stats_frame, text="Khoảng cách: --", bg="lightgray", anchor="w")
        self.distance_label.pack(fill="x", padx=5)

        self.nodes_label = tk.Label(self.stats_frame, text="Số nút đã duyệt: --", bg="lightgray", anchor="w")
        self.nodes_label.pack(fill="x", padx=5)

        self.time_label = tk.Label(self.stats_frame, text="Thời gian tìm kiếm: --", bg="lightgray", anchor="w")
        self.time_label.pack(fill="x", padx=5)
    # ===== EVENT: CLICK =====
    def on_map_click(self, coords):
        lat, lon = coords
        if not (1.13 <= lat <= 1.47 and 103.59 <= lon <= 104.05):
            print("Ngoài phạm vi Singapore!")
            # Bạn có thể dùng messagebox để hiện thông báo lỗi lên màn hình
            tk.messagebox.showwarning("Lỗi", "Vui lòng chọn vị trí trong phạm vi Singapore!")
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

    # ===== RESET =====
    def reset_map(self, lat, lon):
        self.map_widget.delete_all_marker()
        self.map_widget.delete_all_path()
        self.start_marker = self.map_widget.set_marker(lat, lon, text="Start")
        self.start_pos = (lat, lon)

        self.end_marker = None
        self.end_pos = None

        print("Reset → Start:", self.start_pos)
    def run_algorithm(self):
        if not self.start_pos or not self.end_pos:
            print("Chưa chọn đủ điểm!")
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
            pass
        elif selected_algo == "A*":
            pass
        else:
            algo = BFS() # Mặc định nếu có lỗi

        # 2. Bắt đầu đo thời gian
        start_time = time.perf_counter()

        # 3. Chạy thuật toán đã chọn
        # Đảm bảo các class BFS, DFS, Dijkstra, AStar đều trả về (nodes, dist, path)
        total_nodes, distance, path = algo.run("Start", "Dest", g)

        # 4. Kết thúc đo thời gian
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000

        # 5. Cập nhật UI
        if path:
            self.draw_path(path)
            # Làm tròn số cho đẹp giao diện
            self.distance_label.configure(text=f"Khoảng cách: {distance:.2f} km")
            self.nodes_label.configure(text=f"Số nút đã duyệt: {total_nodes}")
            self.time_label.configure(text=f"Thời gian tìm kiếm: {execution_time:.3f} ms")
        else:
            self.distance_label.configure(text="Khoảng cách: Không tìm thấy!")
            self.nodes_label.configure(text="Số nút đã duyệt: 0")
            self.time_label.configure(text="Thời gian: -- ms")


    # ===== DEMO PATH =====
    def fake_path(self):
        # demo: đường thẳng giữa 2 điểm
        return [self.start_pos, self.end_pos]

    def draw_path(self, path):
        # 1. Xóa đường đi cũ
        self.map_widget.delete_all_path()

        if not path:
            return

        path_coords = []

        for node_id in path:
            if node_id in g.nodes:
                coords = g.nodes[node_id]
                path_coords.append(coords)

                # 2. Vẽ "dấu chấm" cho các trạm trung gian
                if node_id not in ["Start", "Dest"]:
                    self.map_widget.set_marker(
                        coords[0],
                        coords[1],
                        text="",
                        # Để tạo dấu chấm nhỏ, ta dùng kích thước vòng tròn (radius)
                        # Thay vì icon_size, ta dùng các tham số sau:
                        marker_color_circle="white",
                        marker_color_outside="#e67e22",
                        # Nếu muốn chấm nhỏ hơn nữa, bạn có thể thử thêm tham số font
                        # hoặc để mặc định vì không có text nó sẽ chỉ hiện vòng tròn màu.
                    )
            else:
                print(f"Cảnh báo: Không tìm thấy tọa độ cho {node_id}")

        # 3. Vẽ đường nối
        if len(path_coords) > 1:
            self.map_widget.set_path(
                path_coords,
                color="#3498db",
                width=2
            )


# ===== MAIN =====
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
