import ibis

from ibisgraph.graph import IbisGraph, IbisGraphConstants


def in_degrees(graph: IbisGraph) -> ibis.Table:
    """Calculate the in-degrees for each node in a directed graph.

    Args:
        graph: A directed graph for which to calculate in-degrees.

    Returns:
        A table with columns 'node_id' and 'in_degree', representing the
        number of incoming edges for each node.

    Raises:
        ValueError: If the graph is undirected, as in-degrees are only
            meaningful for directed graphs.
    """
    if not graph._directed:
        raise ValueError("In-degrees for undirected graph is ambiguous.")
    edges = graph._edges
    return edges.group_by(edges[IbisGraphConstants.DST.value].name("node_id")).aggregate(
        ibis._.count().name("in_degree")
    )


def out_degrees(graph: IbisGraph) -> ibis.Table:
    """Calculate the out-degrees for each node in a directed graph.

    Args:
        graph: A directed graph for which to calculate out-degrees.

    Returns:
        A table with columns 'node_id' and 'out_degree', representing the
        number of outgoing edges for each node.

    Raises:
        ValueError: If the graph is undirected, as out-degrees are only
            meaningful for directed graphs.
    """
    if not graph._directed:
        raise ValueError("Out-degrees for undirected graph is ambiguous.")
    edges = graph._edges
    return edges.group_by(edges[IbisGraphConstants.SRC.value].name("node_id")).aggregate(
        ibis._.count().name("out_degree")
    )


def degrees(graph: IbisGraph) -> ibis.Table:
    """Calculate the degrees for each node in a graph.

    Args:
        graph: A graph for which to calculate degrees.

    Returns:
        A table with columns 'node_id' and 'degree', representing the
        number of edges for each node.
    """
    edges = graph._edges
    return (
        edges.select(
            ibis.array([ibis._[IbisGraphConstants.SRC.value], ibis._[IbisGraphConstants.DST.value]])
            .unnest()
            .name("node_id")
        )
        .group_by("node_id")
        .aggregate(ibis._.count().name("degree"))
    )
