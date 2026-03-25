import math
from math import radians, sin, cos, sqrt, atan2
from scipy.spatial import KDTree
from geopy.distance import geodesic
import json
from Algorithm import DFS, BFS
class Graph():
    def __init__(self):
        self.nodes = {}  # node_id -> (lat, lon)
        self.names = {}  # node_id -> station name
        self.adj_list = {}  # node_id -> list of (neighbor_id, cost)
        self.edges = []  # (u, v, cost)

        self.obstacles = set()
        self._removed_edges = {}

        self._kd_tree = None
        self._node_ids = []

    def haversine(self,lat1, lon1, lat2, lon2):
        R = 6371  # km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) \
            * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2

        return 2 * R * math.asin(math.sqrt(a))
    def find_neighbor(self,node):
        return [neighbor_node[0] for neighbor_node in self.adj_list[node]]

    def load_from_json(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 🔹 Reset dữ liệu cũ
        self.nodes.clear()
        self.names.clear()
        self.adj_list.clear()
        self.edges.clear()
        self._node_ids.clear()
        self._kd_tree = None

        # 🔹 1. Load nodes
        # Trong JSON mới: node_id là Key (ví dụ: "NS10"), info là Value
        for node_id, info in data.items():
            # Lấy tọa độ từ list [long, lat]
            lon, lat = info["coordinates"]
            name = info.get("name", "Unknown")
            if(name=="NS17"): print("check")
            self.nodes[node_id] = (lat, lon)  # Lưu (lat, lon) để khớp với hàm haversine của bạn
            self.names[node_id] = name
            self.adj_list[node_id] = []

        # 🔹 2. Load edges (Trọng số đã có sẵn trong JSON, không cần tính lại)
        for u, info in data.items():
            # Duyệt qua danh sách kề trong JSON: [{"node": "...", "weight": ...}, ...]
            for neighbor in info.get("adjacency", []):
                v = neighbor["node"]
                cost = neighbor["weight"]
                if v in self.nodes:
                    if (u == "NS16"): print(neighbor)
                    self.adj_list[u].append((v, cost))
                    self.edges.append((u, v, cost))

        # 🔹 3. Build KDTree
        points = []
        for node_id, (lat, lon) in self.nodes.items():
            points.append((lat, lon))
            self._node_ids.append(node_id)

        if points:
            from scipy.spatial import KDTree  # Đảm bảo đã import
            self._kd_tree = KDTree(points)

        print(f"✅ Đã load {len(self.nodes)} ga MRT thành công.")

    def print_info_stations(self):
        i=0
        for node, coord in self.nodes.items():
            print(node)
            print(coord)
            print(self.names[node])
            print(self.adj_list[node])
            print("-----------")
            i+=1


    def add_chosen_location(self, start_coord, end_coord):
        """
        Kết nối START/END với 3 ga gần nhất để tối ưu tìm đường
        """
        if not self._kd_tree:
            return None, None

        # Tạo ID tạm thời cho 2 điểm này
        start_node = "Start"
        end_node = "Dest"

        # Khởi tạo danh sách kề tạm thời cho 2 nút này
        self.adj_list[start_node] = []
        self.nodes[start_node] = start_coord
        self.names[start_node] = "Vị trí của bạn"


        self.adj_list[end_node] = []
        self.nodes[end_node] = end_coord
        self.names[end_node] = "Điểm đến"

        # 🔹 Tìm 3 ga gần nhất cho mỗi điểm (k=3)
        for point_type, coord, node_id in [("START", start_coord, start_node),
                                           ("END", end_coord, end_node)]:

            # k=3 để lấy 3 hàng xóm gần nhất
            dists, indices = self._kd_tree.query([coord[0], coord[1]], k=3)

            for d, idx in zip(dists, indices):
                neighbor_id = self._node_ids[idx]

                # Tính khoảng cách thực tế bằng Haversine (km)
                cost = self.haversine(coord[0], coord[1],
                                      self.nodes[neighbor_id][0], self.nodes[neighbor_id][1])

                # Nối 2 chiều: Từ vị trí chọn -> Ga MRT và ngược lại
                self.adj_list[node_id].append((neighbor_id, cost))
                self.adj_list[neighbor_id].append((node_id, cost))

    def remove_chosen_location(self):
        """
        Dọn dẹp các nút tạm thời và các kết nối liên quan để reset đồ thị
        """
        temp_nodes = ["Start", "Dest"]

        for temp_id in temp_nodes:
            if temp_id in self.adj_list:
                # 1. Tìm tất cả các ga hàng xóm đang nối với nút tạm này
                neighbors = self.adj_list[temp_id]

                for neighbor_tuple in neighbors:
                    neighbor_id = neighbor_tuple[0]  # Lấy mã ga MRT (ví dụ: "NS10")

                    # 2. Xóa cạnh ngược: Từ ga MRT trỏ về nút tạm
                    if neighbor_id in self.adj_list:
                        # Lọc bỏ các tuple có chứa temp_id
                        self.adj_list[neighbor_id] = [
                            item for item in self.adj_list[neighbor_id]
                            if item[0] != temp_id
                        ]

                # 3. Xóa chính nút tạm trong các bảng dữ liệu
                del self.adj_list[temp_id]

                if temp_id in self.nodes:
                    del self.nodes[temp_id]
                if temp_id in self.names:
                    del self.names[temp_id]

        print("🧹 Đồ thị đã được dọn dẹp (Reset về trạng thái MRT gốc).")

g =  Graph()
g.load_from_json(r"C:\Users\phank\PycharmProjects\INTRO_AI_IT3160_20252\res\mrt_graph.json")
g.add_chosen_location((1.445, 103.805),(1.285, 103.860))
bfs = BFS()
total_nodes,path=bfs.run("Start","Dest",g)
print(total_nodes,path)
dfs = DFS()
total_nodes,path = dfs.run("Start","Dest",g)
print(total_nodes,path)

