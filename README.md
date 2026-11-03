# Week 9: Planarity Check

Informatics ITS Graph Theory class Group 6

| Name | NRP |
| --- | --- |
| Naila Sa'ada Cahyani | 5025251258 |
| Lina Fatima Azzahra Badr | 5025251168 |

---

## A. Hopcroft-Tarjan Planarity Algorithm (Left-Right Planarity Test)

### 1. Short explanation about algorithm
The **Hopcroft-Tarjan (Left-Right) Planarity Test** is an efficient linear-time algorithm to determine whether an undirected graph is planar:
- **DFS Tree Orientation**: The algorithm performs Depth-First Search (DFS) to build a DFS palm tree (spanning tree edges oriented downwards and back edges oriented upwards towards ancestors).
- **Lowpoint Calculation**: For each edge, two lowest reachable ancestor depths (`low` and `second`) are computed to order edge traversal and handle return edges systematically.
- **Left-Right Constraint Resolution**: A planar graph requires that all back edges and subtrees can be placed either on the left or the right side of the DFS tree path without crossing each other. The algorithm maintains intervals of return edges on a stack, resolving pairwise conflict constraints as subtrees finish.
- **Complexity**: Runs in strictly **$O(V + E)$** linear time and space using explicit stacks and bucket-ordered nesting depths without comparison sorting.
- **Early Rejection**: Applies Euler's planar inequality ($e \le 3v - 6$ for $v \ge 3$) to quickly filter out dense non-planar graphs before tree decomposition.

### 2. Prerequisite to run the code, if any
- **Python**: Python 3.10 or newer.
- **Dependencies**: None. The implementation uses Python's standard library (`argparse`, `collections`, `pathlib`).

### 3. Instructions to run the code
Ensure your terminal is inside the `W9_Tegraf` directory:

```sh
cd W9_Tegraf
```

#### Run with sample input files:
```sh
# Run Hopcroft-Tarjan (Left-Right) on a planar sample
python main.py samples/cube.txt --algorithm lr

# Run Hopcroft-Tarjan (Left-Right) on non-planar samples
python main.py samples/k5.txt --algorithm lr
python main.py samples/k33.txt --algorithm lr
```

#### Run interactively:
```sh
python main.py --algorithm lr
```
Follow the interactive prompts to enter the number of vertices, edges, and each edge:
```text
Number of vertices: 4
Number of edges: 4
Edge 1/4 (u v): 0 1
Edge 2/4 (u v): 1 2
Edge 3/4 (u v): 2 3
Edge 4/4 (u v): 3 0
```

### 4. Result of sample run

#### Sample 1: Cube Graph (`samples/cube.txt`)
```text
$ python main.py samples/cube.txt --algorithm lr
Input: cube.txt
Vertices: 8
Edges: 12
Left-Right: PLANAR
```

#### Sample 2: Complete Graph $K_5$ (`samples/k5.txt`)
```text
$ python main.py samples/k5.txt --algorithm lr
Input: k5.txt
Vertices: 5
Edges: 10
Left-Right: NON-PLANAR
```

#### Sample 3: Complete Bipartite Graph $K_{3,3}$ (`samples/k33.txt`)
```text
$ python main.py samples/k33.txt --algorithm lr
Input: k33.txt
Vertices: 6
Edges: 9
Left-Right: NON-PLANAR
```

#### Summary of Sample Results:
| Input File | Vertices ($V$) | Edges ($E$) | Result |
| :--- | :---: | :---: | :---: |
| `samples/cube.txt` | 8 | 12 | **PLANAR** |
| `samples/disconnected.txt` | 7 | 5 | **PLANAR** |
| `samples/k5.txt` | 5 | 10 | **NON-PLANAR** |
| `samples/k33.txt` | 6 | 9 | **NON-PLANAR** |
| `samples/subdivided_k33.txt` | 8 | 11 | **NON-PLANAR** |

---

## B. [Algorithm Name]

### 1. Short explanation about algorithm

### 2. Prerequisite to run the code, if any

### 3. Instructions to run the code

### 4. Result of sample run


---

## AI Usage Disclosure

### AI Involved:
1. `https://share.gemini.google/O2yu7Q5xatbT`
2. ...
