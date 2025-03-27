<h1 style="text-align: center"><b>IbisGraph</b></h1>

*Under development!*

[![Tests and Code Style](https://github.com/SemyonSinchenko/ibisgraph/actions/workflows/python-ci.yml/badge.svg)](https://github.com/SemyonSinchenko/ibisgraph/actions/workflows/python-ci.yml)

<p align="center">
  <img src="https://raw.githubusercontent.com/SemyonSinchenko/ibisgraph/refs/heads/main/static/logo.png" alt="IbisGraph logo" width="600px"/>
</p>

IbisGraph is an experimental implementation of [Pregel](https://research.google/pubs/pregel-a-system-for-large-scale-graph-processing/) on top of [Ibis](https://ibis-project.org/) DataFrames.

## FAQ

Is it a replacement of graph-libraries, like NetworkX or IGraph?

- *No, this is not a replacement for graph libraries. While IbisGraph is based on Pregel, which was designed for large-scale graph processing and can be easily explained in terms of SQL, it will always be significantly slower compared to other implementations of graph algorithms.*

Will it work on Databricks, Snowflake, PostgrSQL, etc.?

- *Yes. IbisGraph should work with any backend, [supported](https://ibis-project.org/backends/support/matrix) in Ibis.*

Why Pregel?

- *I do not know an alternative graph-processing framework, that can be so easily explained in terms of SQL-operations.*

Is it better than GraphFrames for PySpark users?

- *As a committer of the GraphFrames project, I can say that GraphFrames algorithms are generally better optimized for Apache Spark's specific features. However, I believe that IbisGraph's API is more Pythonic compared to GraphFrames' PySpark API. Additionally, IbisGraph doesn't require extra steps, such as building JARs and configuring the cluster, to run it.*

When should I use IbisGraph?

- *I designed IbisGraph for cases where users need to process connected data stored in a Database, Lakehouse, or cloud Data Warehouse (DWH) system. IbisGraph provides graph abstractions and implementations of graph algorithms that run on the database, cloud DWH, or query engine side. While the implementations of graph algorithms in IbisGraph are generally slower compared to specialized tools like Neo4j, IbisGraph's main advantage is that it doesn't require moving data outside of the target system.*

## Features

- Quite fast on single-node with `DuckDB` backend.
- Write once, debug locally, run on a Database or cluster.
- Theoretically support all the supported by Ibis backends (Snwoflake, PostgreSQL, PySpark, etc.).
- Not only Pregel: batteries are included.

## Implemented algorithms

- [x] Graph abstraction, represented by two `ibis.Table` (nodes and edges)
- [x] In-degrees, out-degrees, degrees
- [x] Jaccard similarity index
- [x] Pregel as a low-level building block for Graph processing
- [x] PageRank
- [x] Shortest Paths
- [x] Label Propagation
- [ ] Weakly Connected Components
- [ ] Strongly Connected Components
- [ ] Attribute Propagation
- [ ] Gremlin
- [ ] OpenCypher

## Inspirations

- [GraphFrames](https://github.com/graphframes/graphframes)
- [Spark GraphX](https://spark.apache.org/graphx/)
- [PySpark Graph](https://github.com/aktungmak/pyspark-graph)
- [Pregel: a system for large-scale graph processing](https://research.google/pubs/pregel-a-system-for-large-scale-graph-processing/)
