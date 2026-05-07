# Quick Start Guide

IbisGraph is a graph analytics library built on top of Ibis. It lets you run graph operations directly on data that already lives in backends supported by Ibis.

## Installation

Install IbisGraph using pip:

```bash
pip install ibisgraph
```

## Backend Configuration

IbisGraph works with any backend supported by Ibis. You'll need to configure your backend according to the [Ibis documentation](https://ibis-project.org/backends/). Here are a few common examples:

```python
# DuckDB example
import ibis
conn = ibis.duckdb.connect()

# SQLite example
conn = ibis.sqlite.connect('path/to/database.db')

# PostgreSQL example
conn = ibis.postgres.connect(
    host='localhost',
    port=5432,
    user='your_user',
    password='your_password',
    database='your_database'
)
```

## Basic Usage

Here's how to get started with IbisGraph:

```python
import ibis
import ibisgraph as ig

# Connect to your database
conn = ibis.duckdb.connect()

# Create example node and edge tables
nodes = conn.create_table(
    'nodes',
    schema={
        'id': 'int64'
    }
)

edges = conn.create_table(
    'edges',
    schema={
        'src': 'int64',
        'dst': 'int64',
        'weight': 'float64'
    }
)

# Create a graph from the node and edge tables
graph = ig.IbisGraph(nodes, edges, directed=True, weight_col='weight')

# Calculate degree metrics
degrees = ig.centrality.degrees(graph)

# Find shortest paths
paths = ig.traversal.shortest_paths(graph, landmarks=[1, 2, 3])

# Calculate PageRank
pagerank = ig.centrality.page_rank(graph)
```

## Common Operations

Here are some common graph operations you can perform:

```python
# Get node degrees
in_degrees = ig.centrality.in_degrees(graph)
out_degrees = ig.centrality.out_degrees(graph)
total_degrees = ig.centrality.degrees(graph)

# Find similar nodes
similar_nodes = ig.similarity.jaccard_similarity(graph)

# Run community detection
communities = ig.clustering.label_propagation(graph)
```

For more detailed examples and API reference, please refer to the full documentation.
