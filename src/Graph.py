import math
from scipy.spatial import KDTree
import pickle

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
        for _, coord, node_id in [("START", start_coord, start_node),
                                           ("END", end_coord, end_node)]:

            # k=3 để lấy 3 hàng xóm gần nhất
            dists, indices = self._kd_tree.query([coord[0], coord[1]], k=3) #ĐOẠN NÀY CẦN SỬA VÌ NÓ ĐANG TÌM TỚI ĐƯỜNG RAY, KHÔNG PHẢI GA TÀU
            # Sau khi sửa thì kd_tree đã chọn ra ga tàu, không phải đường ray
            for _, idx in zip(dists, indices): #dist bị thừa
                neighbor_id = self._node_ids[idx]

                # Tính khoảng cách thực tế bằng Haversine (km)
                cost = self.haversine(coord[0], coord[1],
                                      self.nodes[neighbor_id][0], self.nodes[neighbor_id][1])

                # Nối 2 chiều: Từ vị trí chọn -> Đường ray và ngược lại
                self.adj_list[node_id].append((neighbor_id, cost))
                self.adj_list[neighbor_id].append((node_id, cost))

                self.edge_paths[(node_id, neighbor_id)] = [node_id, neighbor_id]
                self.edge_paths[(neighbor_id, node_id)] = [neighbor_id, node_id]

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

    def calculate_path_distance(self, path):
        """Tính tổng chiều dài uốn lượn thực tế của một đường đi (km)"""
        if not path or len(path) < 2:
            return 0.0

        total_distance = 0.0
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            
            lat1, lon1 = self.nodes[u]
            lat2, lon2 = self.nodes[v]
            
            total_distance += self.haversine(lat1, lon1, lat2, lon2)
            
        return total_distance