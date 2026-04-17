import math
from scipy.spatial import KDTree
import pickle
import requests

class Graph():
    def __init__(self):
        self.nodes = {}  # node_id -> (lat, lon)
        self.names = {}  # node_id -> station name
        self.stations = {} # Lưu riêng các node là ga tàu node_id -> (lat, lon)
        self.adj_list = {}  # node_id -> list of (neighbor_id, cost)
        self.edge_paths = {}  #  key = (node đầu, node đuôi) value = list_path[]

        self.obstacles = set()
        self._removed_edges = {}

        self._kd_tree = None
        self._node_ids = []

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) \
            * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2

        return 2 * R * math.asin(math.sqrt(a))
        
    def find_neighbor(self, node):
        return [neighbor_node[0] for neighbor_node in self.adj_list[node]] #một list các node hàng xóm

    def load_from_pickle(self, pkl_path):
        """Hàm load siêu tốc từ file bộ nhớ đệm"""
        print("⚡ Đang tải dữ liệu siêu tốc từ file .pkl...")
        with open(pkl_path, "rb") as f:
            data = pickle.load(f) # Bung toàn bộ dữ liệu thẳng vào RAM

        # Cập nhật lại các biến instance
        self.nodes = data["nodes"]
        self.names = data["names"]
        self.stations = data["stations"]
        self.adj_list = data["adj_list"]
        self.edge_paths = data["edge_paths"]
        self._node_ids = data["node_ids"]
        self._kd_tree = data["kd_tree"]

        print(f"✅ Đã tải xong siêu tốc: {len(self.nodes)} điểm đường ray và {len(self.stations)} ga tàu.")

    def print_info_stations(self):
        i = 0
        for node, coord in self.nodes.items():
            print(node)
            print(coord)
            print(self.names.get(node, "Unknown"))
            print(self.adj_list.get(node, []))
            print("-----------")
            i += 1
            if i > 10: break # Chỉ in 10 cái để tránh trôi màn hình terminal

    def add_chosen_location(self, start_coord, end_coord): #HÀM CÓ VẤN ĐỀ !!!
        """
        Kết nối START/END với 3 ga gần nhất để tối ưu tìm đường
        """
        if not self._kd_tree:
            return None, None

        # 🔹 DỌN DẸP ĐIỂM CŨ TRƯỚC KHI THÊM MỚI (Tránh rác dữ liệu khi ấn Run nhiều lần)
        self.remove_chosen_location()

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

        # 🔹 Tìm 3 điểm đường ray gần nhất cho mỗi điểm (k=3)
        start_dists, start_indices = self._kd_tree.query((start_coord[0], start_coord[1]), k = 3)
        end_dists, end_indices = self._kd_tree.query((end_coord[0], end_coord[1]), k = 3)

        def get_osrm_walking_data(from_lat, from_lon, to_lat, to_lon):
            try:
                url = f"http://router.project-osrm.org/route/v1/foot/{from_lon},{from_lat};{to_lon},{to_lat}?geometries=geojson"
                response = requests.get(url, timeout= 3).json()
                if response.get("code") == "Ok":
                    route = response["routes"][0]
                    path_coords = [(lat,lon) for lon, lat in route["geometry"]["coordinates"]]
                    distance_km = route["distance"] / 1000.0
                    return distance_km, path_coords
            except Exception as e:
                print(f"Lỗi gọi OSRM: {e}")
            return None, None

        #Xử lý Start với 3 ga gần nhất
        for coord, dists, indices, coord_id in [(start_coord ,start_dists, start_indices, start_node), (end_coord, end_dists, end_indices, end_node)]:
            for d, idx in zip(dists, indices):
                neighbor_id = self._node_ids[idx]
                n_lat, n_lon = self.nodes[neighbor_id]
                walk_cost, walk_path = get_osrm_walking_data(coord[0], coord[1], n_lat, n_lon)
                if walk_cost is None:
                    walk_cost = self.haversine(coord[0], coord[1], n_lat, n_lon)
                    walk_path = [coord_id, neighbor_id]
                self.adj_list[coord_id].append((neighbor_id, walk_cost))
                self.adj_list[neighbor_id].append((coord_id, walk_cost))

                self.edge_paths[(coord_id, neighbor_id)] = walk_path
                self.edge_paths[(neighbor_id, coord_id)] = list(reversed(walk_path))

    def remove_chosen_location(self): #CÓ VẤN ĐỀ THEO HÀM TRÊN LUÔN !!!
        """
        Dọn dẹp các nút tạm thời và các kết nối liên quan để reset đồ thị
        """
        temp_nodes = ["Start", "Dest"]

        for temp_id in temp_nodes:
            if temp_id in self.adj_list:
                # 1. Tìm tất cả các hàng xóm đang nối với nút tạm này
                neighbors = self.adj_list[temp_id]

                for neighbor_tuple in neighbors:
                    neighbor_id = neighbor_tuple[0]

                    # 2. Xóa cạnh ngược: Từ hàng xóm trỏ về nút tạm
                    if neighbor_id in self.adj_list:
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
        keys_to_delete = [k for k in self.edge_paths.keys() if "Start" in k or "Dest" in k] #list các tuple
        for key in keys_to_delete:
            del self.edge_paths[key]