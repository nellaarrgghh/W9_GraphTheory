import os
import sys
import networkx as nx

def load_graph_from_file(filepath):
    """
    Loads an undirected graph from a text file.
    Each line in the file represents an edge defined by two node identifiers 
    separated by spaces, commas, or tabs. Example: 0 1
    """
    G = nx.Graph()
    try:
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines or comment lines starting with '#'
                if not line or line.startswith('#'):
                    continue
                
                # Split line by whitespace or comma
                parts = line.replace(',', ' ').split()
                if len(parts) >= 2:
                    u, v = parts[0], parts[1]
                    G.add_edge(u, v)
                else:
                    print(f"Warning: Skipping malformed line {line_num}: '{line}'")
        return G
    except FileNotFoundError:
        print(f"Error: The input file '{filepath}' was not found.")
        sys.exit(1)

def run_planarity_check(filepath):
    print("=" * 60)
    print(f" Planarity Checker ")
    print("=" * 60)
    
    # Load graph dynamically from the input file
    print(f"-> Loading graph from: {filepath}")
    G = load_graph_from_file(filepath)
    
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    print(f"-> Graph Loaded Successfully!")
    print(f"   Vertices (V): {num_nodes}")
    print(f"   Edges (E):    {num_edges}")
    print("-" * 60)
    
    # Perform planarity test (Linear-time Left-Right / Boyer-Myrvold family algorithm)
    is_planar, result = nx.check_planarity(G, counterexample=True)
    
    if is_planar:
        print("PLANAR")
        print("Result: The graph can be drawn in a plane without edge crossings.")
        print("A valid planar embedding was successfully computed.")
    else:
        print("NON-PLANAR")
        print("Result: The graph is non-planar (contains a Kuratowski subgraph obstruction).")
        print(f"   - Obstruction Nodes: {result.number_of_nodes()}")
        print(f"   - Obstruction Edges: {result.number_of_edges()}")
        print(f"   - Obstruction Edges List: {list(result.edges())}")
    print("=" * 60)

if __name__ == "__main__":
    # Default target is the "inputs" folder, or a custom path passed via command line
    # Usage: python planarity_checker.py [inputs_folder_or_file.txt]
    target = "inputs"
    if len(sys.argv) > 1:
        target = sys.argv[1]
        
    # Check if target is a directory (folder) or a single file
    if os.path.isdir(target):
        print(f"\n📂 Scanning directory: '{target}/' for test cases...")
        txt_files = [os.path.join(target, f) for f in os.listdir(target) if f.endswith('.txt')]
        
        if not txt_files:
            print(f"No .txt test files found inside '{target}/'.")
        
        for file_path in sorted(txt_files):
            run_planarity_check(file_path)
            print("\n")
    else:
        run_planarity_check(target)