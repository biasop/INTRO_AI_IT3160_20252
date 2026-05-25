import osmnx as ox
import math
import pickle
from scipy.spatial import KDTree
from pathlib import Path
import xml.etree.ElementTree as ET
import re

# ==========================================
# CẤU HÌNH ĐƯỜNG DẪN TƯƠNG ĐỐI
# ==========================================
current_dir = Path(__file__).parent
osm_path = current_dir.parent / "res" / "export.osm"
pkl_path = current_dir.parent / "res" / "mrt_graph.pkl"

# ==========================================
# CÁC HÀM TIỆN ÍCH & CHUẨN HÓA
# ==========================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Bán kính Trái Đất (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def clean_station_name(name):
    if not name: return ""
    name = name.lower()
    name = re.sub(r'[-\s]*exi?xt?\s+[a-z0-9]+', '', name)
    name = re.sub(r'\bexit\b.*', '', name)
    name = re.sub(r'\bstation\b', '', name)
    name = re.sub(r'\bmrt\b', '', name)
    name = re.sub(r'\blrt\b', '', name)
    name = re.sub(r'\bconnector\b', '', name)
    name = re.sub(r'\(.*', '', name) 
    name = re.sub(r'[-/]', ' ', name) 
    name = name.strip()
    if len(name) <= 1: return ""
    name = re.sub(r'\s+', ' ', name)
    return name.strip().title()

def get_center(coords):
    avg_lat = sum(c[0] for c in coords) / len(coords)
    avg_lon = sum(c[1] for c in coords) / len(coords)
    return (avg_lat, avg_lon)

# ==========================================
# TRÍCH XUẤT DỮ LIỆU TỪ XML
# ==========================================
def extract_stops_from_osm():
    tree = ET.parse(osm_path)
    root = tree.getroot()
    grouped_by_name = {}
    
    for node in root.findall('node'):
        tags = {tag.attrib['k']: tag.attrib['v'] for tag in node.findall('tag')}
        if tags.get('public_transport') == 'stop_position' or tags.get('railway') == 'stop':
            raw_name = tags.get('name', '')
            name = clean_station_name(raw_name)
            if not name: continue
                
            node_id = node.attrib['id']
            coord = (float(node.attrib['lat']), float(node.attrib['lon']))
            
            if name not in grouped_by_name:
                grouped_by_name[name] = {'id': node_id, 'name': name, 'coord': [coord]}
            else:
                grouped_by_name[name]['coord'].append(coord)

    stop_dict = {}
    for data in grouped_by_name.values():
        stop_dict[data.pop('id')] = data
    return stop_dict

def extract_stations_to_stops():
    tree = ET.parse(osm_path)
    root = tree.getroot()
    stations_dict = {}
    unique_name_station = set()
    node_coords = {}
    
    # 1. Quét Node
    for node in root.findall('node'):
        node_id = node.attrib['id']
        lat, lon = float(node.attrib['lat']), float(node.attrib['lon'])
        node_coords[node_id] = (lat, lon)
        
        tags = {tag.attrib['k']: tag.attrib['v'] for tag in node.findall('tag')}
        if tags.get('railway') in ['station', 'subway_entrance'] and not (tags.get('public_transport') == 'stop_position' or tags.get('railway') == 'stop'):
            name = clean_station_name(tags.get('name', ''))
            if name and name not in unique_name_station:
                unique_name_station.add(name)
                stations_dict[node_id] = {'name': name, 'coord': (lat, lon)}

    # 2. Quét Way
    for way in root.findall('way'):
        tags = {tag.attrib['k']: tag.attrib['v'] for tag in way.findall('tag')}
        if tags.get('railway') in ['station'] and 'name' in tags:
            name = clean_station_name(tags['name'])
            if name and name not in unique_name_station:
                lats, lons = [], []
                for nd in way.findall('nd'):
                    ref_id = nd.attrib['ref']
                    if ref_id in node_coords:
                        lats.append(node_coords[ref_id][0])
                        lons.append(node_coords[ref_id][1])
                if lats and lons:
                    unique_name_station.add(name)
                    stations_dict[way.attrib['id']] = {'name': name, 'coord': (sum(lats)/len(lats), sum(lons)/len(lons))}
    return stations_dict

# ==========================================
# HÀM CHÍNH: XÂY DỰNG, NÉN VÀ LƯU GRAPH
# ==========================================
def build_and_save_data():
    print("⏳ [1/5] Đang trích xuất và đồng bộ hóa Ga tàu từ OSM...")
    stops = extract_stops_from_osm()  
    stations = extract_stations_to_stops() 
    
    # Gộp Stop và Station để lấy danh sách Ga chuẩn cuối cùng
    extracted_stations = []
    for stop_id, stop_data in stops.items():
        name = stop_data['name']
        matched_coord = None
        for st_data in stations.values():
            if name == st_data['name']:
                matched_coord = st_data['coord']
                break
        
        final_coord = matched_coord if matched_coord else get_center(stop_data['coord'])
        extracted_stations.append({
            'name': name,
            'lat': final_coord[0],
            'lon': final_coord[1]
        })
    print(f"🎉 Đã chốt sổ {len(extracted_stations)} Ga đại diện.")

    print(f"\n⏳ [2/5] Đang đọc file mạng lưới đường ray từ {osm_path} (Sẽ mất chút thời gian)...")
    G_nx = ox.graph_from_xml(osm_path, simplify=False)

    nodes = {}
    names = {}
    graph_stations = {} # Đổi tên biến local để tránh trùng lặp với stations dict ở trên
    raw_adj_list = {}

    print("⏳ [3/5] Đang phân tích Đỉnh và Cạnh (Tính Haversine)...")
    for node_id, data in G_nx.nodes(data=True):
        nodes[node_id] = (data['y'], data['x'])
        raw_adj_list[node_id] = []
        names[node_id] = "Đường ray"

    for u, v, data in G_nx.edges(data=True):
        cost = haversine(nodes[u][0], nodes[u][1], nodes[v][0], nodes[v][1])
        raw_adj_list[u].append((v, cost)) # Giữ nguyên luồng đi có hướng như bạn yêu cầu

    all_node_ids = list(nodes.keys())
    all_points = [nodes[nid] for nid in all_node_ids]
    temp_kdtree = KDTree(all_points)

    print("⏳ [4/5] Đang ánh xạ Ga tàu vào mạng lưới đường ray...")
    for st in extracted_stations:
        dist, idx = temp_kdtree.query([st['lat'], st['lon']], k=1)
        nearest_node_id = all_node_ids[idx]
        
        # Nếu điểm đường ray này ĐÃ được một ga khác "chiếm" rồi
        if nearest_node_id in graph_stations:
            old_name = names[nearest_node_id]
            new_name = st['name']
            # Tránh gộp tên trùng lặp
            if new_name not in old_name:
                names[nearest_node_id] = f"{old_name} / Ga {new_name}"
        
        # Nếu điểm đường ray này còn trống
        else:
            names[nearest_node_id] = f"Ga {st['name']}"
            graph_stations[nearest_node_id] = nodes[nearest_node_id]

    print(f"✅ Đã đóng dấu thành công {len(graph_stations)} Ga tàu lên các Node của mạng lưới!")

    print("\n⏳ [5/5] Đang nén đồ thị: Dùng BFS tính đường đi ngắn nhất giữa các Ga kề nhau...")
    adj_list = {sid: [] for sid in graph_stations.keys()}
    edge_paths = {} # key = (node đầu, node đuôi), value = list_path
    
    for start_station in graph_stations.keys():
        visited = set([start_station])
        queue = [(start_station, 0.0, [start_station])]

        while queue:
            curr, curr_cost, path = queue.pop(0)

            if curr != start_station and curr in graph_stations:
                adj_list[start_station].append((curr, curr_cost))
                edge_paths[(start_station, curr)] = path
                continue # Tìm thấy ga tiếp theo rồi thì dừng nhánh BFS này lại
            
            for neighbor, weight in raw_adj_list[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, curr_cost + weight, path + [neighbor]))

    print("⏳ Đang xây dựng cây KDTree (chỉ dành cho Ga) để tối ưu UI Map...")
    node_ids = list(graph_stations.keys())
    points = [graph_stations[nid] for nid in node_ids]
    kd_tree = KDTree(points) if points else None

    # Đóng gói chuẩn theo đúng format gốc của bạn
    data_to_save = {
        "nodes": nodes,
        "names": names,
        "stations": graph_stations,
        "adj_list": adj_list,
        "edge_paths": edge_paths,
        "_removed_edges": [],
        "node_ids": node_ids,
        "kd_tree": kd_tree
    }

    print(f"⏳ Đang nén Data và lưu ra file {pkl_path}...")
    with open(pkl_path, "wb") as f:
        pickle.dump(data_to_save, f)

    print(f"🚀 HOÀN TẤT XUẤT SẮC! Đã lưu {len(nodes)} điểm (gồm {len(graph_stations)} Ga) vào file .pkl.")

if __name__ == "__main__":
    build_and_save_data()