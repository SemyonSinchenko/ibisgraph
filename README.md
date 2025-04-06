<h1 style="text-align: center"><b>IbisGraph</b></h1>

*Under development!*

[![Tests and Code Style](https://github.com/SemyonSinchenko/ibisgraph/actions/workflows/python-ci.yml/badge.svg)](https://github.com/SemyonSinchenko/ibisgraph/actions/workflows/python-ci.yml)[![deploy-docs](https://github.com/SemyonSinchenko/ibisgraph/actions/workflows/docs.yml/badge.svg)](https://github.com/SemyonSinchenko/ibisgraph/actions/workflows/docs.yml)[![Upload Python Package](https://github.com/SemyonSinchenko/ibisgraph/actions/workflows/python-publish.yml/badge.svg)](https://github.com/SemyonSinchenko/ibisgraph/actions/workflows/python-publish.yml)

<p align="center">
  <img src="https://raw.githubusercontent.com/SemyonSinchenko/ibisgraph/refs/heads/main/static/logo.png" alt="IbisGraph logo" width="600px"/>
</p>

## Idea

IbisGraph brings graph processing capabilities to your data warehouse or lake house by implementing the Pregel computation model on top of [Ibis](https://ibis-project.org/). This means you can perform graph analytics directly where your data lives, without moving it to specialized graph databases or in-memory systems.

Key benefits:
- Process graph data in your existing data infrastructure
- Scale with your warehouse/lake resources
- Maintain data governance and security
- Leverage SQL engine optimizations

Supported backends include:
- DuckDB
- PostgreSQL
- SQLite
- Snowflake
- BigQuery
- Apache Spark
- And [many others](https://ibis-project.org/backends/) supported by Ibis

## Quick Start

Install IbisGraph using pip:

```bash
pip install ibisgraph
```

You'll also need to install the appropriate Ibis backend. For example:

```bash
# For DuckDB
pip install "ibis-framework[duckdb]"

# For PostgreSQL
pip install "ibis-framework[postgres]"

# For Snowflake
pip install "ibis-framework[snowflake]"
```

Basic usage:

```python
import ibis
import ibisgraph as ig

# Connect to your database
conn = ibis.duckdb.connect()

# Create a graph
graph = ig.Graph(nodes_table, edges_table)

# Run algorithms
pagerank = ig.centrality.pagerank(graph)
communities = ig.clustering.label_propagation(graph)
similarities = ig.similarity.node_similarity(graph)
```

For more detailed examples, check our [documentation](https://semyonsinchenko.github.io/ibisgraph/).

## FAQ

Is it a replacement for graph libraries like NetworkX or IGraph?

- *No, IbisGraph is not a replacement for traditional graph libraries. While it implements graph algorithms using Pregel (which can be expressed in SQL), it will generally be slower than specialized implementations. Its value comes from being able to process graph data where it already lives.*

Will it work on Databricks, Snowflake, PostgreSQL, etc.?

- *Yes. IbisGraph works with any backend [supported by Ibis](https://ibis-project.org/backends/support/matrix).*

Why Pregel?

- *Pregel operations can be naturally expressed using SQL operations, making it ideal for implementing graph algorithms in data warehouses and lakes.*

Is it better than GraphFrames for PySpark users?

- *As a GraphFrames committer, I can say that GraphFrames algorithms are generally better optimized for Apache Spark. However, IbisGraph provides a more Pythonic API and doesn't require JVM configuration.*

When should I use IbisGraph?

- *Use IbisGraph when you need to process connected data stored in a database, datalake, or warehouse system without moving it out. While algorithms may run slower compared to specialized tools like Neo4j, the main advantage is processing data in place.*

## Features and Roadmap

Implemented:
- [x] Graph abstraction using Ibis Tables
- [x] Degree calculations (in/out/total)
- [x] Jaccard similarity index
- [x] Pregel computation framework
- [x] PageRank algorithm
- [x] Shortest Paths
- [x] Label Propagation

Coming soon:
- [ ] Weakly Connected Components
- [ ] Strongly Connected Components
- [ ] Attribute Propagation
- [ ] Random Walks
- [ ] Node2vec
- [ ] Gremlin support
- [ ] OpenCypher support
- [ ] *The feature you will suggest*

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/SemyonSinchenko/ibisgraph.git
cd ibisgraph
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

3. Install development dependencies:
```bash
uv sync --all-groups
```

### Development Standards

We use:
- [ruff](https://github.com/astral-sh/ruff) for linting and formatting
- [pytest](https://docs.pytest.org/) for testing
- [uv](https://github.com/astral-sh/uv) for dependency management
- [DuckDB](https://duckdb.org/) for testing

### Development Process

1. **Pick an Issue**
    - Check existing issues or create a new one
    - Comment on the issue you want to work on

2. **Fork & Branch**
    - Fork the repository
    - Create a feature branch

3. **Development**
    - Write tests first
    - Implement your changes
    - Run tests: `pytest`
    - Run linter: `ruff check .`
    - Format code: `ruff format .`

4. **Submit PR**
    - Create a Pull Request
    - Wait for review
    - Address feedback

### Project Philosophy

IbisGraph follows the [Benevolent Dictator governance model](https://en.wikipedia.org/wiki/Benevolent_dictator_for_life). While we welcome all contributions, final decisions rest with the project maintainer to ensure consistent direction.

## Inspirations

- [GraphFrames](https://github.com/graphframes/graphframes)
- [Spark GraphX](https://spark.apache.org/graphx/)
- [PySpark Graph](https://github.com/aktungmak/pyspark-graph)
- [Pregel: a system for large-scale graph processing](https://research.google/pubs/pregel-a-system-for-large-scale-graph-processing/)
