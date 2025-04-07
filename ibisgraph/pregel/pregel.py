import ibis
from loguru import logger
from typing_extensions import Callable, Self

from ibisgraph.graph import IbisGraph, IbisGraphConstants

from .models import PregelConstants, PregelMessage, PregelVertexColumn


class Pregel:
    """A Pregel-style graph processing implementation using Ibis.

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

    Note:
        This API is considered low-level. While it is public, it may be hard to use directly.
        It is recommended to use high-level APIs with routines already implemented with this Pregel.
    """

    def __init__(self, graph: IbisGraph) -> None:
        """Initialize a Pregel graph processing instance.

        Args:
            graph: An IbisGraph instance representing the graph to be processed.
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
        """Helper method to access attributes of the source column in messages generation.

        Args:
            col_name: Name of the attribute.

        Returns:
            Ibis wrapper around the attribute.
        """
        return getattr(ibis._, IbisGraphConstants.SRC.value)[col_name]

    def pregel_dst(self, col_name: str) -> ibis.Value:
        """Helper method to access attributes of the destination column in messages generation.

        Args:
            col_name: Name of the attribute.

        Returns:
            Ibis wrapper around the attribute.
        """
        return getattr(ibis._, IbisGraphConstants.DST.value)[col_name]

    def pregel_edge(self, col_name: str) -> ibis.Value:
        """Helper method to access attributes of the edge in messages generation.

        Args:
            col_name: Name of the attribute.

        Returns:
            Ibis wrapper around the attribute.
        """
        return getattr(ibis._, IbisGraphConstants.EDGE.value)[col_name]

    def pregel_msg(self) -> ibis.Value:
        """Helper method to access the Pregel message.

        Returns:
            Ibis wrapper around the message.
        """
        return getattr(ibis._, PregelConstants.MSG_COL_NAME.value)

    def add_vertex_col(
        self,
        col_name: str,
        initial_expr: ibis.Value | ibis.Deferred,
        update_expr: ibis.Value | ibis.Deferred,
    ) -> Self:
        """Add a vertex column to the Pregel.

        Args:
            col_name: Name of the column that will be part of the output.
            initial_expr: Expression for the initial value of the column.
            update_expr: Expression to update the column, may use pregel_msg.

        Returns:
            Updated instance of the Pregel.
        """
        self._vertex_cols[col_name] = PregelVertexColumn(col_name, initial_expr, update_expr)
        return self

    def remove_vertex_col(self, col_name) -> Self:
        """Delete an already added vertex column by name.

        Args:
            col_name: Name of the column to delete.

        Returns:
            Updated instance of the Pregel.
            Does nothing if column does not exist.
        """
        if col_name in self._vertex_cols:
            self._vertex_cols.pop(col_name)

        return self

    def add_message_to_src(self, message: ibis.Value) -> Self:
        """Add a message targeting the source of the edge.

        Args:
            message: Ibis expression for the message; can use src, dst and edge attributes.

        Returns:
            Updated instance of the Pregel.
        """
        self._messages.append(PregelMessage(self.pregel_src(IbisGraphConstants.ID.value), message))
        return self

    def add_message_to_dst(self, message: ibis.Value) -> Self:
        """Add a message targeting the destination of the edge.

        Args:
            message: Ibis expression for the message; can use src, dst and edge attributes.

        Returns:
            Updated instance of the Pregel.
        """
        self._messages.append(PregelMessage(self.pregel_dst(IbisGraphConstants.ID.value), message))
        return self

    def set_has_active_flag(self, value: bool) -> Self:
        """Set whether algorithm supports vertices voting to stop iterations.

        Args:
            value: Whether to enable active flag support.

        Returns:
            Updated instance of the Pregel.

        Note:
            If initial expression is not provided, "literal(True)" will be used,
            meaning all vertices are initially active.
        """
        self._has_active_flag = value
        return self

    def set_initial_active_flag(self, expression: ibis.Value | ibis.Deferred) -> Self:
        """Set the expression for initial values of the active flag column.

        Args:
            expression: Ibis expression for the initial value of the active flag.

        Returns:
            Updated instance of the Pregel.
            Automatically sets "has_active_flag" to True.
        """
        self._has_active_flag = True
        self._initial_active_flag = expression
        return self

    def set_agg_expression_func(self, expression: Callable[[ibis.Value], ibis.Value]) -> Self:
        """Set the aggregation expression function for processing messages.

        Args:
            expression: A callable that takes an Ibis value (message column) and returns
                an aggregated Ibis value. Common aggregations include sum, max, first, etc.

        Returns:
            Updated instance of the Pregel.
        """
        self._agg_expression_func = expression
        return self

    def set_early_stopping(self, value: bool) -> Self:
        """Set whether early stopping is enabled.

        Early stopping allows termination before reaching maximum iterations if no new
        messages are generated. This can optimize computation but has overhead for checking
        message nullity. For algorithms with guaranteed non-null messages (e.g., LabelPropagation),
        it's recommended to use other control methods (vertices voting, max iter, etc.).

        Args:
            value: Whether to enable early stopping.

        Returns:
            Updated instance of the Pregel.
        """
        self._do_early_stopping = value
        return self

    def set_max_iter(self, value: int) -> Self:
        """Set the maximum number of iterations.

        Args:
            value: Positive integer for maximum iterations.

        Returns:
            Updated instance of the Pregel.

        Raises:
            ValueError: If value is not positive.
        """
        if value <= 0:
            raise ValueError(f"Expected positive integer but got {value}.")

        self._max_iter = value
        return self

    def set_checkpoint_interval(self, value: int) -> Self:
        """Set the interval for checkpointing during iterations.

        For DuckDB and other single-node backends, checkpoint on each step works better.
        For distributed engines like Apache Spark, larger values are recommended.

        Args:
            value: Number of iterations between checkpoints. 0 disables checkpointing.

        Returns:
            Updated instance of the Pregel.

        Raises:
            ValueError: If value is negative.
        """
        if value < 0:
            raise ValueError(f"Expected non-negative integer but got {value}.")

        self._checkpoint_interval = value
        return self

    def set_active_flag_upd_col(self, expression: ibis.Value | ibis.Deferred) -> Self:
        """Set a custom update expression for the active flag column.

        Args:
            expression: Ibis expression defining how the active flag should be updated.
                For example, in PageRank this expression should check if the difference
                between old and new ranks is greater than tolerance.

        Returns:
            Updated instance of the Pregel.
        """
        self._active_flag_upd_expr = expression
        return self

    def set_filter_messages_from_non_active(self, value: bool) -> Self:
        """Set whether to filter out messages from non-active vertices.

        Args:
            value: Whether to enable message filtering.

        Returns:
            Updated instance of the Pregel.

        Note:
            This can break some algorithms! For example, in LabelPropagation,
            if a vertex didn't change its label it's considered inactive,
            but we should continue generating messages from it.
        """
        self._filter_messages_from_non_active = value
        return self

    def set_stop_if_all_unactive(self, value: bool) -> Self:
        """Set whether to stop early if all vertices become inactive.

        Args:
            value: Whether to enable stopping on all inactive.

        Returns:
            Updated instance of the Pregel.

        Note:
            Not all algorithms benefit from this feature! The check has overhead.
        """
        self._stop_if_all_non_active = value
        return self

    def _validate(self) -> None:
        """Validate Pregel configuration before running.

        Raises:
            ValueError: If required components are missing.
        """
        if self._agg_expression_func is None:
            raise ValueError("AggExpression should be provided!")
        if len(self._messages) == 0:
            raise ValueError("At least one message (to src or to dst) should be provided!")
        if len(self._vertex_cols) == 0:
            raise ValueError("At least one vertex column should be provided!")

    def run(self) -> ibis.Table:
        """Run the Pregel algorithm and return results.

        Returns:
            Table with all existing vertices columns and all new columns.
            If active flag was used, it is removed from the final result.

        Raises:
            ValueError: If validation fails before running.
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
