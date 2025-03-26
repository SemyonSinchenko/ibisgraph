import ibis

from ibisgraph.graph import IbisGraph, IbisGraphConstants


def jaccard_similarity(graph: IbisGraph) -> ibis.Table:
    """
    Calculate Jaccard similarity between all pairs of nodes in a graph.

    Jaccard similarity is defined as the size of the intersection of two nodes' neighborhoods
    divided by the size of their union. This function computes pairwise Jaccard similarities
    for all nodes in the graph.

    For undirected graphs, the edge list is symmetrized to ensure correct neighborhood calculation.

    :param graph: The input graph to compute Jaccard similarities on.
    :returns: A table with three columns:
        - "node_id_left": The first node in the pair
        - "node_id_right": The second node in the pair
        - "jaccard_similarity": The Jaccard similarity between the two nodes' neighborhoods
    """
    edges = graph.edges
    if not graph.directed:
        edges = edges.union(
            edges.select(
                edges[IbisGraphConstants.DST.value].name(IbisGraphConstants.SRC.value),
                edges[IbisGraphConstants.SRC.value].name(IbisGraphConstants.DST.value),
            )
        )
    neighbors = edges.group_by(
        edges[IbisGraphConstants.SRC.value].name(IbisGraphConstants.ID.value)
    ).aggregate(ibis._[IbisGraphConstants.DST.value].collect().name("nbr"))

    cross_joined = neighbors.cross_join(neighbors)
    return cross_joined.select(
        cross_joined[IbisGraphConstants.ID.value].name("node_id_left"),
        cross_joined[f"{IbisGraphConstants.ID.value}_right"].name("node_id_right"),
        (
            (cross_joined["nbr"].intersect(cross_joined["nbr_right"])).length()
            / (cross_joined["nbr"].union(cross_joined["nbr_right"]).length())
        ).name("jaccard_similarity"),
    )
