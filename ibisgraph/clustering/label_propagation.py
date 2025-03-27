import ibis

from ibisgraph.graph import IbisGraph, IbisGraphConstants
from ibisgraph.pregel.pregel import Pregel

LABEL_COL_NAME = "label"
NODE_COL_NAME = "node_id"


def label_propagation(
    graph: IbisGraph,
    max_iter: int = 30,
    checkpoint_interval: int = 1,
    sort_labels: bool = False,
) -> ibis.Table:
    """
    Perform Label Propagation clustering on a graph with Pregel.

    Label Propagation is an iterative algorithm that assigns labels to nodes
    based on the labels of their neighbors. Each node initially starts with
    its own unique label and then iteratively adopts the most frequent label
    among its neighbors. This implementation is not determenistic if sort_labels is False.
    If sort_labels is True, then labels are sorted by index and result is determenistic,
    but it may tend to cases when all the labels in the output will be the same,
    because nodes with low id will be preferred.

    :param graph: Input graph to perform clustering on.
    :param max_iter: Maximum number of iterations. Defaults to 30.
    :param checkpoint_interval: Interval for checkpointing. Defaults to 1.
    :param sort_labels: If True, sort labels before selecting mode. Defaults to False.

    :returns: A table with two columns:
            - 'node_id': Original node identifiers
            - 'label': Assigned cluster label for each node
    """
    pregel = (
        Pregel(graph)
        .set_max_iter(max_iter)
        .set_has_active_flag(True)
        .set_checkpoint_interval(checkpoint_interval)
        .set_filter_messages_from_non_active(False)
        .set_stop_if_all_unactive(True)
    )

    pregel = pregel.add_vertex_col(
        LABEL_COL_NAME,
        ibis._[IbisGraphConstants.ID.value],
        pregel.pregel_msg(),
    ).set_active_flag_upd_col(pregel.pregel_msg() != ibis._[LABEL_COL_NAME])

    pregel = pregel.add_message_to_dst(pregel.pregel_src(LABEL_COL_NAME))

    if not graph.directed:
        pregel = pregel.add_message_to_src(pregel.pregel_dst(LABEL_COL_NAME))

    if sort_labels:
        pregel = pregel.set_agg_expression_func(lambda msg: msg.collect().sort().modes())
    else:
        pregel = pregel.set_agg_expression_func(lambda msg: msg.collect().modes())
    result = pregel.run()

    return result.select(
        result[IbisGraphConstants.ID.value].name(NODE_COL_NAME), result[LABEL_COL_NAME]
    )
