import math
import pickle
from pathlib import Path
import xml.etree.ElementTree as ET
import re
from scipy.spatial import KDTree

# ==========================================
# CẤU HÌNH ĐƯỜNG DẪN TƯƠNG ĐỐI
# ==========================================
current_dir = Path(__file__).parent
osm_path = current_dir.parent / "res" / "export.osm"
pkl_path = current_dir.parent / "res" / "mrt_graph.pkl" 

#lấy stop từ osm (ĐÃ XONG)

def clean_station_name(name):
    if not name: return ""
    name = name.lower()
    
    # 1. Xóa các loại Exit
    name = re.sub(r'[-\s]*exi?xt?\s+[a-z0-9]+', '', name)
    name = re.sub(r'\bexit\b.*', '', name)
    
    # 2. Xóa hậu tố
    name = re.sub(r'\bstation\b', '', name)
    name = re.sub(r'\bmrt\b', '', name)
    name = re.sub(r'\blrt\b', '', name)
    name = re.sub(r'\bconnector\b', '', name)
    
    # 3. SỬA LỖI ĐẶC BIỆT: Xóa mọi thứ từ dấu mở ngoặc trở đi (Khắc phục lỗi mapper quên đóng ngoặc)
    name = re.sub(r'\(.*', '', name) 
    
    name = re.sub(r'[-/]', ' ', name) 
    name = name.strip()
    
    if len(name) <= 1: return ""
        
    name = re.sub(r'\s+', ' ', name)
    return name.strip().title()

def extract_stops_from_osm():
    tree = ET.parse(osm_path)
    root = tree.getroot()
    
    station_to_stops = {}
    stops = {}
    
    for node in root.findall('node'):
        tags = {tag.attrib['k']: tag.attrib['v'] for tag in node.findall('tag')}
        
        if tags.get('public_transport') == 'stop_position' or tags.get('railway') == 'stop':
            raw_name = tags.get('name', 'KHÔNG CÓ TÊN')
            name = clean_station_name(raw_name)
            node_id = node.attrib['id']
            coord = (float(node.attrib['lat']), float(node.attrib['lon']))
            
            if name not in station_to_stops:
                station_to_stops[name] = []
            
            station_to_stops[name].append(node_id)

            stops[node_id] = {
                'stop_name' : name,
                'coord' : coord
            }
                
    print(f"📊 Đã gộp {len(stops)} thành {len(station_to_stops)} cụm stop.")
    return station_to_stops, stops

# ==========================================
# HÀM TÍNH KHOẢNG CÁCH THỰC TẾ (ĐÃ XONG)
# ==========================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Bán kính Trái Đất (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def build_and_save_data():
    station_to_stops, stops = extract_stops_from_osm()
    print("⏳ Đang đọc file OSM thủ công để không bị mất ga...")
    tree = ET.parse(osm_path)
    root = tree.getroot()
    
    nodes = {}
    raw_adj_list = {}

    for node in root.findall('node'):
        node_id = node.attrib['id']
        lat = float(node.attrib['lat'])
        lon = float(node.attrib['lon'])
        nodes[node_id] = (lat, lon)
        raw_adj_list[node_id] = []
        
    for way in root.findall('way'):
        nd_refs = [nd.attrib['ref'] for nd in way.findall('nd')]
        for i in range(len(nd_refs) - 1):
            u = nd_refs[i]
            v = nd_refs[i+1]
            if u in nodes and v in nodes:
                cost = haversine(nodes[u][0], nodes[u][1], nodes[v][0], nodes[v][1])
                # File OSM đã có sẵn 2 way cho 2 chiều, nên ta chỉ lấy theo đúng chiều của way (directed graph)
                raw_adj_list[u].append((v, cost))

    graph_stations = {}
    for stop_id, info in stops.items():
        if stop_id in nodes:
            graph_stations[stop_id] = {
                'name': info['stop_name'],
                'coord': nodes[stop_id] 
            }
        else:
            print(f"  ⚠️ Cảnh báo: Stop '{info['stop_name']}' (ID: {stop_id}) bị văng ra khỏi đường ray. Đã bỏ qua!")

    print(f"✅ Giữ lại được {len(graph_stations)}/{len(stops)} Stop chuẩn 100% trên ray!")

    #tạo adjlist = BFS
    adj_list = {sid: [] for sid in graph_stations.keys()}
    for start_station in graph_stations.keys():
        visited = set([start_station])
        start_coord = nodes[start_station]
        queue = [(start_station, 0.0, [start_coord])]

        while queue:
            curr, curr_cost, path = queue.pop(0)

            # Đụng trúng ga (stop) tiếp theo
            if curr != start_station and curr in graph_stations:
                adj_list[start_station].append({
                    'target': curr,
                    'weight': curr_cost,
                    'type': 'rail',
                    'path': path # Path chứa toàn bộ tọa độ uốn lượn
                })
                continue 
            
            for neighbor, weight in raw_adj_list[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    neighbor_coord = nodes[neighbor]
                    queue.append((neighbor, curr_cost + weight, path + [neighbor_coord]))

    print("⏳ Đang tạo các kết nối đi bộ tại Ga Trung Chuyển...")
    TRANSFER_PENALTY = 0.5 
    
    for name, stop_ids in station_to_stops.items():
        if len(stop_ids) > 1:
            for i in range(len(stop_ids)):
                for j in range(i + 1, len(stop_ids)):
                    id_A, id_B = stop_ids[i], stop_ids[j]
                    
                    # Chỉ nối nếu cả 2 stop đều hợp lệ (nằm trong graph_stations)
                    if id_A in graph_stations and id_B in graph_stations:
                        coord_A = graph_stations[id_A]['coord']
                        coord_B = graph_stations[id_B]['coord']
                        
                        adj_list[id_A].append({
                            'target': id_B, 'weight': TRANSFER_PENALTY, 'type': 'transfer', 'path': [coord_A, coord_B]
                        })
                        adj_list[id_B].append({
                            'target': id_A, 'weight': TRANSFER_PENALTY, 'type': 'transfer', 'path': [coord_B, coord_A]
                        })

    print("⏳ Đang định dạng dữ liệu cho app (Graph.py)...")
    
    g_nodes = {}
    g_names = {}
    g_stations = {}
    g_adj_list = {}
    g_edge_paths = {}
    g_node_ids = []
    g_kd_tree_data = []

    for sid, info in graph_stations.items():
        g_nodes[sid] = info['coord']
        g_names[sid] = info['name']
        g_stations[sid] = info['coord']
        g_adj_list[sid] = []
        g_node_ids.append(sid)
        g_kd_tree_data.append(info['coord'])
        
    for u, edges in adj_list.items():
        for edge in edges:
            v = edge['target']
            cost = edge['weight']
            path = edge['path']
            g_adj_list[u].append((v, cost))
            g_edge_paths[(u, v)] = path
            
    kd_tree = KDTree(g_kd_tree_data) if g_kd_tree_data else None

    print("⏳ Đang nén dữ liệu và ghi ra file...")
    data_to_save = {
        "nodes": g_nodes,
        "names": g_names,
        "stations": g_stations,
        "adj_list": g_adj_list,
        "edge_paths": g_edge_paths,
        "_removed_edges": [],
        "node_ids": g_node_ids,
        "kd_tree": kd_tree
    }

    with open(pkl_path, "wb") as f:
        pickle.dump(data_to_save, f)

    print(f"🚀 HOÀN TẤT XUẤT SẮC! Đồ thị đã lưu tại: {pkl_path}")

if __name__ == "__main__":
    build_and_save_data()