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
        if start in graph.obstacles or goal in graph.obstacles:
            return 0, None
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
        if start in graph.obstacles or goal in graph.obstacles:
            return 0, None
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
            if current == goal:
                path = self.reconstruct_path(start, goal, came_from)
                distance = g_score[goal]
                return count_node, distance, path

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
        return count_node, None, None






