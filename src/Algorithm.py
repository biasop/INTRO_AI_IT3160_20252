from abc import ABC, abstractmethod
from distutils import dist
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
            if u in graph.adj_list:
                for neighbor_id, cost in graph.adj_list[u]:
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
            for neighbor in graph.adj_list[current]:
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
            for neighbor in graph.adj_list[current]:
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

        # Để kiểm tra nhanh node đã có trong hàng đợi chưa
        open_set = {start}

        came_from = {}

        # g_score: Chi phí thực tế từ start đến node hiện tại
        g_score = {node: float('inf') for node in graph.nodes}
        g_score[start] = 0

        # f_score: g_score + h_score
        f_score = {node: float('inf') for node in graph.nodes}

        # Lấy tọa độ mục tiêu để tính heuristic
        goal_lat, goal_lon = graph.nodes[goal]
        start_lat, start_lon = graph.nodes[start]

        # Tính toán f ban đầu bằng hàm haversine của graph
        f_score[start] = graph.haversine(start_lat, start_lon, goal_lat, goal_lon)

        while not open_queue.empty():
            # Lấy node có f_score thấp nhất
            _, current = open_queue.get()
            count_node += 1

            if current == goal:
                # Trả về: count_node, distance, path
                path = self.reconstruct_path(start, goal, came_from)
                distance = g_score[goal]
                return count_node, distance, path

            # Duyệt các láng giềng từ adj_list: [(neighbor_id, weight), ...]
            for neighbor, weight in graph.adj_list.get(current, []):
                tentative_g_score = g_score[current] + weight

                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score

                    # Tính Heuristic: Haversine từ neighbor tới goal
                    n_lat, n_lon = graph.nodes[neighbor]
                    h_val = graph.haversine(n_lat, n_lon, goal_lat, goal_lon)

                    f_score[neighbor] = g_score[neighbor] + h_val

                    if neighbor not in open_set:
                        open_queue.put((f_score[neighbor], neighbor))
                        open_set.add(neighbor)

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

            for neighbor, weight in graph.adj_list.get(current, []):
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
        for u in graph.adj_list:
            for v, w in graph.adj_list[u]:
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
            for neighbor, weight in graph.adj_list.get(current, []):
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

                    # Đánh dấu đã duyệt xong
                    closed_set.add(current)

                    # Duyệt qua các láng giềng
                    for neighbor, weight in graph.adj_list.get(current, []):
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
        pass

class BidirectionalDijkstra(Algorithm):
    def __init__(self):
        super().__init__()
    def run(self, start, goal, graph):
        pass







