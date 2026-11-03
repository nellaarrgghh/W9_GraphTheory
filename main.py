import argparse
from collections import deque
from pathlib import Path


class _Edge:
    def __init__(self, tail, head, depth):
        self.tail = tail
        self.head = head
        self.low = depth
        self.second = depth
        self.lowest_return = None
        self.link = None
        self.bottom = 0


class _Interval:
    def __init__(self, edge=None):
        # A same-side chain of return edges, from high down to low via link.
        self.low = edge
        self.high = edge

    def conflicts(self, edge):
        return self.high is not None and self.high.low > edge.low

    def append(self, other):
        if other.low is None:
            return
        if self.low is None:
            self.high = other.high
        else:
            self.low.link = other.high
        self.low = other.low


class _Conflict:
    def __init__(self, edge=None):
        # The two intervals must be on opposite sides; either can be empty.
        self.left = _Interval()
        self.right = _Interval(edge)

    def swap(self):
        self.left, self.right = self.right, self.left

    def lowest(self):
        if self.left.low is None:
            return self.right.low.low
        if self.right.low is None:
            return self.left.low.low
        return min(self.left.low.low, self.right.low.low)


class _LeftRight:
    def __init__(self, graph):
        self.graph = graph
        self.depth = [-1] * len(graph)
        self.parent = [None] * len(graph)
        self.outgoing = [[] for _ in graph]
        self.conflicts = []

    def orient(self, root):
        self.depth[root] = 0
        frames = [(root, iter(self.graph[root]))]
        while frames:
            vertex, neighbors = frames[-1]
            neighbor = next(neighbors, None)
            if neighbor is None:
                frames.pop()
                edge = self.parent[vertex]
                if edge is not None:
                    self.record_lowpoints(edge)
                continue

            if self.depth[neighbor] == -1:
                edge = _Edge(vertex, neighbor, self.depth[vertex])
                self.outgoing[vertex].append(edge)
                self.parent[neighbor] = edge
                self.depth[neighbor] = self.depth[vertex] + 1
                frames.append((neighbor, iter(self.graph[neighbor])))
            elif self.depth[neighbor] < self.depth[vertex]:
                parent = self.parent[vertex]
                if parent is not None and neighbor == parent.tail:
                    continue
                edge = _Edge(vertex, neighbor, self.depth[vertex])
                edge.low = self.depth[neighbor]
                self.outgoing[vertex].append(edge)
                self.record_lowpoints(edge)

    def record_lowpoints(self, edge):
        parent = self.parent[edge.tail]
        if parent is None:
            return
        # Keep two distinct lowest ancestor depths; the tail depth is a sentinel.
        if edge.low < parent.low:
            parent.second = min(parent.low, edge.second)
            parent.low = edge.low
        elif edge.low > parent.low:
            parent.second = min(parent.second, edge.low)
        else:
            parent.second = min(parent.second, edge.second)

    def order_edges(self):
        # Nesting depth is 2*low, plus one for a chordal subtree. Its bounded
        # integer range permits linear-time ordering instead of comparison sort.
        buckets = [[] for _ in range(2 * len(self.graph))]
        for edges in self.outgoing:
            for edge in edges:
                nesting = 2 * edge.low + (edge.second < self.depth[edge.tail])
                buckets[nesting].append(edge)
        self.outgoing = [[] for _ in self.graph]
        for bucket in buckets:
            for edge in bucket:
                self.outgoing[edge.tail].append(edge)

    def merge_constraints(self, edge, parent):
        merged = _Conflict()
        # First collect the current subtree's returns. They must admit one
        # common side until they reach the parent's lowest return.
        while len(self.conflicts) > edge.bottom:
            pair = self.conflicts.pop()
            if pair.left.low is not None:
                pair.swap()
            if pair.left.low is not None:
                return False
            if pair.right.low.low > parent.low:
                merged.right.append(pair.right)
            else:
                pair.right.low.link = parent.lowest_return

        # Earlier sibling subtrees can force these returns onto opposite sides.
        while self.conflicts:
            pair = self.conflicts[-1]
            if not (pair.left.conflicts(edge) or pair.right.conflicts(edge)):
                break
            self.conflicts.pop()
            if pair.right.conflicts(edge):
                pair.swap()
            if pair.right.conflicts(edge):
                return False
            merged.right.append(pair.right)
            merged.left.append(pair.left)

        if merged.left.low is not None or merged.right.low is not None:
            self.conflicts.append(merged)
        return True

    def integrate(self, edge):
        vertex = edge.tail
        if edge.low >= self.depth[vertex]:
            return True
        parent = self.parent[vertex]
        if edge is self.outgoing[vertex][0]:
            parent.lowest_return = edge.lowest_return
            return True
        return self.merge_constraints(edge, parent)

    def trim_returns(self, edge):
        # Returns ending at the parent vertex impose no constraints above it.
        vertex = edge.tail
        while self.conflicts and self.conflicts[-1].lowest() == self.depth[vertex]:
            self.conflicts.pop()
        if self.conflicts:
            pair = self.conflicts[-1]
            for interval, other in ((pair.left, pair.right), (pair.right, pair.left)):
                while interval.high is not None and interval.high.head == vertex:
                    interval.high = interval.high.link
                if interval.high is None and interval.low is not None:
                    interval.low.link = other.low
                    interval.low = None

        if edge.low < self.depth[vertex]:
            pair = self.conflicts[-1]
            left, right = pair.left.high, pair.right.high
            # Link to the highest surviving return for later iterative trimming.
            if left is not None and (right is None or left.low > right.low):
                edge.link = left
            else:
                edge.link = right

    def test_component(self, root):
        frames = [(root, 0)]
        while frames:
            vertex, index = frames[-1]
            if index == len(self.outgoing[vertex]):
                frames.pop()
                parent = self.parent[vertex]
                if parent is not None:
                    self.trim_returns(parent)
                    if not self.integrate(parent):
                        return False
                continue

            edge = self.outgoing[vertex][index]
            frames[-1] = (vertex, index + 1)
            edge.bottom = len(self.conflicts)
            if self.parent[edge.head] is edge:
                frames.append((edge.head, 0))
            else:
                edge.lowest_return = edge
                self.conflicts.append(_Conflict(edge))
                if not self.integrate(edge):
                    return False
        return True


def left_right(graph: list[set[int]]) -> bool:
    """Brandes's Left-Right test: O(n + m) time and space.

    The input must be a symmetric, loop-free adjacency list with vertices 0..n-1.
    Disconnected graphs and isolated vertices are supported; input is not changed.
    """
    size = len(graph)
    if size < 3:
        return True
    if sum(map(len, graph)) // 2 > 3 * size - 6:
        return False

    state = _LeftRight(graph)
    roots = []
    for vertex in range(size):
        if state.depth[vertex] == -1:
            roots.append(vertex)
            state.orient(vertex)
    state.order_edges()
    for root in roots:
        if not state.test_component(root):
            return False
    return True


def _edge(u, v):
    return (min(u, v), max(u, v))


def _blocks(graph):
    # Each block can be embedded separately at its articulation vertices.
    depth = [-1] * len(graph)
    low = [0] * len(graph)
    parent = [-1] * len(graph)
    pending_edges = []
    for root in range(len(graph)):
        if depth[root] != -1:
            continue
        depth[root] = low[root] = 0
        stack = [(root, iter(graph[root]))]
        while stack:
            u, neighbors = stack[-1]
            v = next(neighbors, None)
            if v is None:
                stack.pop()
                p = parent[u]
                if p != -1:
                    low[p] = min(low[p], low[u])
                    if low[u] >= depth[p]:
                        block = []
                        while pending_edges:
                            edge = pending_edges.pop()
                            block.append(edge)
                            if edge == (p, u):
                                break
                        yield block
                continue
            if depth[v] == -1:
                parent[v] = u
                depth[v] = low[v] = depth[u] + 1
                pending_edges.append((u, v))
                stack.append((v, iter(graph[v])))
            elif v != parent[u] and depth[v] < depth[u]:
                low[u] = min(low[u], depth[v])
                pending_edges.append((u, v))


def _find_cycle(graph):
    root = next(iter(graph))
    parent = {root: None}
    depth = {root: 0}
    stack = [(root, iter(sorted(graph[root])))]
    while stack:
        u, neighbors = stack[-1]
        v = next(neighbors, None)
        if v is None:
            stack.pop()
        elif v not in parent:
            parent[v] = u
            depth[v] = depth[u] + 1
            stack.append((v, iter(sorted(graph[v]))))
        elif v != parent[u] and depth[v] < depth[u]:
            cycle = [u]
            while cycle[-1] != v:
                cycle.append(parent[cycle[-1]])
            return cycle
    raise ValueError('A nontrivial biconnected block must contain a cycle')


def _segments(graph, vertices, edges):
    segments = []
    unseen = set(graph) - vertices
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        inside = {start}
        attachments = set()
        stack = [start]
        while stack:
            u = stack.pop()
            for v in graph[u]:
                if v in vertices:
                    attachments.add(v)
                elif v in unseen:
                    unseen.remove(v)
                    inside.add(v)
                    stack.append(v)
        segments.append((inside, attachments))

    # An unembedded edge between two embedded vertices is also a segment.
    for u in sorted(vertices):
        for v in sorted(graph[u] & vertices):
            if u < v and (u, v) not in edges:
                segments.append((set(), {u, v}))
    return segments


def _segment_path(graph, inside, attachments):
    start, end = sorted(attachments)[:2]
    previous = {start: None}
    queue = deque([start])
    while queue:
        u = queue.popleft()
        for v in sorted(graph[u]):
            if v in previous or (v not in inside and v != end):
                continue
            # A component segment must enter its interior, not use a chord.
            if inside and u == start and v == end:
                continue
            previous[v] = u
            if v == end:
                path = [end]
                while path[-1] != start:
                    path.append(previous[path[-1]])
                return path[::-1]
            queue.append(v)
    raise ValueError('Segment attachments must be joined through its interior')


def _embed_block(graph):
    cycle = _find_cycle(graph)
    vertices = set(cycle)
    edges = {_edge(cycle[i - 1], cycle[i]) for i in range(len(cycle))}
    # The initial cycle has two faces, including the outer face.
    states = [([cycle, cycle[::-1]], vertices, edges)]
    while states:
        faces, vertices, edges = states.pop()
        segments = _segments(graph, vertices, edges)
        if not segments:
            return True

        best = None
        best_faces = None
        for inside, attachments in segments:
            possible = [i for i, face in enumerate(faces) if attachments.issubset(face)]
            if not possible:
                break
            if best_faces is None or len(possible) < len(best_faces):
                best = (inside, attachments)
                best_faces = possible
        else:
            inside, attachments = best
            path = _segment_path(graph, inside, attachments)
            added_edges = {_edge(u, v) for u, v in zip(path, path[1:])}
            # Try every admissible face, so a failed choice is not a false NO.
            for index in reversed(best_faces):
                face = faces[index]
                a, b = face.index(path[0]), face.index(path[-1])
                if a > b:
                    path = path[::-1]
                    a, b = b, a
                first = face[a:b + 1] + path[-2:0:-1]
                second = face[b:] + face[:a + 1] + path[1:-1]
                new_faces = faces[:index] + [first, second] + faces[index + 1:]
                states.append((new_faces, vertices | set(path), edges | added_edges))
    return False


def demoucron(graph: list[set[int]]) -> bool:
    """Demoucron-style face insertion with backtracking, not polynomial-time DMP.

    Input follows the same adjacency-list contract as left_right. Search can take
    combinatorial time; use Left-Right for large graphs. Input is not changed.
    """
    for edges in _blocks(graph):
        if len(edges) == 1:
            continue  # A bridge always has a planar drawing.
        block = {}
        for u, v in edges:
            block.setdefault(u, set()).add(v)
            block.setdefault(v, set()).add(u)
        if len(edges) > 3 * len(block) - 6:
            return False
        if not _embed_block(block):
            return False
    return True


def _add_edge(graph, u, v):
    n = len(graph)
    if not (0 <= u < n and 0 <= v < n):
        raise ValueError(f'Edge {u} {v} has a vertex outside 0..{n - 1}')
    if u == v or v in graph[u]:
        return False
    graph[u].add(v)
    graph[v].add(u)
    return True


def _read_count(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value >= 0:
                return value
        except ValueError:
            pass
        print('Please enter one non-negative integer, for example: 6')


def read_interactive():
    print('Enter an undirected graph. Vertex labels start at 0.')
    print('Each edge is two labels separated by a space, for example: 0 1')
    print('Press Ctrl+C to cancel. Loops and duplicate edges are ignored.')
    n = _read_count('Number of vertices: ')
    while True:
        m = _read_count('Number of edges: ')
        if n > 0 or m == 0:
            break
        print('A graph with no vertices must have 0 edges.')
    graph = [set() for _ in range(n)]
    for index in range(m):
        while True:
            try:
                parts = input(f'Edge {index + 1}/{m} (u v): ').split()
                if len(parts) != 2:
                    raise ValueError('Enter exactly two integers, for example: 0 1')
                try:
                    u, v = map(int, parts)
                except ValueError:
                    raise ValueError('Enter exactly two integers, for example: 0 1') from None
                if not _add_edge(graph, u, v):
                    print('Self-loop or duplicate ignored; this input line still counts.')
                break
            except ValueError as error:
                print(error)
    return graph


def read_graph(path):
    """Read n m followed by m undirected edges; vertex labels start at zero."""
    lines = []
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        line = line.split('#', 1)[0].strip()
        if line:
            lines.append(line)
    if not lines:
        raise ValueError('Input is empty; expected n m on the first line')
    try:
        numbers = [list(map(int, line.split())) for line in lines]
    except ValueError:
        raise ValueError('Vertex counts and labels must be integers') from None
    if any(len(row) != 2 for row in numbers):
        raise ValueError('Each nonempty line must contain exactly two integers')
    n, m = numbers[0]
    if n < 0 or m < 0:
        raise ValueError('Vertex and edge counts cannot be negative')
    if len(numbers) - 1 != m:
        raise ValueError(f'Expected {m} edge lines, found {len(numbers) - 1}')
    graph = [set() for _ in range(n)]
    for u, v in numbers[1:]:
        _add_edge(graph, u, v)
    return graph


def main():
    parser = argparse.ArgumentParser(description='Compare two planarity checks')
    parser.add_argument('input', type=Path, nargs='?',
                        help='Optional graph file; omit it to enter a graph live')
    parser.add_argument('--algorithm', choices=['both', 'lr', 'dmp'], default='both',
                        help='both (default), Left-Right, or Demoucron')
    args = parser.parse_args()
    try:
        graph = read_graph(args.input) if args.input else read_interactive()
    except (EOFError, KeyboardInterrupt):
        parser.exit(1, '\nInput cancelled. Run again to enter a complete graph.\n')
    except (OSError, ValueError) as error:
        parser.error(str(error))

    print(f'Input: {args.input.name if args.input else "interactive"}')
    print(f'Vertices: {len(graph)}')
    print(f'Edges: {sum(map(len, graph)) // 2}')
    results = []
    for key, label, check in [('lr', 'Left-Right', left_right),
                              ('dmp', 'Demoucron', demoucron)]:
        if args.algorithm in ('both', key):
            result = check(graph)
            results.append(result)
            print(f'{label}: {"PLANAR" if result else "NON-PLANAR"}')
    if len(results) == 2 and results[0] != results[1]:
        raise RuntimeError('The algorithms disagree; check the implementations')


if __name__ == '__main__':
    main()
