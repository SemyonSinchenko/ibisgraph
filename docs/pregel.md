# Pregel Implementation in IbisGraph

## Overview

This document explains how IbisGraph implements Pregel-like graph processing using SQL operations. The implementation translates Pregel's vertex-centric computation model into a series of SQL operations that can run in any data warehouse or data lake supported by Ibis.

## What is Pregel?

Pregel is a system for large-scale graph processing introduced by Google. It uses a vertex-centric approach where:

1. Each vertex can store state
2. Vertices communicate through messages
3. Computation proceeds in synchronized iterations (supersteps)

In each superstep:

1. Vertices receive messages from the previous superstep
2. Update their state based on received messages
3. Send messages to other vertices for the next superstep

## SQL Translation

IbisGraph translates this model into SQL operations. Here's a visualization of how a typical superstep works:

```
Initial State:
Table: vertices
+----+-------+
| id | value |
+----+-------+
| 1  | 0.2   |
| 2  | 0.3   |
| 3  | 0.5   |
+----+-------+

Table: edges
+------+--------+
| from | to     |
+------+--------+
| 1    | 2      |
| 2    | 3      |
| 3    | 1      |
+------+--------+

Superstep:
1. Generate messages:
   SELECT 
     e.to as target,
     v.value as message
   FROM vertices v
   JOIN edges e ON v.id = e.from

2. Aggregate messages:
   SELECT
     target,
     SUM(message) as agg_message
   FROM messages
   GROUP BY target

3. Update vertices:
   SELECT
     v.id,
     CASE 
       WHEN m.agg_message IS NULL THEN v.value
       ELSE function(v.value, m.agg_message)
     END as new_value
   FROM vertices v
   LEFT JOIN messages m ON v.id = m.target
```

## Key Components

### 1. Graph State
- Vertex data stored in regular SQL tables
- Edge data stored in source-target format
- Additional columns can store vertex/edge attributes

### 2. Message Passing
Implemented through:
1. JOIN operations between vertex and edge tables
2. Message generation expressions
3. GROUP BY for message aggregation

### 3. Vertex State Updates
Performed using:
1. LEFT JOIN to preserve vertices that receive no messages
2. UPDATE expressions defined by the algorithm
3. Optional active vertex tracking

### 4. Halting Conditions
Multiple stopping criteria available:
- Maximum iterations reached
- No messages generated
- All vertices vote to halt
- Custom convergence conditions

## Performance Considerations

### Advantages
1. **No Data Movement**
    - All processing happens in the data warehouse
    - No need to extract data or maintain separate systems

2. **Scalability**
    - Inherits data warehouse scaling capabilities
    - No single-machine memory limitations

3. **Integration**
    - Natural integration with SQL-based data pipelines
    - Can leverage existing warehouse optimizations

### Limitations
1. **Iteration Overhead**
    - Each superstep requires multiple SQL operations
    - More expensive than native graph processing

2. **Message Handling**
    - Message generation can create large intermediate results
    - Aggregation performance depends on warehouse capabilities

3. **State Management**
    - Vertex state changes require table updates
    - May need careful tuning of checkpoint intervals

## Implementation Details

### Active Vertex Tracking

```python
# Example of active vertex tracking
pregel.set_has_active_flag(True)
      .set_initial_active_flag(initial_condition)
      .set_active_flag_upd_col(update_condition)
```

### Message Generation
```python
# Example of message generation
pregel.add_message_to_dst(
    ibis.case()
        .when(condition, message_value)
        .else_(None)
)
```

### Vertex Updates
```python
# Example of vertex state update
pregel.add_vertex_col(
    "value",
    initial_expr=initial_value,
    update_expr=update_function(old_value, message)
)
```

## Optimization Tips

1. **Checkpoint Intervals**
   - For single-node backends (DuckDB, SQLite):
     ```python
     pregel.set_checkpoint_interval(1)
     ```
   - For distributed engines (Spark, Snowflake):
     ```python
     pregel.set_checkpoint_interval(5)  # or higher
     ```

2. **Message Filtering**
   ```python
   # Filter messages from inactive vertices
   pregel.set_filter_messages_from_non_active(True)
   ```

3. **Early Stopping**
   ```python
   # Stop when no new messages or all vertices inactive
   pregel.set_early_stopping(True)
   pregel.set_stop_if_all_unactive(True)
   ```

## Example: PageRank Implementation

Here's how PageRank is implemented using this Pregel framework:

```python
def page_rank(graph: IbisGraph, alpha: float = 0.85) -> ibis.Table:
    n_nodes = graph.num_nodes
    initial_rank = 1.0 / n_nodes
    
    pregel = (
        Pregel(graph)
        .add_vertex_col(
            "rank",
            initial_expr=initial_rank,
            update_expr=alpha * pregel.pregel_msg() + (1 - alpha) / n_nodes
        )
        .add_message_to_dst(
            pregel.pregel_src("rank") / pregel.pregel_src("out_degree")
        )
        .set_agg_expression_func(lambda msg: msg.sum())
    )
    
    return pregel.run()
```

This implementation shows how Pregel concepts map to SQL operations while maintaining the algorithm's logical structure.

## Best Practices

1. **Message Volume**
    - Filter unnecessary messages when possible
    - Use appropriate aggregation functions
    - Consider using active vertex tracking

2. **State Management**
    - Keep vertex state minimal
    - Use appropriate data types
    - Consider compression for large state

3. **Performance Tuning**
    - Adjust checkpoint intervals based on backend
    - Use appropriate convergence conditions
    - Monitor intermediate result sizes

## Debugging Tips

1. **Message Generation**
    - Use `pregel_src()` and `pregel_dst()` helpers
    - Check for NULL values in messages
    - Verify message targeting

2. **State Updates**
    - Validate initial state expressions
    - Check update logic with edge cases
    - Monitor convergence patterns

3. **Performance Issues**
    - Check execution plans
    - Monitor intermediate result sizes
    - Verify checkpoint interval settings
