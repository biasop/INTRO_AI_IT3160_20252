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