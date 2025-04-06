# Pregel

## Top-level overview

[Pregel](https://research.google/pubs/pregel-a-system-for-large-scale-graph-processing/) is a core concept and a main building block in the IbisGraph library. Let's explore how it works under the hood.

The algorithm is designed to be iterative but includes an option to stop early when convergence is achieved. The main advantage of Pregel is that it can operate without any global state. This means that, theoretically, any Pregel-based algorithm is infinitely scalable, and this scalability is horizontal. We can distribute nodes across the cluster, and all we need to do is transmit very small messages from one node to another. Each message contains a minimal piece of information, while aggregations and message processing are atomic operations for each node.

Pregel operates through synchronized iterations called supersteps. Each superstep consists of three main steps: (1) each vertex prepares messages to send to its neighbors based on its internal state, (2) each vertex collects and aggregates messages received from its neighbors, and (3) each vertex updates its internal state based on the aggregated messages. While the operations within a single vertex are independent and atomic, Pregel enforces a blocking phase at the end of each superstep: all vertices must complete their computations before the next superstep begins.

![A very simple illustration of the Pregel idea.](https://raw.githubusercontent.com/SemyonSinchenko/ibisgraph/refs/heads/main/static/pregel.png)

## Example: shortest paths to node

Let's examine how Pregel works by implementing the Shortest Paths algorithm. The algorithm's goal is to find all shortest paths to a specific node in the graph, which we'll call a landmark. Initially, all nodes in the graph except the landmark start with a NULL state. The landmark is the only node with a non-NULL state, which is set to 0. In this case, each node's state represents its distance from the landmark.

### Message generation

If the state of the node is not NULL, then the message value equals the current STATE plus 1. For example, the first non-NULL subset of messages that will be sent is 1, which is transmitted to all neighbors of the landmark.

### Message aggregation

On the aggregation step we are choosing the smallest value from all the messages.

### Updating the state

If the aggregation results are smaller than the current message state, we will use these results as the new state.

### Example for 6-nodes graph

![Simple example of Shortest Paths with Pregel](https://raw.githubusercontent.com/SemyonSinchenko/ibisgraph/refs/heads/main/static/pregel-sp.png)

As you can see, on the iteration 4 we are sending a message to the vertex that has a state equal to 2, so in that case we are not updating the state.

# Pregel in IbisGraph

The Pregel implementation in IbisGraph is primarily a rewrite of the GraphFrames library's Pregel implementation. The key difference is that IbisGraph uses Ibis DataFrames instead of the Apache Spark DataFrame API. Additionally, several optimizations have been incorporated, including early stopping and nodes-voting functionality.

## Pseudo-code description

- Generate initial value (state) for all the nodes. In the IbisGraph implementation, state is handled as a column in the nodes table. It is possible to provide a lot of state-columns.
- Generate all triplets (node-edge-node) by performing two sequential joins of nodes data and edges. Each row in the triplets will contain all columns from the source node (as a `struct<>`), all columns from the destination node (as a `struct<>`), and all columns from the edges (also as a `struct<>`).

```python
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
```

- Generate messages as tuples in the format (target -> message). The target can be either the source or destination of the edge. During message generation, you can utilize any information from the source, destination, and edge structures. In tabular notation, this operation simply involves selecting additional columns as an array and expanding this array into individual rows.

```python
messages = [
    ibis.struct({IbisGraphConstants.ID.value: m.target_column, "msg": m.msg_expr})
    for m in self._messages
]
triplets_with_messages = triplets.select(ibis.array(messages).unnest().name("msg"))
```

Because each message is a pair, the new column `msg` is a struct. We can also desstruct this struct before doing back-join with nodes data:

```python
new_messages_table = triplets_with_messages.filter(
    triplets_with_messages["msg"]["msg"].notnull()
).select(
    triplets_with_messages["msg"][IbisGraphConstants.ID.value],
    triplets_with_messages["msg"]["msg"].name(PregelConstants.MSG_COL_NAME.value),
)
```

- Join and aggregate messages step. Because we have a nodes data table (with a node-id column) and messages table (with reciever of the message id column), all that we need is to do groupby + aggregate + join:

```python
aggregated_messages = new_messages_table.group_by(IbisGraphConstants.ID.value).agg(
    {PregelConstants.MSG_COL_NAME.value: self._agg_expression_func(msg_col)}
)
pregel_nodes_data = pregel_nodes_data.join(
    aggregated_messages, [IbisGraphConstants.ID.value], how="left"
)
```

- Update of the state. Now when we have a table with node ID, current state columns and aggregated message, we can just do select of the new state and go the step 1.



