import math
from math import radians, sin, cos, sqrt, atan2
from scipy.spatial import KDTree
from geopy.distance import geodesic
import json
from Algorithm import DFS
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
            if(i==10) : break
g =  Graph()
g.load_from_json(r"C:\Users\phank\PycharmProjects\INTRO_AI_IT3160_20252\res\mrt_graph.json")
g.print_info_stations()

