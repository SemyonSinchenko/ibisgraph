import ibis
from ibisgraph import IbisGraph
from ibisgraph.centrality.degrees import degrees, out_degrees
from ibisgraph.graph import IbisGraphConstants
from ibisgraph.pregel import Pregel


def page_rank(
    graph: IbisGraph,
    alpha: float = 0.85,
    max_iters: int = 20,
    checkpoint_interval: int = 1,
    tol: float = 1e-4,
) -> ibis.Table:
    if (alpha <= 0) or (alpha >= 1.0):
        raise ValueError(f"Expected 0 <= alpha < 1.0 but got {alpha}.")
    num_nodes = graph.num_nodes
    coeff = (1 - alpha) / num_nodes
    initial_scores = 1.0 / num_nodes
    if graph.directed:
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
            "pagerank",
            ibis.literal(initial_scores),
            rank_upd_expr,
        )
        .add_vertex_col(
            "err",
            ibis.literal(100.0),
            (ibis._["pagerank"] - rank_upd_expr).abs(),
        )
        .add_message_to_dst(pregel.pregel_src("pagerank") / pregel.pregel_src("degree"))
        .set_agg_expression_func(lambda msg: msg.collect().sums())
        .set_has_active_flag(True)
        .set_active_flag_upd_col(ibis._["err"] >= tol)
        .set_early_stopping(True)
        .set_max_iter(max_iters)
        .set_stop_if_all_unactive(True)
    )

    if not graph.directed:
        pregel = pregel.add_message_to_src(
            pregel.pregel_dst("pagerank") / pregel.pregel_dst("degree")
        )

    output = pregel.run()
    return output.rename({"node_id": IbisGraphConstants.ID.value}).select("node_id", "pagerank")
