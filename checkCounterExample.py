import random
import time
import os
import glob
from collections import defaultdict
import itertools

from subgraphChecks import checkSubgraphConstraints


def get_perfect_matchings(edge_list):
    def get_edges_of_vertices(edge_list, vertices):
        return [edge for edge in edge_list if set(edge[:2]).issubset(vertices)]

    matchings_set = set()

    for edge1 in edge_list:
        subgraph1 = get_edges_of_vertices(edge_list, set(range(6)) - set(edge1[:2]))
        for edge2 in subgraph1:
            subgraph2 = get_edges_of_vertices(subgraph1, set(range(6)) - set(edge1[:2]) - set(edge2[:2]))
            for edge3 in subgraph2:
                # Sorting the edges to avoid permutations being considered as separate matchings
                matching = tuple(sorted([edge1, edge2, tuple(edge3)]))
                matchings_set.add(matching)

    return [list(matching) for matching in matchings_set]


def get_ivc(perfect_matching):
    vertex_colors = [None] * 6
    for edge in perfect_matching:
        idxA, idxB, colA, colB = edge
        vertex_colors[idxA] = colA
        vertex_colors[idxB] = colB
    return vertex_colors


def count_ivc(perfect_matchings):
    # Initialize the counts to 0 for all possible IVCs
    all_possible_ivcs = defaultdict(int)
    for ivc in itertools.product(range(3), repeat=6):
        all_possible_ivcs[ivc] = 0

    # Count the IVCs in the given perfect matchings
    for pm in perfect_matchings:
        ivc = tuple(get_ivc(pm))
        all_possible_ivcs[ivc] += 1

    return all_possible_ivcs


def ivc_conditions(edges):
    # None non-monochromatic IVC can exist only once.
    # Monochromatic IVCs must exist at least once

    # True: Fulfulls condition
    # False: cannot be a counter-example
    perfect_matchings = get_perfect_matchings(edges)
    result = count_ivc(perfect_matchings)
    for ivc, count in result.items():
        #print(f"IVC {ivc} appears {count} times.")

        if len(set(ivc))==1:
            # monochromatic IVC needs to exist at least once:
            if count==0:
                #print(f"Monochromatic IVC with color={ivc[0]} doesnt exist.")
                return False
        else:
            # non-monochromatic IVC cannot exist exactly once:
            if count==1:
                #print(f"Non-Monochromatic IVC with color={ivc} exist exactly once.")
                return False

    return True


def checkGraph(vertices, colors, edges):
    if not ivc_conditions(edges):
        return False
    return checkSubgraphConstraints(vertices, colors, edges)


def randomGraph(full_edge_set, edge_probability):
    edges = set()
    for edge in full_edge_set:
        if random.random() < edge_probability:
            edges.add(edge)
    return edges

def randomAddEdges(edges, n, full_edge_set):
    # Note: modifies edges set in place
    missing_edges = full_edge_set - edges
    if len(missing_edges) < n:
        edges.update(missing_edges)
    else:
        subset = random.sample(list(missing_edges), n)
        edges.update(subset)

def randomRemoveEdges(edges, n):
    # Note: modifies edges set in place
    if len(edges) < n:
        edges = set()
    else:
        subset = random.sample(list(edges), n)
        edges.difference_update(subset)


directory="results"
if not os.path.exists(directory):
    os.makedirs(directory)


while True:
    vertices = list(range(6))
    colors = list(range(3))

    all_edges = set()
    for n1,n2 in itertools.combinations(vertices, 2):
        for c1,c2 in itertools.product(colors, repeat=2):
            all_edges.add((n1,n2,c1,c2))

    CURR_ID=random.randint(10000000, 99999999)

    all_min_graphs=[]

    min_graph=[]
    min_graph_len=666

    while True:

        # first try to randomly generate a graph that passes all the checks
        attempts = 1
        edges = randomGraph(all_edges, 0.5)
        while not checkGraph(vertices, colors, edges):
            attempts +=1
            if attempts % 100 == 0:
                print(f"... {attempts} attempts")
            if random.random() < 0.0001:
                print("Start completely from scratch")
                edges = randomGraph(all_edges, 0.5)
            elif random.random() < 0.5:
                randomAddEdges(edges, random.randint(1,5), all_edges)
            else:
                randomRemoveEdges(edges, random.randint(1,5))
        print(f"Found a graph in {attempts} attempts")

        # -- previously, sometimes start from a known good graph?
        # turn that off for now
        """
        else:
            if random.random()>0.2:
                edges=min_graph[:]
            else:
                edges=random.choice(all_min_graphs)[:]

        res=True
        if min_graph_len!=666 and checkGraph(vertices, colors, edges) == False:
            print("MISTAKE")
            for _ in range(10):
                time.sleep(1)
        """

        # try to randomly minimize the graph
        while True:

            if len(edges)<min_graph_len:
                min_graph = list(edges)
                min_graph_len=len(edges)
                #print(min_graph)
                #print(f'Current minimum length: {min_graph_len}')

                path = os.path.join("results", f"solution{len(min_graph)}_{CURR_ID}.txt")
                did_write=False
                while not did_write:
                    try:
                        with open(path, 'w') as file:
                            file.write(f"{min_graph}")
                        pattern = os.path.join(directory, f"solution*_{CURR_ID}.txt")

                        # Get a list of matching filenames
                        files_to_check = glob.glob(pattern)

                        for file in files_to_check:
                            # Extract the XXX number from the filename
                            number = int(file.split("solution")[1].split("_")[0])

                            # Check if it's not the length of min_graph
                            if number != len(min_graph):
                                os.remove(file)

                        did_write=True
                    except:
                        time.sleep(0.1)

                all_min_graphs.append(min_graph)

            else:
                #print(f'    Current length: {len(edges)} (best: {min_graph_len})')
                pass

            num_elements=random.choice([1,2,3,4])
            randomRemoveEdges(edges, num_elements)

            res = checkGraph(vertices, colors, edges)
            if not res:
                break

