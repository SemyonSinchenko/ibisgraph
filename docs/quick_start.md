# Quick Start Guide

IbisGraph is a graph analytics library built on top of Ibis, allowing you to perform graph operations on data stored in various backends supported by Ibis. The main benefit of the IbisGraph is that data is staying in the backend and all the operations are done in this backend.

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

# Create example edge table
edges = conn.create_table(
    'edges',
    schema={
        'source': 'int64',
        'target': 'int64',
        'weight': 'float64'
    }
)

# Create a graph from the edges table
graph = ig.Graph(edges, source_col='source', target_col='target', weight_col='weight')

# Calculate degree metrics
degrees = graph.degrees()

# Find shortest paths
paths = graph.shortest_paths(sources=[1, 2, 3])

# Calculate PageRank
pagerank = graph.pagerank()
```

## Common Operations

Here are some common graph operations you can perform:

```python
# Get node degrees
in_degrees = graph.in_degrees()
out_degrees = graph.out_degrees()
total_degrees = graph.degrees()

# Find similar nodes
similar_nodes = graph.node_similarity(method='jaccard')

# Run community detection
communities = graph.label_propagation()
```

For more detailed examples and API reference, please refer to the full documentation.
