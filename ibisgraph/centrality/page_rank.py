import ibis

from ibisgraph.graph import IbisGraph
from ibisgraph.centrality.degrees import degrees, out_degrees
from ibisgraph.graph import IbisGraphConstants
from ibisgraph.pregel import Pregel

PAGERANK_NODE_COL_NAME = "node_id"
PAGERANK_SCORE_COL_NAME = "pagerank"


def page_rank(
    graph: IbisGraph,
    alpha: float = 0.85,
    max_iters: int = 20,
    checkpoint_interval: int = 1,
    tol: float = 1e-4,
) -> ibis.Table:
    """Compute PageRank for a graph using the Pregel iterative algorithm.

    PageRank measures the importance of nodes in a graph based on the structure of incoming links.
    The algorithm simulates a random walk through the graph, where a hypothetical 'random surfer'
    follows links with probability `alpha` and jumps to a random node with probability `1 - alpha`.

    Args:
        graph: The input graph for PageRank computation.
        alpha: Damping factor controlling random walk probability. Must be between 0 and 1.
            Defaults to 0.85.
        max_iters: Maximum number of iterations. Defaults to 20.
        checkpoint_interval: Interval for checkpointing. Defaults to 1.
            Recommended to keep at 1 for single-node/in-memory backends.
            For distributed engines like Apache Spark, larger values are recommended.
        tol: Convergence tolerance. Stops when score changes are below this value.
            Defaults to 1e-4.

    Returns:
        A table with node IDs (column "node_id") and their corresponding PageRank scores
        (column "pagerank").

    Raises:
        ValueError: If alpha is not between 0 and 1.

    Note:
        - For convergence-based stopping: Set max_iter high and control flow with tol.
        - For fixed iterations: Set tol to 0 and control flow with max_iter.
        - While this implementation supports undirected graphs, PageRank is not
          clearly defined for such graphs.
    """
    if (alpha <= 0) or (alpha >= 1.0):
        raise ValueError(f"Expected 0 <= alpha < 1.0 but got {alpha}.")
    num_nodes = graph.num_nodes
    coeff = (1 - alpha) / num_nodes
    initial_scores = 1.0 / num_nodes
    if graph.is_directed:
        tmp_degrees = out_degrees(graph).rename(
            {IbisGraphConstants.ID.value: "node_id", "degree": "out_degree"}
        )
    else:
        tmp_degrees = degrees(graph).rename({IbisGraphConstants.ID.value: "node_id"})
    nodes_with_degrees = graph.nodes.join(tmp_degrees, [IbisGraphConstants.ID.value])
    new_g = IbisGraph(
        nodes_with_degrees,
        graph.edges,
        id_col=IbisGraphConstants.ID.value,
        src_col=IbisGraphConstants.SRC.value,
        dst_col=IbisGraphConstants.DST.value,
    )
    pregel = Pregel(new_g)

    rank_upd_expr = ibis.ifelse(
        pregel.pregel_msg().isnull(), ibis.literal(0.0), pregel.pregel_msg()
    ) * ibis.literal(alpha) + ibis.literal(coeff)

    pregel = (
        pregel.add_vertex_col(
            PAGERANK_SCORE_COL_NAME,
            ibis.literal(initial_scores),
            rank_upd_expr,
        )
        .add_vertex_col(
            "err",
            ibis.literal(100.0),
            (ibis._[PAGERANK_SCORE_COL_NAME] - rank_upd_expr).abs(),
        )
        .add_message_to_dst(
            pregel.pregel_src(PAGERANK_SCORE_COL_NAME) / pregel.pregel_src("degree")
        )
        .set_agg_expression_func(lambda msg: msg.collect().sums())
        .set_has_active_flag(True)
        .set_active_flag_upd_col(ibis._["err"] >= tol)
        .set_early_stopping(True)
        .set_max_iter(max_iters)
        .set_stop_if_all_unactive(True)
    )

    if not graph.is_directed:
        pregel = pregel.add_message_to_src(
            pregel.pregel_dst(PAGERANK_SCORE_COL_NAME) / pregel.pregel_dst("degree")
        )

    output = pregel.run()
    return output.rename({PAGERANK_NODE_COL_NAME: IbisGraphConstants.ID.value}).select(
        PAGERANK_NODE_COL_NAME, PAGERANK_SCORE_COL_NAME
    )
