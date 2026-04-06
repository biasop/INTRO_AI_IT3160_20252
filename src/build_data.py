import osmnx as ox
import math
import pickle
from scipy.spatial import KDTree
from pathlib import Path

# Cấu hình đường dẫn
current_dir = Path(__file__).parent
osm_path = current_dir.parent / "res" / "export.osm"
pkl_path = current_dir.parent / "res" / "mrt_graph.pkl" # File nhị phân đầu ra

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def build_and_save_data():
    print(f"⏳ Đang đọc file OSM gốc từ {osm_path} (Sẽ mất chút thời gian)...")
    G_nx = ox.graph_from_xml(osm_path, simplify=False)

    nodes = {}
    names = {}
    stations = {}
    adj_list = {}
    edges = []
    node_ids = []

    print("⏳ Đang phân tích Đỉnh và Cạnh...")
    for node_id, data in G_nx.nodes(data=True):
        nodes[node_id] = (data['y'], data['x'])
        adj_list[node_id] = []
        
        if data.get('railway') == 'station' or data.get('station') in ['subway', 'light_rail']:
            name = data.get('name', 'Ga chưa rõ tên')
            names[node_id] = f"Ga {name}"
            stations[node_id] = (data['y'], data['x'])
        else:
            names[node_id] = "Đường ray"

    for u, v, data in G_nx.edges(data=True):
        cost = haversine(nodes[u][0], nodes[u][1], nodes[v][0], nodes[v][1])
        adj_list[u].append((v, cost))
        adj_list[v].append((u, cost)) 
        edges.append((u, v, cost))

    print("⏳ Đang xây dựng cây KDTree để tối ưu tìm kiếm...")
    for node_id, (lat, lon) in nodes.items():
        node_ids.append(node_id)
        
    points = [nodes[nid] for nid in node_ids]
    kd_tree = KDTree(points) if points else None

    # Đóng gói tất cả vào một Dictionary
    data_to_save = {
        "nodes": nodes,
        "names": names,
        "stations": stations,
        "adj_list": adj_list,
        "edges": edges,
        "node_ids": node_ids,
        "kd_tree": kd_tree
    }

    print(f"⏳ Đang nén và lưu ra file {pkl_path}...")
    with open(pkl_path, "wb") as f:
        pickle.dump(data_to_save, f)

    print(f"✅ Hoàn tất! Đã lưu {len(nodes)} điểm vào file .pkl.")

if __name__ == "__main__":
    build_and_save_data()