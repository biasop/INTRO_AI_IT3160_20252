import math
from scipy.spatial import KDTree
import pickle
import requests
import json
class Graph():
    def __init__(self):
        self.nodes = {}  # node_id -> (lat, lon)
        self.names = {}  # node_id -> station name
        self.stations = {} # Lưu riêng các node là ga tàu node_id -> (lat, lon)
        self.adj_list = {}  # node_id -> list of (neighbor_id, cost)
        self.edge_paths = {}  #  key = (node đầu, node đuôi) value = list_path[]

        self._removed_edges = [] #(u,v)

        self._kd_tree = None
        self._node_ids = []

    def load_from_json(self, graph_path, segment_path):
        # 1. Đọc file mrt_graph (nút và kề)
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)

        for node_id, info in graph_data.items():
            # Lưu ý: file graph của bạn là [Lon, Lat], ta đổi về (Lat, Lon)
            lat, lon = info["coordinates"][1], info["coordinates"][0]
            self.nodes[node_id] = (lat, lon)
            self.names[node_id] = info["name"]
            self.stations[node_id] = (lat, lon)

            # Nạp danh sách kề
            self.adj_list[node_id] = []
            for neighbor in info.get("adjacency", []):
                self.adj_list[node_id].append((neighbor["node"], neighbor["weight"]))

        # 2. Đọc file segments (đường đi chi tiết)
        with open(segment_path, 'r', encoding='utf-8') as f:
            segment_data = json.load(f)

        for seg_id, info in segment_data.items():
            u = info["from"]
            v = info["to"]
            # Chuyển list [lat, lon] bên trong path thành list của các tuple (lat, lon)
            path_coords = [tuple(p) for p in info["path"]]
            self.edge_paths[(u, v)] = path_coords

        print(f"✅ Đã nạp {len(self.nodes)} nút và {len(self.edge_paths)} đoạn đường.")

    def verify_graph_integrity(self):
        adj_edges = set()

        for u, neighbors in self.adj_list.items():
            # Kiểm tra nếu neighbors không phải danh sách
            if not isinstance(neighbors, list):
                print(f"LỖI CẤU TRÚC: Node {u} có adj_list không phải là list (Kiểu: {type(neighbors)})")
                continue

            for item in neighbors:
                # Kiểm tra xem item có phải (v, cost) không
                if not isinstance(item, (tuple, list)) or len(item) < 2:
                    print(f"LỖI DỮ LIỆU: Tại node {u}, item '{item}' không phải cặp (v, cost)")
                    continue

                v, cost = item[0], item[1]
                edge = tuple(sorted((u, v)))
                adj_edges.add(edge)

        path_edges = set()
        for edge_key in self.edge_paths.keys():
            path_edges.add(tuple(sorted(edge_key)))

        # So sánh như cũ
        missing_paths = adj_edges - path_edges
        extra_paths = path_edges - adj_edges

        print(f"--- Kết quả kiểm tra ---")
        print(f"Cạnh trong adj_list: {len(adj_edges)}")
        print(f"Cạnh trong edge_paths: {len(path_edges)}")

        if missing_paths: print(f"Thiếu path cho: {list(missing_paths)[:3]}...")
        if extra_paths: print(f"Thừa path tại: {list(extra_paths)[:3]}...")
    def save_to_json(self, graph_output_path, segment_output_path):
        # 1. Chuẩn bị dữ liệu cho mrt_graph
        graph_to_save = {}
        for node_id in self.nodes:
            lat, lon = self.nodes[node_id]
            graph_to_save[node_id] = {
                "name": self.names.get(node_id, ""),
                "coordinates": [lon, lat],  # Lưu lại dạng [Lon, Lat] như gốc
                "adjacency": [
                    {"node": neighbor, "weight": weight}
                    for neighbor, weight in self.adj_list.get(node_id, [])
                ],
                "network_count": 1.0
            }

        # 2. Chuẩn bị dữ liệu cho segments
        segments_to_save = {}
        for (u, v), path in self.edge_paths.items():
            key = f"{u}->{v}"
            segments_to_save[key] = {
                "from": u,
                "to": v,
                "path": path  # path đã là list của list hoặc tuple
            }

        # Ghi file mrt_graph
        with open(graph_output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_to_save, f, indent=4, ensure_ascii=False)

        # Ghi file segments
        with open(segment_output_path, 'w', encoding='utf-8') as f:
            json.dump(segments_to_save, f, indent=4, ensure_ascii=False)

        print(f"💾 Đã lưu dữ liệu ra {graph_output_path} và {segment_output_path}")
    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) \
            * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2

        return 2 * R * math.asin(math.sqrt(a))
        
    def get_neighbors(self, node):
        """Trả về danh sách hàng xóm hợp lệ (không đi qua các đoạn tàu hỏng)"""
        if node not in self.adj_list:
            return []
        valid_neighbors = []
        for neighbor, weight in self.adj_list[node]:
            # Nếu cạnh nằm trong danh sách hỏng (xét cả 2 chiều để an toàn) thì bỏ qua
            if (node, neighbor) in self._removed_edges or (neighbor, node) in self._removed_edges:
                continue
            valid_neighbors.append((neighbor, weight))
        return valid_neighbors

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

        self._removed_edges = data.get("_removed_edges", [])
        
        self._node_ids = data["node_ids"]
        self._kd_tree = data["kd_tree"]

        print(f"✅ Đã tải xong siêu tốc: {len(self.nodes)} điểm đường ray và {len(self.stations)} ga tàu.")


    def save_to_pickle(self, pkl_path):
        """Hàm lưu toàn bộ trạng thái đồ thị vào file .pkl để tải nhanh lần sau"""
        print(f"💾 Đang đóng gói và lưu dữ liệu vào {pkl_path}...")

        try:
            # Gom tất cả các thuộc tính quan trọng vào một dictionary
            data_to_save = {
                "nodes": self.nodes,
                "names": self.names,
                "stations": self.stations,
                "adj_list": self.adj_list,
                "edge_paths": self.edge_paths,
                "_removed_edges":self._removed_edges,
                "node_ids": self._node_ids,
                "kd_tree": self._kd_tree
            }

            # Lưu dưới dạng binary (wb)
            with open(pkl_path, "wb") as f:
                pickle.dump(data_to_save, f)

            print("✅ Lưu file .pkl thành công! Lần sau bạn có thể dùng load_from_pickle để mở app ngay lập tức.")

        except Exception as e:
            print(f"❌ Lỗi khi lưu file pickle: {e}")
    def print_info_stations(self):
        i = 0
        for node, coord in self.nodes.items():
            if(self.names.get(node)=="Đường ray") : continue
            if(type(node) == int) :continue
            print(node)
            print(coord)
            print(self.names.get(node, "Unknown"))
            print(self.adj_list.get(node, []))
            print("-----------")
            i += 1


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

    def remove_chosen_location(self):
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