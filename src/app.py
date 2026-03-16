import tkinter as tk
import tkintermapview
import osmnx as ox
import threading

class SingaporeMRTApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("900x700")
        self.root.title("Bản đồ hệ thống MRT/LRT Singapore")

        # 1. Khởi tạo bản đồ TkinterMapView
        self.map_widget = tkintermapview.TkinterMapView(self.root, corner_radius=0)
        self.map_widget.pack(fill="both", expand=True)

        # 2. Đặt tâm bản đồ về khu vực Singapore
        self.map_widget.set_position(1.3521, 103.8198) 
        self.map_widget.set_zoom(12)

        # Đường dẫn tới file .osm của bạn (nhớ đổi tên cho đúng)
        self.source_path = "resexport.osm" 

        # 3. Chạy luồng phụ để load dữ liệu tránh treo giao diện UI
        threading.Thread(target=self.load_and_draw_graph, daemon=True).start()

    def load_and_draw_graph(self):
        print("Đang đọc file .osm...")
        try:
            # Sử dụng đúng hàm bạn đã dùng trong đồ án để load đồ thị từ file xml/osm
            G = ox.graph_from_xml(self.source_path, retain_all=True, simplify=False)
            print(f"Tải thành công! Đồ thị có {len(G.nodes)} đỉnh và {len(G.edges)} cạnh.")
        except Exception as e:
            print(f"Lỗi khi đọc file bản đồ: {e}")
            return

        print("Đang vẽ các tuyến tàu điện lên bản đồ...")
        
        # Lấy danh sách tọa độ các node để tra cứu nhanh
        node_coords = {node_id: (data['y'], data['x']) for node_id, data in G.nodes(data=True)}

        print("Hoàn tất hiển thị!")

if __name__ == "__main__":
    root = tk.Tk()
    app = SingaporeMRTApp(root)
    root.mainloop()