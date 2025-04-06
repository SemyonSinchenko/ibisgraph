import ibis
from loguru import logger
from typing_extensions import Callable, Self

from ibisgraph.graph import IbisGraph, IbisGraphConstants

from .models import PregelConstants, PregelMessage, PregelVertexColumn


class Pregel:
    """
    A Pregel-style graph processing implementation using Ibis for both single-node
    and distributed graph computations.

    This class provides a flexible framework for implementing vertex-centric graph algorithms
    with support for:
    - Vertex-level message passing
    - Customizable vertex column updates
    - Optional active vertex tracking
    - Early stopping
    - Custom activity expressions
    - Configurable maximum iterations
    - Checkpointing

    Key methods allow adding vertex columns, defining message passing strategies,
    and controlling algorithm execution parameters.

    This API is considered as the low-level. While it is public, it may be hard to use it directly.
    It is recommended to use a high-level APIs with routines, already implemented with this Pregel.
    """

    def __init__(self, graph: IbisGraph) -> None:
        """
        Initialize a Pregel graph processing instance.

        This method sets up the initial state for a Pregel-style graph computation,
        preparing the graph for vertex-centric processing. It initializes various
        internal attributes with default values that can be customized later.

        :param graph: An IbisGraph instance representing the graph to be processed
        :type graph: IbisGraph
        """
        self._graph = graph
        self._has_active_flag = False
        self._initial_active_flag: ibis.Value | ibis.Deferred = ibis.literal(True)
        self._vertex_cols: dict[str, PregelVertexColumn] = {}
        self._messages: list[PregelMessage] = []
        self._agg_expression_func: Callable[[ibis.Value], ibis.Value] | None = None
        self._do_early_stopping = True
        self._max_iter = 10
        self._checkpoint_interval = 1
        self._active_flag_upd_expr: ibis.Value | ibis.Deferred | None = None
        self._filter_messages_from_non_active: bool = False
        self._stop_if_all_non_active: bool = False

    def pregel_src(self, col_name: str) -> ibis.Value:
        """
        Helper method that simplify an access to attributes of the source column
        in messages generation.

        :param col_name: a name of the attribute
        :returns: ibis warpper around the attribute
        """
        return getattr(ibis._, IbisGraphConstants.SRC.value)[col_name]

    def pregel_dst(self, col_name: str) -> ibis.Value:
        """
        Helper method that simplify an access to attributes of the dst column
        in messages generation.

        :param col_name: a name of the attribute
        :returns: ibis warpper around the attribute
        """
        return getattr(ibis._, IbisGraphConstants.DST.value)[col_name]

    def pregel_edge(self, col_name: str) -> ibis.Value:
        """
        Helper method that simplify an access to attributes of the edge
        in messages generation.

        :param col_name: a name of the attribute
        :returns: ibis warpper around the attribute
        """
        return getattr(ibis._, IbisGraphConstants.EDGE.value)[col_name]

    def pregel_msg(self) -> ibis.Value:
        """
        Helper method that simplify an access to the Pregel message.
        """
        return getattr(ibis._, PregelConstants.MSG_COL_NAME.value)

    def add_vertex_col(
        self,
        col_name: str,
        initial_expr: ibis.Value | ibis.Deferred,
        update_expr: ibis.Value | ibis.Deferred,
    ) -> Self:
        """
        Add a vertex column to the Pregel. Column should has name, initial value and an update expression.

        :param col_name: a name of the column. It will be a part of the output
        :param initial_expr: expression for the initial value of the column
        :update_expr: expression to update the column, may use pregel_msg
        :returns: an updated instance of the Pregel
        """
        self._vertex_cols[col_name] = PregelVertexColumn(col_name, initial_expr, update_expr)
        return self

    def remove_vertex_col(self, col_name) -> Self:
        """
        Delete already added new vertex column by name. Does nothing if column does not exists.

        :param col_name: a name of the column to delete
        :returns: an updated instance of the Pregel
        """
        if col_name in self._vertex_cols:
            self._vertex_cols.pop(col_name)

        return self

    def add_message_to_src(self, message: ibis.Value) -> Self:
        """
        Add a message to the list of Pregel messages with a target equal to source of the edge.

        :param message: ibis expression for the message; can use srs, dst and edge attributes.
        :returns: an updated instance of the Pregel
        """
        self._messages.append(PregelMessage(self.pregel_src(IbisGraphConstants.ID.value), message))
        return self

    def add_message_to_dst(self, message: ibis.Value) -> Self:
        """
        Add a message to the list of Pregel messages with a target equal to destination of the edge.

        :param message: ibis expression for the message; can use srs, dst and edge attributes.
        :returns: an updated instance of the Pregel
        """
        self._messages.append(PregelMessage(self.pregel_dst(IbisGraphConstants.ID.value), message))
        return self

    def set_has_active_flag(self, value: bool) -> Self:
        """
        Set flag that algorithm supports vertices voting to stop iterations earlier
        or stop generating messages from this column (to both src and dst). If initial
        expression would not be provided, "literal(True)" will be used that means all the
        vertices considered initially active.

        :param value: flag value
        :returns: an updated instance of the Pregel
        """
        self._has_active_flag = value
        return self

    def set_initial_active_flag(self, expression: ibis.Value | ibis.Deferred) -> Self:
        """
        Set the expression that will be used for initial values of the active flag column.
        Automatically set "has_active_flag" to True.

        :param expression: ibis expression for the initial value of the active flag
        :returns: an updated instance of the Pregel
        """
        self._has_active_flag = True
        self._initial_active_flag = expression
        return self

    def set_agg_expression_func(self, expression: Callable[[ibis.Value], ibis.Value]) -> Self:
        """
        Set the aggregation expression function for processing messages.

        This method allows defining a custom aggregation function to combine messages
        received by a vertex during a single iteration of the Pregel algorithm. It can access
        pregel msg internally.

        :param expression: A callable that takes an Ibis value (message column) and returns
                           an aggregated Ibis value. Common aggregations include sum, max, first, etc.
        :returns: An updated instance of the Pregel
        """
        self._agg_expression_func = expression
        return self

    def set_early_stopping(self, value: bool) -> Self:
        """
        Set whether early stopping is enabled for the Pregel algorithm.

        Early stopping allows the Pregel algorithm to terminate before reaching the maximum
        number of iterations if no new messages are generated. This can help optimize
        computation by stopping when the algorithm has converged or no further changes
        are expected. But the check that there is a non-null message is not free, so if you
        know that there are always non null messages (for example, LabelPropagation),
        it is strongly recommended to rely on different ways to control the Pregel-flow
        (vertices voting, max iter, etc.)

        :param value: A boolean flag to enable or disable early stopping
        :returns: An updated instance of the Pregel
        """
        self._do_early_stopping = value
        return self

    def set_max_iter(self, value: int) -> Self:
        """
        Set the maximum number of iterations for the Pregel algorithm.

        This method allows controlling the total number of iterations the Pregel algorithm
        will execute. If the algorithm converges earlier, it may stop before reaching the
        maximum number of iterations. However, this method ensures that the algorithm will
        not run indefinitely.

        :param value: A positive integer representing the maximum number of iterations
        :raises ValueError: If a non-positive integer is provided
        :returns: An updated instance of the Pregel
        """
        if value <= 0:
            raise ValueError(f"Expected positive integer but got {value}.")

        self._max_iter = value
        return self

    def set_checkpoint_interval(self, value: int) -> Self:
        """
        Set the interval for checkpointing during Pregel iterations.

        Checkpointing allows intermediate results to be cached periodically during the
        Pregel algorithm's execution. This can help with performance and memory management
        by creating intermediate snapshots of the graph's state. But checkpoints are not free!

        For DuckDB and other single-node backends checkpoint on each step works better.
        For the case of distributed engine, like Apache Spark, the bigger value is recommended.

        :param value: The number of iterations between each checkpoint.
                      Set to 0 to disable checkpointing.
        :raises ValueError: If a negative integer is provided
        :returns: An updated instance of the Pregel
        """
        if value < 0:
            raise ValueError(f"Expected non-negative integer but got {value}.")

        self._checkpoint_interval = value
        return self

    def set_active_flag_upd_col(self, expression: ibis.Value | ibis.Deferred) -> Self:
        """
        Set a custom update expression for the active flag column.

        This method allows defining a custom expression to determine whether a vertex
        remains active in the Pregel algorithm. The expression can use message information
        or other vertex attributes to decide vertex activity. For example, in the PageRank
        this expression should check is the difference between old and new ranks grater than tolerance.

        :param expression: An Ibis expression defining how the active flag should be updated
        :returns: An updated instance of the Pregel
        """
        self._active_flag_upd_expr = expression
        return self

    def set_filter_messages_from_non_active(self, value: bool) -> Self:
        """
        Set whether messages from non-active vertices should be filtered out.

        When set to True, the Pregel algorithm will only process messages from edges where
        at least one of the source or destination vertices is active. This can help optimize
        computation by reducing unnecessary message processing for inactive vertices. In some
        cases, Pregel will be broken by that setting! For example, in LabelPropagation,
        if the vertex did not change it's label it is considered unactive, but we should continue
        generate messages from it!

        :param value: Boolean flag to enable/disable filtering of messages from non-active vertices
        :returns: an updated instance of the Pregel
        """
        self._filter_messages_from_non_active = value
        return self

    def set_stop_if_all_unactive(self, value: bool) -> Self:
        """
        Set whether the Pregel algorithm should stop early if all vertices become inactive.

        When set to True, the algorithm will terminate if all vertices are marked as non-active
        during an iteration. This can help optimize computation by stopping early when no further
        processing is needed. Not all the algorithms can benefit from this feature! Check is not free.

        :param value: Boolean flag to enable/disable early stopping when all vertices are inactive
        :returns: an updated instance of the Pregel
        """
        self._stop_if_all_non_active = value
        return self

    def _validate(self) -> None:
        if self._agg_expression_func is None:
            raise ValueError("AggExpression should be provided!")
        if len(self._messages) == 0:
            raise ValueError("At least one message (to src or to dst) should be provided!")
        if len(self._vertex_cols) == 0:
            raise ValueError("At least one vertex column should be prvided!")

    def run(self) -> ibis.Table:
        """
        Run the Pregel and return the result in the form of the Table.

        :returns: a table with all the exisitng vertices columns and all the new columns.
        """
        self._validate()
        messages = [
            ibis.struct({IbisGraphConstants.ID.value: m.target_column, "msg": m.msg_expr})
            for m in self._messages
        ]

        graph_columns = [getattr(ibis._, c) for c in self._graph._nodes.columns]
        for vcol in self._vertex_cols.values():
            graph_columns.append(vcol.initial_expr.name(vcol.col_name))

        if self._has_active_flag:
            graph_columns.append(
                self._initial_active_flag.name(PregelConstants.ACTIVE_VERTEX_FLAG.value)
            )

        pregel_nodes_data = self._graph._nodes.select(*graph_columns)
        edges = self._graph._edges.select(
            ibis.struct({col: getattr(ibis._, col) for col in self._graph._edges.columns}).name(
                IbisGraphConstants.EDGE.value
            )
        ).cache()

        it = 0

        while it < self._max_iter:
            logger.info(f"Start iteration {it} of {self._max_iter}")
            it += 1

            src_nodes_data = pregel_nodes_data.select(
                ibis.struct({col: ibis._[col] for col in pregel_nodes_data.columns}).name(
                    IbisGraphConstants.SRC.value
                )
            )
            dst_nodes_data = pregel_nodes_data.select(
                ibis.struct({col: ibis._[col] for col in pregel_nodes_data.columns}).name(
                    IbisGraphConstants.DST.value
                )
            )
            triplets = src_nodes_data.inner_join(
                edges,
                [
                    src_nodes_data[IbisGraphConstants.SRC.value][IbisGraphConstants.ID.value]
                    == edges[IbisGraphConstants.EDGE.value][IbisGraphConstants.SRC.value]
                ],
            ).inner_join(
                dst_nodes_data,
                [
                    dst_nodes_data[IbisGraphConstants.DST.value][IbisGraphConstants.ID.value]
                    == edges[IbisGraphConstants.EDGE.value][IbisGraphConstants.DST.value]
                ],
            )
            if self._filter_messages_from_non_active:
                src_active = triplets[IbisGraphConstants.SRC.value][
                    PregelConstants.ACTIVE_VERTEX_FLAG.value
                ].cast("bool")
                dst_active = triplets[IbisGraphConstants.DST.value][
                    PregelConstants.ACTIVE_VERTEX_FLAG.value
                ].cast("bool")
                triplets = triplets.filter(ibis.or_(src_active, dst_active))

            triplets_with_messages = triplets.select(ibis.array(messages).unnest().name("msg"))
            new_messages_table = triplets_with_messages.filter(
                triplets_with_messages["msg"]["msg"].notnull()
            ).select(
                triplets_with_messages["msg"][IbisGraphConstants.ID.value],
                triplets_with_messages["msg"]["msg"].name(PregelConstants.MSG_COL_NAME.value),
            )

            if self._do_early_stopping:
                cnt_of_not_null_msgs = new_messages_table.count().to_pandas()
                logger.info(f"{cnt_of_not_null_msgs} non null messages were generated.")
                if cnt_of_not_null_msgs == 0:
                    logger.info(f"Pregel stopped on the iteration {it}: no more messages.")
                    break

            assert self._agg_expression_func is not None
            msg_col = new_messages_table[PregelConstants.MSG_COL_NAME.value]
            aggregated_messages = new_messages_table.group_by(IbisGraphConstants.ID.value).agg(
                {PregelConstants.MSG_COL_NAME.value: self._agg_expression_func(msg_col)}
            )

            pregel_nodes_data = pregel_nodes_data.join(
                aggregated_messages, [IbisGraphConstants.ID.value], how="left"
            )

            new_columns = [getattr(pregel_nodes_data, col) for col in self._graph._nodes.columns]
            for vertex_col in self._vertex_cols.values():
                new_columns.append(vertex_col.update_expr.name(vertex_col.col_name))

            if self._has_active_flag:
                if self._active_flag_upd_expr is not None:
                    new_active_col = self._active_flag_upd_expr.name(
                        PregelConstants.ACTIVE_VERTEX_FLAG.value
                    )
                else:
                    new_active_col = (
                        pregel_nodes_data[PregelConstants.MSG_COL_NAME.value]
                        .notnull()
                        .name(PregelConstants.ACTIVE_VERTEX_FLAG.value)
                    )
                new_columns.append(new_active_col)

            tmp_pregel_nodes_data = pregel_nodes_data.select(*new_columns)

            if (
                (self._checkpoint_interval > 0)
                and (it != 0)
                and (it % self._checkpoint_interval == 0)
            ):
                pregel_nodes_data = tmp_pregel_nodes_data.cache()
            else:
                pregel_nodes_data = tmp_pregel_nodes_data

            if self._stop_if_all_non_active:
                all_active = (
                    pregel_nodes_data.select(
                        pregel_nodes_data[PregelConstants.ACTIVE_VERTEX_FLAG.value]
                    )
                    .distinct()
                    .to_pandas()
                )
                if len(all_active) == 1:
                    if not all_active.values[0]:
                        logger.info("Pregel stopped earlier: all nodes are non-active.")
                        break

        logger.info("Pregel stopped: max-iterations reached.")
        if self._has_active_flag:
            return pregel_nodes_data.drop(PregelConstants.ACTIVE_VERTEX_FLAG.value)
        else:
            return pregel_nodes_data
