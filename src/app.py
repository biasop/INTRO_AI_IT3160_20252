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
        self.mode = None
        self.all_paths = {}
        self.selected_path_highlight=None# phuc vu cho admin
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
        self.map_widget.set_zoom(13)

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
        self.map_widget.delete_all_marker()
        self.map_widget.delete_all_path()
        g.remove_chosen_location()
        ctk.CTkLabel(self.left_frame, text="CHỌN CHẾ ĐỘ", font=("Arial", 20, "bold")).pack(pady=(50, 20))

        ctk.CTkButton(self.left_frame, text="Chế độ Admin", command=self.show_admin_panel, width=200).pack(pady=10)
        ctk.CTkButton(self.left_frame, text="Chế độ User", command=self.show_user_panel, width=200).pack(pady=10)


    def show_user_panel(self):
        self.mode= "user"
        """Giao diện tìm đường (User)"""
        self.clear_left_frame()

        # Tiêu đề
        ctk.CTkLabel(self.left_frame, text="CHẾ ĐỘ USER", font=("Arial", 18, "bold"), text_color="#1f6aa5").pack(pady=(20, 10))
        
        ctk.CTkLabel(self.left_frame, text="Chọn thuật toán", font=("Arial", 14)).pack(pady=5)

        # Combobox chọn thuật toán
        self.algo_var = ctk.StringVar(value="BFS")
        self.algo_box = ctk.CTkComboBox(self.left_frame, variable=self.algo_var,
                                        values=["BFS", "DFS", "Dijkstra", "A*","Bellman-Ford","UCS",
                                                "Greedy", "Bidirectional A*", "Bidirectional Dijkstra"],
                                        width=200)
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
        """Hàm điều phối sự kiện click chuột trên bản đồ"""

        zoom_component = [
            self.map_widget.button_zoom_in.canvas_rect,
            self.map_widget.button_zoom_in.canvas_text,
            self.map_widget.button_zoom_out.canvas_rect,
            self.map_widget.button_zoom_out.canvas_text
        ]

        # check xem chuột có chạm vào nút zoom không?
        clicked_items = self.map_widget.canvas.find_withtag("current")
        for item in clicked_items:
            if item in zoom_component:
                # Đang click vào nút Zoom -> Thoát hàm luôn, không vẽ start/end
                return

        lat, lon = coords
        # Kiểm tra phạm vi chung cho cả 2 chế độ
        if not (1.13 <= lat <= 1.47 and 103.59 <= lon <= 104.05):
            messagebox.showwarning("Lỗi", "Vui lòng chọn vị trí trong phạm vi Singapore!")
            return

        # Điều hướng xử lý dựa trên chế độ hiện tại
        if self.mode == "admin":
            self._handle_admin_click(coords)
        elif self.mode == "user":
            self._handle_user_click(coords)
        else:
            print("Chưa chọn chế độ, không xử lý click.")

    def _handle_user_click(self, coords):
        lat, lon = coords
        if self.start_marker is None:
            self.start_pos = (lat, lon)
            self.start_marker = self.map_widget.set_marker(lat, lon, text="Start")
        elif self.end_marker is None:
            self.end_pos = (lat, lon)
            self.end_marker = self.map_widget.set_marker(lat, lon, text="End")
        else:
            self.reset_map(lat, lon)

    # ===== RESET & XỬ LÝ cho User =====
    def reset_map(self, lat, lon):
        self.map_widget.delete_all_marker()
        self.map_widget.delete_all_path()
        self.start_marker = self.map_widget.set_marker(lat, lon, text="Start")
        self.start_pos = (lat, lon)

        self.end_marker = None
        self.end_pos = None
        
        # Reset lại Label nếu giao diện User đang mở
        if self.mode == "user":
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
        g.remove_chosen_location()
        
        if hasattr(self, 'distance_label') and self.distance_label.winfo_exists():
            self.distance_label.configure(text="Khoảng cách: --")
            self.nodes_label.configure(text="Số nút đã duyệt: --")
            self.time_label.configure(text="Thời gian: --")


    def run_algorithm(self):
        """Hàm khởi tạo luồng để không làm treo giao diện"""
        if not self.start_pos or not self.end_pos:
            messagebox.showwarning("Thiếu điểm", "Vui lòng click chọn điểm Start và End trên bản đồ!")
            return

        # Hiển thị trạng thái chờ cho người dùng
        self.time_label.configure(text="Đang tính toán...")

        # Tạo một luồng riêng để chạy thuật toán
        thread = threading.Thread(target=self._run_algorithm_task, daemon=True)
        thread.start()

    def _run_algorithm_task(self):
        """Logic tính toán chạy ngầm"""
        try:
            # 1. Thêm vị trí vào đồ thị
            g.add_chosen_location(self.start_pos, self.end_pos)

            # 2. Khởi tạo thuật toán dựa trên Combobox
            selected_algo = self.algo_var.get()
            algos = {
                "BFS": BFS(), "DFS": DFS(), "Dijkstra": Dijkstra(),
                "A*": AStar(), "Bellman-Ford": BellmanFord(), "UCS": UCS(),
                "Greedy": Greedy(), "Bidirectional A*": BidirectionalAstar(),
                "Bidirectional Dijkstra": BidirectionalDijkstra()
            }
            algo = algos.get(selected_algo, BFS()) #mặc định

            # 3. Đo thời gian và chạy
            start_time = time.perf_counter()
            total_nodes, distance, path = algo.run("Start", "Dest", g)
            end_time = time.perf_counter()

            execution_time = (end_time - start_time) * 1000

            # 4. Gửi kết quả về luồng chính (Main Thread) để cập nhật UI
            self.root.after(0, self._update_ui_after_run, total_nodes, distance, path, execution_time)

        except Exception as e:
            print(f"Lỗi thuật toán: {e}")
            self.root.after(0, lambda: messagebox.showerror("Lỗi", "Đã xảy ra lỗi trong quá trình tìm đường."))

    def _update_ui_after_run(self, total_nodes, distance, path, execution_time):
        """Cập nhật giao diện (Chỉ chạy trên luồng chính)"""
        if path:
            self.draw_path(path)
            self.distance_label.configure(text=f"Khoảng cách: {distance:.2f} km")
            self.nodes_label.configure(text=f"Số nút đã duyệt: {total_nodes}")
            self.time_label.configure(text=f"Thời gian tìm kiếm: {execution_time:.3f} ms")
        else:
            self.map_widget.delete_all_path()
            self.distance_label.configure(text="Khoảng cách: Không tìm thấy!")
            self.nodes_label.configure(text=f"Số nút đã duyệt: {total_nodes}")
            self.time_label.configure(text="Thời gian: -- ms")
            messagebox.showinfo("Kết quả", "Không tìm thấy đường đi giữa 2 điểm này trên mạng lưới MRT!")
    def draw_path(self, path):
        # 1. Dọn dẹp bản đồ (Xóa đường và marker cũ)
        self.map_widget.delete_all_path()
        if hasattr(self, 'station_markers'):
            for marker in self.station_markers:
                marker.delete()
        self.station_markers = []

        if not path or len(path) < 2:
            return

        # Biến gom toàn bộ tọa độ của cả hành trình
        full_path_coords = []

        for i in range(len(path)):
            u = path[i]

            # --- PHẦN 1: LẤY TỌA ĐỘ CỦA NÚT HIỆN TẠI ---
            current_node_pos = None
            if u == "Start":
                current_node_pos = self.start_pos
            elif u == "Dest":
                current_node_pos = self.end_pos
            elif u in g.nodes:
                current_node_pos = g.nodes[u]

            # Nếu tìm thấy tọa độ, thêm vào danh sách tổng
            if current_node_pos:
                # Tránh thêm trùng tọa độ nếu node trước đó đã có tọa độ này
                if not full_path_coords or current_node_pos != full_path_coords[-1]:
                    full_path_coords.append(current_node_pos)

            # --- PHẦN 2: LẤY CÁC NÚT CHI TIẾT GIỮA U VÀ V (ĐƯỜNG RAY CONG) ---
            if i < len(path) - 1:
                v = path[i + 1]
                # Lấy danh sách ID trung gian từ edge_paths
                detailed_nodes = g.edge_paths.get((u, v), [])

                for node_id in detailed_nodes:
                    pos = None
                    if isinstance(node_id, tuple):
                        pos = node_id
                    elif node_id in g.nodes:
                        pos = g.nodes[node_id]

                    if pos and (not full_path_coords or pos != full_path_coords[-1]):
                        full_path_coords.append(pos)

            # --- PHẦN 3: ĐẶT MARKER TÊN GA ---
            if u not in ["Start", "Dest"] and u in g.nodes:
                name = g.names.get(u, "Ga Tàu")
                lat, lon = g.nodes[u]
                marker = self.map_widget.set_marker(
                    lat, lon,
                    text=name,
                    marker_color_circle="#e74c3c",  # Màu đỏ cho ga tàu
                    text_color="#2c3e50"
                )
                self.station_markers.append(marker)

        # --- PHẦN 4: VẼ ĐƯỜNG ĐI DUY NHẤT ---
        if len(full_path_coords) > 1:
            # Bạn có thể đổi màu tùy theo loại đường (đi bộ hoặc tàu)
            self.map_widget.set_path(full_path_coords, color="#3498db", width=5)

        print(f"Đã vẽ đường đi với {len(full_path_coords)} điểm tọa độ.")
    # ===== RESET & XỬ LÝ cho Admin =====
    def show_admin_panel(self):
        self.mode = "admin"
        self.clear_left_frame()

        # 1. Tiêu đề
        ctk.CTkLabel(self.left_frame, text="QUẢN TRỊ VIÊN", font=("Arial", 18, "bold")).pack(pady=10)

        # 2. Nút chức năng
        ctk.CTkButton(self.left_frame, text="Hiện mạng lưới Hover",
                      command=self.draw_all_graph_edges).pack(pady=10)
        # 3. PHẦN BẢNG HIỂN THỊ TUYẾN ĐƯỜNG HỎNG
        ctk.CTkLabel(self.left_frame, text="Danh sách tuyến đường hỏng:", font=("Arial", 13, "bold")).pack(pady=(15, 5))

        # Khung cuộn cho bảng
        table_container = ctk.CTkScrollableFrame(self.left_frame, width=280, height=250)
        table_container.pack(pady=5, padx=10, fill="both", expand=True)

        # Cấu hình cột đều nhau
        table_container.grid_columnconfigure((0, 1), weight=1)

        # Tiêu đề bảng (Header)
        ctk.CTkLabel(table_container, text="Ga đi", font=("Arial", 12, "bold"),
                     fg_color="#1f538d", text_color="white").grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        ctk.CTkLabel(table_container, text="Ga đến", font=("Arial", 12, "bold"),
                     fg_color="#1f538d", text_color="white").grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

        # Lấy dữ liệu từ class Graph
        # Giả sử trong class chính của bạn có self.graph = Graph()
        broken_edges = g._removed_edges

        if not broken_edges:
            ctk.CTkLabel(table_container, text="Hệ thống hoạt động tốt", font=("Arial", 11, "italic")).grid(row=1,
                                                                                                            column=0,
                                                                                                            columnspan=2,
                                                                                                            pady=20)
        else:
            for i, (u, v) in enumerate(broken_edges, start=1):
                name_u = g.names.get(u, f"ID: {u}")
                name_v = g.names.get(v, f"ID: {v}")

                bg_color = "gray25" if i % 2 == 0 else "transparent"

                # Cột Ga Đi
                ctk.CTkLabel(
                    table_container,
                    text=name_u,
                    font=("Arial", 11),
                    fg_color=bg_color,
                    anchor="w",           # Căn lề trái
                    justify="left",       # Căn lề văn bản bên trong sang trái
                    wraplength=120,       # Tự động xuống dòng sau 120 pixel
                    padx=5                # Đệm một chút cho chữ không dính sát lề
                ).grid(row=i, column=0, sticky="nsew", padx=1, pady=1)

                # Cột Ga Đến
                ctk.CTkLabel(
                    table_container,
                    text=name_v,
                    font=("Arial", 11),
                    fg_color=bg_color,
                    anchor="w",           # Căn lề trái
                    justify="left",
                    wraplength=120,       # Tự động xuống dòng
                    padx=5
                ).grid(row=i, column=1, sticky="nsew", padx=1, pady=1)
        # 4. Nút quay lại (đẩy xuống dưới cùng)
        ctk.CTkButton(self.left_frame, text="← Thoát Admin",
                      command=self.exit_admin, fg_color="#d32f2f", hover_color="#b71c1c").pack(side="bottom", pady=20)

    def exit_admin(self):
        # Hủy bind sự kiện Motion
        self.map_widget.canvas.unbind("<Motion>")
        self.show_initial_menu()

    def draw_all_graph_edges(self):
        self.map_widget.delete_all_path()
        self.map_widget.delete_all_marker()
        self.path_objects = []
        created_markers_nodes = set()
        drawed_edges = set()  # Lưu các cặp đã vẽ

        for (u, v), path_data in g.edge_paths.items():

            if (u,v) in drawed_edges or (v,u) in drawed_edges: #ĐOẠN NÀY CHƯA XỬ LÝ 1 CHIỀU
                continue  # Nếu cặp này vẽ rồi thì bỏ qua luôn

            actual_coords = [g.nodes[item] if item in g.nodes else item for item in path_data]

            if len(actual_coords) > 1:
                # KIỂM TRA TRẠNG THÁI: Nếu cặp (u,v) hoặc (v,u) nằm trong danh sách hỏng
                is_broken = (u, v) in g._removed_edges or (v, u) in g._removed_edges
                path_color = "#FF0000" if is_broken else "#000000"
                path_width = 4 if is_broken else 2


                # Vẽ đường với màu sắc tương ứng
                path_obj = self.map_widget.set_path(actual_coords, color=path_color, width=path_width)

                self.path_objects.append({
                    "obj": path_obj,
                    "coords": actual_coords,
                    "id": (u, v)
                })


    def _handle_admin_click(self, coords):
        threshold = 0.001
        found_edge = None
        min_dist=99999

        for item in self.path_objects:
            line_coords = item["coords"]
            cur_dist = min(dist_to_segment(coords, line_coords[i], line_coords[i + 1], threshold)
                   for i in range(len(line_coords) - 1))
            if cur_dist<min_dist and cur_dist<threshold :
                min_dist = cur_dist
                found_edge = item["id"]



        if found_edge != None :
            u, v = found_edge
            # Kiểm tra xem cạnh này đã có trong danh sách hỏng chưa (xét cả 2 chiều)
            existing_edge = next((edge for edge in g._removed_edges if edge == (u, v) or edge == (v, u)), None)
            if existing_edge:
                # Nếu ĐÃ HỎNG -> Sửa nó (Xóa khỏi danh sách)
                g._removed_edges.remove(existing_edge)
                print(f"🛠️ Đã sửa chữa tuyến: {found_edge}")
            else:
                # Nếu ĐANG BÌNH THƯỜNG -> Làm hỏng nó (Thêm vào danh sách)
                g._removed_edges.append((u, v))
                print(f"⚠️ Đã đánh dấu hỏng tuyến: {found_edge}")

            # CẬP NHẬT GIAO DIỆN
            # Vẽ lại toàn bộ bản đồ để cập nhật màu sắc
            self.draw_all_graph_edges()
            # Vẽ lại bảng bên trái để cập nhật danh sách chữ
            self.show_admin_panel()

    def on_closing(self):
        print("\n🔄 Đang chuẩn bị đóng ứng dụng...")

        # 1. Loại bỏ các vị trí chọn tạm thời
        g.remove_chosen_location()
        
        # BỔ SUNG: Chủ động xóa các đoạn hỏng "rác" liên quan đến điểm tự chọn trước khi lưu
        if hasattr(g, '_removed_edges'):
            g._removed_edges = [
                edge for edge in g._removed_edges 
                if "Start" not in edge and "Dest" not in edge and "vị trí" not in str(edge)
            ]

        # 2. Lưu lại vào file Pickle sạch
        g.save_to_pickle(pkl_path)
        print("👋 Dữ liệu đã an toàn. Tạm biệt!")
        self.root.quit()
        self.root.destroy()

def dist_to_segment( p, s1, s2, threshold):
    px, py = p
    x1, y1 = s1
    x2, y2 = s2

    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5 < threshold

    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))  # Giới hạn trong đoạn thẳng s1-s2

    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    dist = ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
    return dist

# ===== MAIN =====
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()