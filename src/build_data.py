import osmnx as ox
import math
import pickle
from scipy.spatial import KDTree
from pathlib import Path
import xml.etree.ElementTree as ET
import re
# Cấu hình đường dẫn
current_dir = Path(__file__).parent
osm_path = current_dir.parent / "res" / "export.osm"
pkl_path = current_dir.parent / "res" / "mrt_graph.pkl" # File nhị phân đầu ra

def extract_station_from_osm():
    def clean_station_name(name):
        # 1. Bỏ phần trong ngoặc đơn: "Admiralty (NSL)" -> "Admiralty"
        name = re.sub(r'\(.*?\)', '', name)
        
        # 2. Bỏ phần Exit: "Admiralty Exit A" -> "Admiralty"
        name = re.sub(r'\bExit\b.*', '', name, flags=re.IGNORECASE)
        
        # 3. Xóa khoảng trắng thừa
        return name.strip()
    
    tree = ET.parse(osm_path)
    root = tree.getroot()
    all_nodes = {}

    grouped_stations = {} #key: name của ga, value: [] list of (lat, lon)

    def is_station(tags):
        return (
            tags.get('railway') in ['station', 'halt', 'subway_entrance'] or
            tags.get('station') in ['subway', 'light_rail', 'yes'] or
            tags.get('public_transport') == 'station'
        )

    for node in root.findall('node'):
        all_nodes[node.attrib['id']] = (float(node.attrib['lat']), float(node.attrib['lon']))

    for node in root.findall('node'):
        tags = {tag.attrib['k']: tag.attrib['v'] for tag in node.findall('tag')}
        if is_station(tags):
            raw_name = tags.get('name')
            if raw_name:
                name = clean_station_name(raw_name)
                if name not in grouped_stations:
                    grouped_stations[name] = []
                grouped_stations[name].append((float(node.attrib['lat']), float(node.attrib['lon'])))
    
    for way in root.findall('way'):
        tags = {tag.attrib['k']: tag.attrib['v'] for tag in node.findall('tag')}
        if is_station(tags):
            name = tags.get('name', 'Chưa rõ tên')
            if name != 'Chưa rõ tên':
                lats, lons = [], []
                for nd in way.findall('nd'):
                    ref = nd.attrib['ref']
                    if ref in all_nodes:
                        lats.append(all_nodes[ref][0])
                        lons.append(all_nodes[ref][1])
                    if lats and lons:
                        avr_lat = sum(lats)/len(lats)
                        avr_lon = sum(lons)/len(lons)
                        if name not in grouped_stations:
                            grouped_stations[name] = []
                        grouped_stations.append((avr_lat, avr_lon))

    extracted_stations = []
    for name, coords_list in grouped_stations.items():
        final_lat = sum(c[0] for c in coords_list) / len(coords_list)
        final_lon = sum(c[1] for c in coords_list) / len(coords_list)
        extracted_stations.append({
            'name': name,
            'lat': final_lat,
            'lon': final_lon
        })

    print(f"🔍 Đã lọc trùng và tìm thấy chính xác {len(extracted_stations)} Ga tàu duy nhất.")
    return extracted_stations

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
    raw_adj_list = {}

    print("⏳ Đang phân tích Đỉnh và Cạnh...")
    for node_id, data in G_nx.nodes(data=True):
        nodes[node_id] = (data['y'], data['x'])
        raw_adj_list[node_id] = []
        names[node_id] = "Đường ray"

    for u, v, data in G_nx.edges(data=True):
        cost = haversine(nodes[u][0], nodes[u][1], nodes[v][0], nodes[v][1])
        raw_adj_list[u].append((v, cost))
        raw_adj_list[v].append((u, cost))

    extracted_stations = extract_station_from_osm()
    all_node_ids = list(nodes.keys())
    all_points = [nodes[nid] for nid in all_node_ids]
    temp_kdtree = KDTree(all_points)

    print("⏳ Đang ánh xạ Ga tàu vào mạng lưới đường ray...")
    for st in extracted_stations:
        # Bỏ qua các ga rác không có tên
        if st['name'] == 'Chưa rõ tên':
            continue
            
        dist, idx = temp_kdtree.query([st['lat'], st['lon']], k=1)
        nearest_node_id = all_node_ids[idx]
        
        # Nếu điểm đường ray này ĐÃ được một ga khác "chiếm" rồi
        if nearest_node_id in stations:
            old_name = names[nearest_node_id]
            new_name = st['name']
            
            # Tránh gộp tên trùng lặp
            if new_name not in old_name:
                names[nearest_node_id] = f"{old_name} / Ga {new_name}"
        
        # Nếu điểm đường ray này còn trống
        else:
            names[nearest_node_id] = f"Ga {st['name']}"
            stations[nearest_node_id] = nodes[nearest_node_id]

    print(f"✅ Đã đóng dấu thành công {len(stations)} Ga tàu trên mạng lưới!")

    #Sửa
    print("⏳ Đang nén đồ thị: Tính toán đường đi giữa các Ga tàu kề nhau...") #Dùng BFS
    adj_list = {sid: [] for sid in stations.keys()}
    edge_paths = {} # key = (node đầu, node đuôi) value = list_path[]
    for start_station in stations.keys():
        visited = set([start_station])
        queue = [(start_station, 0.0, [start_station])] #node hiện tại, chi phí, list các node trên đường đi

        while queue:
            curr, curr_cost, path = queue.pop(0)

            if curr != start_station and curr in stations:
                adj_list[start_station].append((curr, curr_cost))
                edge_paths[(start_station, curr)] = path
                continue
            
            for neighbor, weight in raw_adj_list[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, curr_cost + weight, path + [neighbor]))


    print("⏳ Đang xây dựng cây KDTree để tối ưu tìm kiếm...") #sửa thành chỉ lấy ga tàu    
    node_ids = list(stations.keys())
    points = [stations[nid] for nid in node_ids]
    kd_tree = KDTree(points) if points else None

    # Đóng gói tất cả vào một Dictionary
    data_to_save = {
        "nodes": nodes,
        "names": names,
        "stations": stations,
        "adj_list": adj_list,
        "edge_paths": edge_paths,
        "node_ids": node_ids,
        "kd_tree": kd_tree
    }

    print(f"⏳ Đang nén và lưu ra file {pkl_path}...")
    with open(pkl_path, "wb") as f:
        pickle.dump(data_to_save, f)

    print(f"✅ Hoàn tất! Đã lưu {len(nodes)} điểm vào file .pkl.")

if __name__ == "__main__":
    build_and_save_data()