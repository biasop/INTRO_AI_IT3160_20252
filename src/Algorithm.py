from abc import ABC, abstractmethod
from queue import PriorityQueue, Queue

from networkx.algorithms.shortest_paths.dense import reconstruct_path


class Algorithm(ABC):
    def __init__(self):
        pass
    @abstractmethod
    def run(self,start,goal,graph):
        pass
    def reconstruct_path(self, start, goal, came_from):
        path = []
        current = goal
        while current != start:
            path.append(current)
            if came_from.get(current) is None:
                return None
            current = came_from[current]
        path.append(start)
        return path[::-1]

    def calculate_path_distance(self, path,graph):
        """
        Tính tổng khoảng cách dựa trên trọng số (cost) có sẵn trong adj_list
        """
        if not path or len(path) < 2:
            return 0.0

        total_distance = 0.0

        for i in range(len(path) - 1):
            u = path[i]
            v = path[i + 1]
            # Tìm v trong danh sách hàng xóm của u để lấy cost
            found = False
            for neighbor_id, cost in graph.get_neighbors(u):
                if neighbor_id == v:
                    total_distance += cost
                    found = True
                    break

            if not found:
                # Trường hợp dự phòng nếu đồ thị có lỗi hoặc cạnh 1 chiều
                print(f"Cảnh báo: Không tìm thấy cạnh nối từ {u} đến {v}")

        return total_distance

class DFS(Algorithm):
    def __init__(self):
        super().__init__()

    def run(self, start, goal, graph):
        #if start in graph.obstacles or goal in graph.obstacles:
            #return 0, None
        count_node = 0
        came_from = {}
        open_set = []
        open_set.append(start)
        came_from[start] = None
        closed = set()
        closed.add(start)
        while open_set:
            count_node += 1
            current = open_set.pop()
            if current == goal:
                path = self.reconstruct_path(start,goal,came_from)
                distance = self.calculate_path_distance(path,graph)
                return count_node, distance, path
            for neighbor in graph.get_neighbors(current):
                neighbor_id = neighbor[0]
                if neighbor_id in closed:
                    continue
                closed.add(neighbor_id)
                came_from[neighbor_id] = current
                open_set.append(neighbor_id)
        return count_node, None
class BFS(Algorithm):
    def __init__(self):
        super().__init__()
    def run(self, start, goal, graph):
        #if start in graph.obstacles or goal in graph.obstacles:
            #return 0, None
        count_node = 0
        came_from = {}
        open_set = [start]
        came_from[start] = None
        closed = set()
        closed.add(start)
        while open_set:
            count_node +=1
            current = open_set.pop(0)
            if current == goal:
                path = self.reconstruct_path(start, goal, came_from)
                distance = self.calculate_path_distance(path,graph)
                return count_node , distance , path
            for neighbor in graph.get_neighbors(current):
                neighbor_id = neighbor[0]
                if neighbor_id in closed:
                    continue
                closed.add(neighbor_id)
                came_from[neighbor_id] = current
                open_set.append(neighbor_id)
        return count_node, None , None

class AStar(Algorithm):
    def __init__(self):
        super().__init__()

    def run(self, start, goal, graph):
        count_node = 0
        # Priority Queue: (chi_phi_tich_luy, node_id)
        # Bản chất: Nhặt giá trị chi_phi_tich_luy (g_score) nhỏ nhất lên đầu
        open_queue = PriorityQueue()
        open_queue.put((0, start))

        # Để theo dõi các node đã được chốt đường đi ngắn nhất (Lazy Deletion)
        closed_set = set()

        came_from = {}

        # g_score: Chi phí thực tế từ start đến node hiện tại
        g_score = {node: float('inf') for node in graph.nodes}
        g_score[start] = 0

        # Lấy tọa độ mục tiêu để tính heuristic
        goal_lat, goal_lon = graph.nodes[goal]
        start_lat, start_lon = graph.nodes[start]

        while not open_queue.empty():
            # Lấy node có f_score thấp nhất
            current_f, current = open_queue.get()
            
            # Lazy Deletion: Bỏ qua nếu node đã được chốt đường ngắn nhất
            if current in closed_set:
                continue
            
            closed_set.add(current)
            count_node += 1

            if current == goal:
                # Trả về: count_node, distance, path
                path = self.reconstruct_path(start, goal, came_from)
                distance = g_score[goal]
                return count_node, distance, path

            # Duyệt các láng giềng từ adj_list: [(neighbor_id, weight), ...]
            for neighbor, weight in graph.get_neighbors(current):
                tentative_g_score = g_score[current] + weight

                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score

                    # Tính Heuristic: Haversine từ neighbor tới goal
                    n_lat, n_lon = graph.nodes[neighbor]
                    h_val = graph.haversine(n_lat, n_lon, goal_lat, goal_lon)

                    # Đẩy thẳng vào Priority Queue, nếu trùng lặp thì Lazy Deletion sẽ lo
                    open_queue.put((tentative_g_score + h_val, neighbor))

        # Không tìm thấy đường
        return count_node, None, None


class Dijkstra(Algorithm):
    def __init__(self):
        super().__init__()
    def run(self, start, goal, graph):
        count_node  =0
        # Priority Queue: (chi_phi_tich_luy, node_id)
        # Bản chất: Nhặt giá trị chi_phi_tich_luy (g_score) nhỏ nhất lên đầu
        open_queue = PriorityQueue()
        open_queue.put((0, start))
        open_set = {start}
        came_from = {}

        g_score = {node: float('inf') for node in graph.nodes}
        g_score[start] = 0

        while not open_queue.empty():
            current_priority, current = open_queue.get()
            count_node += 1

            # Nếu giá trị lấy ra từ Queue đã cũ (lớn hơn g_score hiện tại), bỏ qua
            if current_priority> g_score[current]:
                continue

            for neighbor, weight in graph.get_neighbors(current):
                # Tính quãng đường mới qua node 'current'
                tentative_g_score = g_score[current] + weight

                # Nếu tìm thấy đường đi ngắn hơn đến 'neighbor'
                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score

                    # Đưa vào Priority Queue để xét các bước tiếp theo
                    # Priority Queue sẽ tự động sắp xếp để g_score nhỏ nhất lên đầu
                    open_queue.put((g_score[neighbor], neighbor))

                # Nếu duyệt hết mà không thấy đích
        if g_score[goal] == float('inf'):
            return count_node, None, None  # Thất bại, không có đường đi

            # Truy vết và trả về kết quả
        path = self.reconstruct_path(start, goal, came_from)
        distance = g_score[goal]

        return count_node, distance, path
    
class BellmanFord(Algorithm):
    def __init__(self):
        super().__init__()
    def run(self, start, goal, graph):
        #if start in graph.obstacles or goal in graph.obstacles:
            #return 0, None


        count_node =0
        dist = {node: float('inf') for node in graph.nodes}
        prev = {node: None for node in graph.nodes}
        dist[start] = 0

        edges = []
        # Lấy danh sách tất cả các cạnh từ adj_list để Bellman-Ford duyệt
        for u in graph.nodes:
            for v, w in graph.get_neighbors(u):
                edges.append((u, v, w))
        #repeat len(graph.nodes) - 1 times:
        # for all edges in graph.egdes update shortest path

        for _ in range(len(graph.nodes)-1):
            for u,v,w in edges:
                # for all edges in graph.egdes update shortest path
                #if u in graph.obstacles or v in graph.obstacles:
                    #continue  # Bỏ qua cạnh này
                count_node += 1
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    prev[v] = u

        # tao them 1 vong lap de check xem co duong di ngan nhat nao co trong so am vo cung (check toi uu, neu co khoa none)
        for u,v,w in edges:
            #if u in graph.obstacles or v in graph.obstacles:
                #continue  # Bỏ qua cạnh này
            count_node += 1
            if dist[u] + w < dist[v]:
                return count_node, None, None

        path = self.reconstruct_path(start, goal, prev)
        distance = dist[goal] if dist[goal] != float('inf') else None
        return count_node, distance, path



class UCS(Algorithm):
    #Nhìn ban đầu Dijkstra và UCS gần như là một vì đều lan truyền dựa trên g_score.
    # Điểm khác biệt duy nhất là điều kiện dừng:
    # UCS sẽ dừng lại ngay lập tức khi tìm ra đường đi tối ưu đến đỉnh Goal (mặc kệ phần còn lại của bản đồ),
    # còn Dijkstra truyền thống sẽ chạy đến cùng để tìm ra đường đi tối ưu đến toàn bộ các đỉnh trên đồ thị.
    def __init__(self):
        super().__init__()
    def run(self, start, goal, graph):
        #if start in graph.obstacles or goal in graph.obstacles:
            #return 0, None, None
        count_node = 0
        open_queue = PriorityQueue()
        open_queue.put((0, start))
        came_from = {}
        g_score = {node: float('inf') for node in graph.nodes}
        g_score[start] = 0
        open_set = {start}

        while not open_queue.empty():
            count_node += 1
            current_priority, current = open_queue.get()
            if current == goal:
                path = self.reconstruct_path(start, goal, came_from)
                distance = g_score[goal]
                return count_node, distance, path
            if current_priority > g_score[current]:
                continue
            for neighbor, weight in graph.get_neighbors(current):
                tentative_g_score = g_score[current] + weight

                # Nếu tìm được đường đi mới rẻ hơn
                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score

                    # Đưa vào hàng đợi với chi phí mới nhất
                    open_queue.put((g_score[neighbor], neighbor))

        return count_node, None, None


class Greedy(Algorithm):
    def __init__(self):
        super().__init__()
    def run(self, start, goal, graph):
        count_node = 0

        # Hàng đợi ưu tiên: (h_score, node_id)
        # Chỉ quan tâm đỉnh nào có vẻ gần đích nhất
        open_queue = PriorityQueue()
        came_from = {}

            # Tập hợp để tránh đi vào chu trình
        closed_set = set()
        open_set = {start}

            # Lấy tọa độ của đích để tính heuristic
        goal_lat, goal_lon = graph.nodes[goal]
        start_lat, start_lon = graph.nodes[start]

            # Khởi tạo heuristic cho điểm bắt đầu
        h_start = graph.haversine(start_lat, start_lon, goal_lat, goal_lon)
        open_queue.put((h_start, start))

        while not open_queue.empty():
            # Lấy ra đỉnh có h_score nhỏ nhất (gần đích nhất theo đường chim bay)
            _, current = open_queue.get()
            count_node += 1

            # ĐIỀU KIỆN DỪNG: Tìm thấy đích
            if current == goal:
                path = self.reconstruct_path(start, goal, came_from)
                # Vì Greedy không lưu g_score, ta dùng hàm hỗ trợ để tính lại tổng quãng đường
                distance = self.calculate_path_distance(path, graph)
                return count_node, distance, path

            #đánh dấu đã duyệt xong
            closed_set.add(current)

            # Duyệt qua các láng giềng
            for neighbor, weight in graph.get_neighbors(current):
                # Bỏ qua nếu đã duyệt rồi
                if neighbor in closed_set:
                    continue

            # Nếu là đỉnh mới, đưa vào hàng đợi chờ duyệt
                if neighbor not in open_set:
                    came_from[neighbor] = current
                    open_set.add(neighbor)

            # Tính Heuristic: Haversine từ láng giềng tới goal
                    n_lat, n_lon = graph.nodes[neighbor]
                    h_val = graph.haversine(n_lat, n_lon, goal_lat, goal_lon)

                    open_queue.put((h_val, neighbor))

            # Thất bại: Duyệt hết mà không tới được đích
        return count_node, None, None


class BidirectionalAstar(Algorithm):
    def __init__(self):
        super().__init__()

    def run(self, start, goal, graph):
        if start == goal: return 0, 0, [start]

        count_node = 0
        g_f, g_b = {start: 0}, {goal: 0}
        pq_f, pq_b = PriorityQueue(), PriorityQueue()

        goal_lat, goal_lon = graph.nodes[goal]
        start_lat, start_lon = graph.nodes[start]

        # f = g + h
        pq_f.put((graph.haversine(start_lat, start_lon, goal_lat, goal_lon), start))
        pq_b.put((graph.haversine(goal_lat, goal_lon, start_lat, start_lon), goal))

        parent_f, parent_b = {start: None}, {goal: None}
        best_dist = float('inf')
        mu = None
        
        # Xây dựng danh sách các cạnh đi VÀO mỗi node (Predecessors)
        # Bắt buộc phải dùng cho Backward Search trên đồ thị có hướng (đường tàu 1 chiều)
        incoming = {n: [] for n in graph.nodes}
        for u in graph.nodes:
            for v, w in graph.get_neighbors(u):
                incoming[v].append((u, w))

        closed_f = set()
        closed_b = set()

        while not pq_f.empty() and not pq_b.empty():
            # Forward Search
            _, u = pq_f.get()
            if u not in closed_f:
                closed_f.add(u)
                count_node += 1
    
                for v, w in graph.get_neighbors(u):
                    new_g = g_f[u] + w
                    if v not in g_f or new_g < g_f[v]:
                        g_f[v] = new_g
                        parent_f[v] = u
                        v_lat, v_lon = graph.nodes[v]
                        h = graph.haversine(v_lat, v_lon, goal_lat, goal_lon)
                        pq_f.put((new_g + h, v))
                        if v in g_b:
                            if g_f[v] + g_b[v] < best_dist:
                                best_dist = g_f[v] + g_b[v]
                                mu = v

            # Backward Search
            _, u = pq_b.get()
            if u not in closed_b:
                closed_b.add(u)
                count_node += 1
                # QUAN TRỌNG: Dùng incoming[u] thay vì graph.get_neighbors(u)
                for v, w in incoming[u]:
                    new_g = g_b[u] + w
                    if v not in g_b or new_g < g_b[v]:
                        g_b[v] = new_g
                        parent_b[v] = u
                        v_lat, v_lon = graph.nodes[v]
                        h = graph.haversine(v_lat, v_lon, start_lat, start_lon)
                        pq_b.put((new_g + h, v))
                        if v in g_f:
                            if g_f[v] + g_b[v] < best_dist:
                                best_dist = g_f[v] + g_b[v]
                                mu = v

            # Kiểm tra điều kiện kết thúc sớm
            if not pq_f.empty() and not pq_b.empty():
                if min(pq_f.queue[0][0], pq_b.queue[0][0]) >= best_dist:
                    break

        if mu is None: return count_node, None, None

        # Reconstruct path tương tự Dijkstra
        path_f, path_b = [], []
        curr = mu
        while curr is not None:
            path_f.append(curr)
            curr = parent_f[curr]
        path_f.reverse()
        curr = parent_b[mu]
        while curr is not None:
            path_b.append(curr)
            curr = parent_b[curr]

        return count_node, best_dist, path_f + path_b


from queue import PriorityQueue


class BidirectionalDijkstra(Algorithm):
    def __init__(self):
        super().__init__()

    def run(self, start, goal, graph):
        if start == goal: return 0, 0, [start]

        count_node = 0
        # Dữ liệu cho chiều đi xuôi (Forward)
        dist_f = {start: 0}
        pq_f = PriorityQueue()
        pq_f.put((0, start))
        parent_f = {start: None}

        # Dữ liệu cho chiều đi ngược (Backward)
        dist_b = {goal: 0}
        pq_b = PriorityQueue()
        pq_b.put((0, goal))
        parent_b = {goal: None}

        best_dist = float('inf')
        mu = None  # Điểm giao nhau tối ưu

        # Xây dựng danh sách các cạnh đi VÀO mỗi node (Predecessors)
        # Bắt buộc phải dùng cho Backward Search trên đồ thị có hướng
        incoming = {n: [] for n in graph.nodes}
        for u in graph.nodes:
            for v, w in graph.get_neighbors(u):
                incoming[v].append((u, w))

        while not pq_f.empty() and not pq_b.empty():
            # Phát triển bên Forward
            if not pq_f.empty():
                d, u = pq_f.get()
                count_node += 1
                if d <= dist_f.get(u, float('inf')):
                    for v, w in graph.get_neighbors(u):
                        if dist_f.get(v, float('inf')) > dist_f[u] + w:
                            dist_f[v] = dist_f[u] + w
                            parent_f[v] = u
                            pq_f.put((dist_f[v], v))
                            # Kiểm tra nếu nút này đã được chiều kia duyệt tới
                            if v in dist_b:
                                new_dist = dist_f[v] + dist_b[v]
                                if new_dist < best_dist:
                                    best_dist = new_dist
                                    mu = v

            # Phát triển bên Backward
            if not pq_b.empty():
                d, u = pq_b.get()
                count_node += 1
                if d <= dist_b.get(u, float('inf')):
                    # QUAN TRỌNG: Dùng incoming[u] thay vì graph.get_neighbors(u)
                    for v, w in incoming[u]:
                        if dist_b.get(v, float('inf')) > dist_b[u] + w:
                            dist_b[v] = dist_b[u] + w
                            parent_b[v] = u
                            pq_b.put((dist_b[v], v))
                            if v in dist_f:
                                new_dist = dist_f[v] + dist_b[v]
                                if new_dist < best_dist:
                                    best_dist = new_dist
                                    mu = v

            # Điều kiện dừng: Khi khoảng cách nhỏ nhất trong PQ lớn hơn quãng đường tốt nhất tìm được
            if not pq_f.empty() and not pq_b.empty():
                if pq_f.queue[0][0] + pq_b.queue[0][0] >= best_dist:
                    break

        if mu is None: return count_node, None, None

        # Tái tạo đường đi từ mu về 2 phía
        path_f = []
        curr = mu
        while curr is not None:
            path_f.append(curr)
            curr = parent_f[curr]
        path_f.reverse()

        path_b = []
        curr = parent_b[mu]
        while curr is not None:
            path_b.append(curr)
            curr = parent_b[curr]

        return count_node, best_dist, path_f + path_b






