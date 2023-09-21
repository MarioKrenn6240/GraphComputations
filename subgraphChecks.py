
from collections import defaultdict
import itertools
import logging


def calcEdgesByVertex(edges):
    """
    returns  dict vertex -> set of edges incident on that vertex
    """
    d = defaultdict(set)
    for edge in edges:
        n1,n2,c1,c2 = edge
        d[n1].add(tuple(edge))
        d[n2].add(tuple(edge))
    return d


def calcColoredVertexPairing(edges):
    """
    returns  dict (n1, c1) -> set of (n2, c2) such that there is an edge [n1,n2,c1,c2]
    """
    d = defaultdict(set)
    for edge in edges:
        n1,n2,c1,c2 = edge
        d[(n1,c1)].add((n2,c2))
        d[(n2,c2)].add((n1,c1))
    return d


def degreeConstraint(colors, edgesByVertex):
    """
    check constraint from Rishi's result
    if |colors| >= 3:
      in skeleton graph, deg > 3, or there are no multi-edges
    """
    if len(colors) < 3:
        return True

    for v, edges in edgesByVertex.items():
        skeletonConnections = set((n1,n2) for n1,n2,c1,c2 in edges)
        if len(skeletonConnections) > 3:
            continue
        if len(skeletonConnections) < len(edges):
            logging.debug(f"degreeConstraint v={v}, {edges}")
            return False
    return True


def forbiddenStarA(colors, vertices, cVertexPairs):
    """
    Check for forbidden star subgraph of multi-color edges

    This is based on the 2^(n-1) colored vertex weight syzygy.

    For any vertex n1, and color c1
      consider the set V of vertices n2 such that the following edge exists
        (n1,n2,c1,c1) -- monochrome
      then there cannot be an star graph on vertices n1 and V such that:
          - all the edges are multi-colored
          - the central vertex is n1
          - the edges in the star all have color c1 associated with n1

    Note:
      If we just consider a star graph on all vertices,
        these are real forbidden subgraphs that cannot occur in a monochromatic
        graph with n=|vertices|, c=|colors|.
      Otherwise these are actually conditionally forbidden subgraphs,
      implications of the form:
        if edges X are not in the graph, then edges Y cannot be in the graph either.
    """
    if len(colors) < 2:
        return True

    # consider all possible n1,c1 for the center node of the star graph
    for cnode, cnodes in cVertexPairs.items():
        n1,c1 = cnode

        # first determine which vertices we need to consider for the star
        checkVertices = set()
        for n2 in vertices:
            if n2 == n1:
                continue
            if (n2,c1) in cnodes:
                checkVertices.add(n2)

        # If there are no vertices to check, we have the degenerate case:
        #   the "empty set" is always a subset of the edges.
        # This should not happen though, because it means there was no
        # monochrome c1 edge incident on vertex n1.
        if len(checkVertices) == 0:
            return False

        # determine if star subgraph exists
        vcolor = {} # vertex from V -> color
        for n2,c2 in cnodes:
            if (n2 in checkVertices) and (c2 != c1):
                vcolor[n2] = c2

        if len(vcolor) == len(checkVertices):
            logging.debug(f"starA n1={n1}, c1={c1}, {vcolor}")
            return False
    return True


def forbiddenStarB(colors, vertices, cVertexPairs):
    """
    Check for forbidden star subgraph of edges using at most two colors.

    This is based on the 2^n colored vertex weight syzygy.

    For any vertex n1, and distinct colors c1, c2,
      consider the set V of vertices n2 such that one of the following edges exists
        (n1,n2,c2,c2) -- monochrome
        (n1,n2,c1,c2) -- "reversed" multi-color, since it disagrees with center color
      then there cannot be an star graph on vertices n1 and V such that:
          - the star graph uses only colors != c2, and
          - the central vertex is n1
          - the edges in the star all have color c1 associated with n1

    Note:
      If we just consider a star graph on all vertices,
        these are real forbidden subgraphs that cannot occur in a monochromatic
        graph with n=|vertices|, c=|colors|.
      Otherwise these are actually conditionally forbidden subgraphs,
      implications of the form:
        if edges X are not in the graph, then edges Y cannot be in the graph either.

    The real forbidden subgraphs only apply to |colors| >= 3.
    However the conditionally forbidden subgraphs still apply to |colors| = 2.
    """
    if len(colors) < 2:
        return True

    # consider all possible n1,c1 for the center node of the star graph
    for cnode, cnodes in cVertexPairs.items():
        n1,c1 = cnode

        # consider all c2, which is a color the star must avoid
        #   and also (along with c1) determines which edge colors require a vertex to be included
        for c2 in colors:
            if c1 == c2:
                continue

            # first determine which vertices we need to consider for the star
            checkVertices = set()
            for n2 in vertices:
                if n2 == n1:
                    continue
                if ((n2,c2) in cnodes) or ((n2,c2) in cVertexPairs[(n1,c2)]):
                    checkVertices.add(n2)

            # if |colors| = 2, only the conditionally forbidden subgraphs apply
            if (len(colors) == 2) and (len(checkVertices) == len(vertices) - 1):
                continue

            # If there are no vertices to check, we have the degenerate case:
            #   the "empty set" is always a subset of the edges.
            # This should not happen though, because it means there was no
            # monochrome c2 edge incident on vertex n1.
            if len(checkVertices) == 0:
                return False

            # determine if star subgraph exists
            vcolor = {} # vertex from V -> color
            for n3,c3 in cnodes:
                if (n3 in checkVertices) and (c3 != c2):
                    vcolor[n3] = c3

            if len(vcolor) == len(checkVertices):
                logging.debug(f"starB n1={n1}, c1={c1}, {vcolor}")
                return False
    return True


def forbiddenStarC(colors, vertices, cVertexPairs):
    """
    Check for forbidden star subgraph with one edge disagreeing on central color

    This is based on the "reverse" case of the 2^n colored vertex weight syzygy.

    --- Writing out some of the details to help check the "conditionally" forbidden graphs.

    For example: {000000}-{111111} with edge*subgraph expansion on node 0
    would give the coefficient on {000000} as:
        -w0111*w0201*w0301*w0401*w0501
        -w0101*w0211*w0301*w0401*w0501
        -w0101*w0201*w0311*w0401*w0501
        -w0101*w0201*w0301*w0411*w0501
        -w0101*w0201*w0301*w0401*w0511
    chosing any one of those terms, and multplying all the coefficients by that,
    will end up cancelling the other terms, due to the 5-star of multi-color edges

    In the case where w0500 and w0510 are not in the graph,
    then consider: {000000}-{111110} with edge*subgraph expansion on node 0
    would give the coefficient on {000000} as:
        -w0111*w0201*w0301*w0401
        -w0101*w0211*w0301*w0401
        -w0101*w0201*w0311*w0401
        -w0101*w0201*w0301*w0411
    With w0500 not in the graph, then 4-star of multi-color edges is forbidden such
    that we can again take a term, multiply the coefficients by that,
    and it will end up cancelling the other terms.

    Similarly for considering w0400, w0410, w0500, w0510 not in the graph.

    ----

    For any vertex n1, and distinct colors c1, c2,
      consider the set V of vertices n2 such that one of the following edges exists
        (n1,n2,c1,c1) -- monochrome
        (n1,n2,c2,c1) -- "reversed" multi-color, since it disagrees with center color
      then there cannot be an star graph on vertices n1 and V such that:
          - the central vertex is n1
          - the star graph has exactly one edge (n1,n2,c2,c3) for some n2 in V and c3!=c1
          - all other edges, for n3 in V and n3!=n2, (n1,n3,c1,c4) with c4!=c1

    Note:
      If we just consider a star graph on all vertices,
        these are real forbidden subgraphs that cannot occur in a monochromatic
        graph with n=|vertices|, c=|colors|.
      Otherwise these are actually conditionally forbidden subgraphs,
      implications of the form:
        if edges X are not in the graph, then edges Y cannot be in the graph either.

    The real forbidden subgraphs only apply to |colors| >= 3.
    However the conditionally forbidden subgraphs still apply to |colors| = 2.
    """
    if len(colors) < 2:
        return True

    # consider all possible n1,c1 for the center node of the star graph
    for cnode, cnodes in cVertexPairs.items():
        n1,c1 = cnode

        # consider all c2, which is the 'alternate' color of the star central node
        #   and also (along with c1) determines which edge colors require a vertex to be included
        for c2 in colors:
            if c1 == c2:
                continue

            # first determine which vertices we need to consider for the star
            checkVertices = set()
            for n2 in vertices:
                if n2 == n1:
                    continue
                if ((n2,c1) in cnodes) or ((n2,c1) in cVertexPairs[(n1,c2)]):
                    checkVertices.add(n2)

            # if |colors| = 2, only the conditionally forbidden subgraphs apply
            if (len(colors) == 2) and (len(checkVertices) == len(vertices) - 1):
                continue

            # If there are no vertices to check, we have the degenerate case:
            #   the "empty set" is always a subset of the edges.
            # This should not happen though, because it means there was no
            # monochrome c1 edge incident on vertex n1.
            if len(checkVertices) == 0:
                return False

            # consider all n2, the edge which disagrees on the color of n1 in the star
            for n2,c3 in cVertexPairs[(n1,c2)]:
                if c3 == c1:
                    continue
                if n2 not in checkVertices:
                    continue

                # determine if star subgraph exists
                vcolor = {} # vertex from V -> color
                vcolor[n2] = c3
                for n3,c4 in cnodes:
                    if n3 == n2:
                        continue
                    if (n3 in checkVertices) and (c4 != c1):
                        vcolor[n3] = c4

                if len(vcolor) == len(checkVertices):
                    logging.debug(f"starC n1={n1}, c1={c1}, n2={n2}, {vcolor}")
                    return False
    return True


def colorCollapse(colors, fromColor, toColor, edges):
    """
    makes a new set of edges with any color labelled fromColor changed to the label toColor

    returns (newEdges, newColors)

    Note:
    this means the remaining colors may no longer be labelled from 0 to numColors-1,
    """
    newColors = list(colors)
    newColors.remove(fromColor)

    transformColor = {c:c for c in newColors}
    transformColor[fromColor] = toColor
    newEdges = set()
    for n1,n2,c1,c2 in edges:
        newEdges.add((n1,n2,transformColor[c1],transformColor[c2]))
    return (newEdges, newColors)


def _checkSubgraphConstraints(vertices, colors, edges):
    """
    Checks subgraph constraints for monochromatic graph
    Does not perform color collapse checks.

    returns True is all tests pass, else False
    """
    edgesByVertex = calcEdgesByVertex(edges)
    cVertexPairs = calcColoredVertexPairing(edges)

    if not degreeConstraint(colors, edgesByVertex):
        return False

    if not forbiddenStarA(colors, vertices, cVertexPairs):
        return False

    if not forbiddenStarB(colors, vertices, cVertexPairs):
        return False

    if not forbiddenStarC(colors, vertices, cVertexPairs):
        return False

    return True


def checkSubgraphConstraints(vertices, colors, edges):
    """
    Checks subgraph constraints for monochromatic graph

    returns True is all tests pass, else False
    """

    if not _checkSubgraphConstraints(vertices, colors, edges):
        return False

    # also check with color collapsing
    # with |colors|>3, it may be useful to do multiple rounds of this
    # just try collapsing once
    if len(colors) >= 3:
        for fromColor, toColor in itertools.permutations(colors, 2):
            newEdges, newColors = colorCollapse(colors, fromColor, toColor, edges)
            if not _checkSubgraphConstraints(vertices, newColors, newEdges):
                logging.debug(f"Failed check with color collapsing {fromColor} -> {toColor}")
                return False

    return True



# run some checks
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)

    # n=4 c=3 should pass checks
    vertices = list(range(4))
    colors = list(range(3))
    edges = [[0,1,0,0],[2,3,0,0],[0,2,1,1],[1,3,1,1],[0,3,2,2],[1,2,2,2]]
    assert checkSubgraphConstraints(vertices, colors, edges)

    # n=4 c=2 max edges
    vertices = list(range(4))
    colors = list(range(2))
    edges = [[0,1,0,0],[0,1,1,1],
             [0,2,0,0],[0,2,0,1],[0,2,1,0],[0,2,1,1],
             [0,3,0,0],[0,3,0,1],[0,3,1,0],[0,3,1,1],
             [1,2,0,0],[1,2,0,1],[1,2,1,0],[1,2,1,1],
             [1,3,0,0],[1,3,0,1],[1,3,1,0],[1,3,1,1],
             [2,3,0,0],[2,3,1,1]]
    assert checkSubgraphConstraints(vertices, colors, edges)

    # n=6 c=2 monochrome edges only appear in multi-edges
    vertices = list(range(6))
    colors = list(range(2))
    edges = [[0,1,0,0],[0,1,1,1], [2,3,0,0],[2,3,1,1], [4,5,0,0],[4,5,1,1],
             [1,3,0,1],[3,5,0,1],[1,5,1,0],
             [0,2,0,1],[2,4,0,1],[0,4,1,0]]
    assert checkSubgraphConstraints(vertices, colors, edges)

    # n=6 c=3, not valid, but should pass tests
    vertices = list(range(6))
    colors = list(range(3))
    edges = [[0,1,0,0],[2,3,0,0],[4,5,0,0],
             [1,2,1,1],[3,4,1,1],[0,5,1,1],
             [0,2,2,2],[3,5,2,2],[1,4,2,2]]
    assert checkSubgraphConstraints(vertices, colors, edges)

    # n=6 c=3, full skeleton graph + one multi-edge, fails starA
    vertices = list(range(6))
    colors = list(range(3))
    edges = [[0,1,0,0],[2,3,0,0],[4,5,0,0],
             [1,2,1,1],[3,4,1,1],[0,5,1,1], [0,3,0,0],[1,5,1,1],[2,4,1,1],
             [0,2,2,2],[3,5,2,2],[1,4,2,2], [0,4,2,2],[1,3,2,2],[2,5,2,2],
             [4,5,0,1]]
    assert not checkSubgraphConstraints(vertices, colors, edges)

    # n=6 c=3, monochrome star, fails starB
    vertices = list(range(6))
    colors = list(range(3))
    edges = [[0,1,0,0],[2,3,0,0],[4,5,0,0],[3,5,0,0],[2,5,0,0],
             [1,2,1,1],[3,4,1,1],[0,5,1,1], [0,3,1,1],[1,5,1,1],[2,4,1,1],
             [0,2,2,2],[3,5,2,2],[1,4,2,2], [0,4,2,2],[1,3,2,2],[2,5,2,2]]
    assert not checkSubgraphConstraints(vertices, colors, edges)

    # n=6 c=3, fail starC
    vertices = list(range(6))
    colors = list(range(3))
    edges = [[0,1,0,0],[2,3,0,0],[4,5,0,0],
             [1,2,1,1],[3,4,1,1],[0,5,1,1], [0,3,1,1],[1,5,1,1],[2,4,1,1], [1,5,0,1], [0,5,2,0],
             [0,2,2,2],[3,5,2,2],[1,4,2,2], [0,4,2,2],[1,3,2,2],[2,5,2,2]]
    assert not checkSubgraphConstraints(vertices, colors, edges)

    # TODO:
    # with all the conditional forbidden subgraphs,
    # its a bit hard to construct an example color collapse failure that passes all the other tests
    """
    # n=6 c=3, fail color collapse
    vertices = list(range(6))
    colors = list(range(3))
    edges = [
             [0,1,1,0],[0,2,1,0],[0,3,1,0],[0,4,2,0],[0,5,2,0],
             # ...
            ]
    assert not checkSubgraphConstraints(vertices, colors, edges)
    """

