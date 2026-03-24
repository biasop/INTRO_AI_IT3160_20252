from abc import ABC, abstractmethod
from queue import PriorityQueue, Queue
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


class DFS(Algorithm):
    def __init__(self, graph=None):
        super().__init__()
        self.graph = graph

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
        print(graph.names[start],graph.names[goal])
        while open_set:
            count_node += 1
            current = open_set.pop()
            if current == goal:
                return count_node, self.reconstruct_path(start, goal, came_from)
            for neighbor in graph.adj_list[current]:
                print(neighbor)
                neighbor_id = neighbor[0]
                if neighbor_id in closed:
                    continue
                closed.add(neighbor)
                came_from[neighbor] = current
                open_set.append(neighbor)
        return count_node, None