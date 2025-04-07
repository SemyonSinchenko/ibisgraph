from collections.abc import Sequence

import ibis

from ibisgraph.graph import IbisGraph, IbisGraphConstants
from ibisgraph.pregel.pregel import Pregel

DISTANCE_COL_NAME = "distances"
SP_NODE_ID_COL_NAME = "node_id"


def shortest_paths(
    graph: IbisGraph,
    landmarks: Sequence[int],
    checkpoint_interval: int = 1,
    max_iter: int = 20,
) -> ibis.Table:
    """Calculate shortest paths from multiple landmark nodes in a graph using Pregel.

    Computes the shortest distances from specified landmark nodes to all other
    nodes in the graph using a Pregel-based algorithm. Supports both directed and
    undirected graphs.

    Args:
        graph: The input graph to compute shortest paths on.
        landmarks: Sequence of node IDs to use as landmark/source nodes.
        checkpoint_interval: Interval for checkpointing. Defaults to 1.
            Recommended to keep at 1 for single-node/in-memory backends.
            For distributed engines like Apache Spark, larger values are recommended.
        max_iter: Maximum number of Pregel iterations. Acts as a safeguard against
            infinite iterations. Defaults to 20.

    Returns:
        A table with two columns:
        - "node_id": The ID of each node in the graph
        - "distances": A struct containing shortest distances to each landmark node
            (distance_to_{landmark_id} -> distance (int))

    Warning:
        Distances to landmarks are handled as columns internally. If landmarks contains
        many elements, there may be performance issues due to operations on very wide tables.
    """
    pregel = (
        Pregel(graph)
        .set_early_stopping(True)
        .set_initial_active_flag(ibis._[IbisGraphConstants.ID.value].isin(landmarks))
        .set_checkpoint_interval(checkpoint_interval)
    )
    distance_col_pattern = "distance_to_{}"

    for lmark in landmarks:
        col_name = distance_col_pattern.format(lmark)
        pregel = pregel.add_vertex_col(
            col_name,
            ibis.ifelse(
                ibis._[IbisGraphConstants.ID.value] == ibis.literal(lmark),
                ibis.literal(0),
                ibis.null("int"),
            ),
            ibis.ifelse(
                ibis.or_(
                    pregel.pregel_msg()[col_name] < ibis._[col_name],
                    ibis.and_(pregel.pregel_msg()[col_name].notnull(), ibis._[col_name].isnull()),
                ),
                pregel.pregel_msg()[col_name],
                ibis._[col_name],
            ),
        )

    pregel_to_dst_check_exprs = [
        ibis.or_(
            pregel.pregel_src(distance_col_pattern.format(lmark)) + ibis.literal(1)
            < pregel.pregel_dst(distance_col_pattern.format(lmark)),
            ibis.and_(
                pregel.pregel_src(distance_col_pattern.format(lmark)).notnull(),
                pregel.pregel_dst(distance_col_pattern.format(lmark)).isnull(),
            ),
        )
        for lmark in landmarks
    ]
    pregel = pregel.add_message_to_dst(
        ibis.ifelse(
            ibis.or_(*pregel_to_dst_check_exprs),
            ibis.struct(
                {
                    distance_col_pattern.format(lmark): pregel.pregel_src(
                        distance_col_pattern.format(lmark)
                    )
                    + ibis.literal(1)
                    for lmark in landmarks
                }
            ),
            ibis.null(),
        )
    )

    if not graph.is_directed:
        pregel_to_src_check_exprs = [
            ibis.or_(
                pregel.pregel_dst(distance_col_pattern.format(lmark)) + ibis.literal(1)
                < pregel.pregel_src(distance_col_pattern.format(lmark)),
                ibis.and_(
                    pregel.pregel_dst(distance_col_pattern.format(lmark)).notnull(),
                    pregel.pregel_src(distance_col_pattern.format(lmark)).isnull(),
                ),
            )
            for lmark in landmarks
        ]
        pregel = pregel.add_message_to_src(
            ibis.ifelse(
                ibis.or_(*pregel_to_src_check_exprs),
                ibis.struct(
                    {
                        distance_col_pattern.format(lmark): pregel.pregel_dst(
                            distance_col_pattern.format(lmark)
                        )
                        + ibis.literal(1)
                        for lmark in landmarks
                    }
                ),
                ibis.null(),
            )
        )

    pregel = pregel.set_agg_expression_func(
        lambda msg: ibis.struct(
            {
                distance_col_pattern.format(lmark): msg[distance_col_pattern.format(lmark)]
                .collect()
                .mins()
                for lmark in landmarks
            }
        )
    )

    raw_output = pregel.set_max_iter(20).set_filter_messages_from_non_active(True).run()
    return raw_output.select(
        raw_output[IbisGraphConstants.ID.value].name(SP_NODE_ID_COL_NAME),
        ibis.struct(
            {
                distance_col_pattern.format(lmark): raw_output[distance_col_pattern.format(lmark)]
                for lmark in landmarks
            }
        ).name(DISTANCE_COL_NAME),
    )
