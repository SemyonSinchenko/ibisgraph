# IbisGraph

*Under development!*

<p align="center">
  <img src="https://github.com/SemyonSinchenko/ibisgraph/blob/initial-development/static/logo.png?raw=true" alt="IbisGraph logo" width="600px"/>
</p>

IbisGraph is an experimental implementation of [Pregel](https://research.google/pubs/pregel-a-system-for-large-scale-graph-processing/) on top of [Ibis](https://ibis-project.org/) DataFrames.

## Features

- Quite fast on single-node with `DuckDB` backend!
- Write once, debug locally, run on a Database or cluster!
- Theoretically support all the supported by Ibis backends (Snwoflake, PostgreSQL, PySpark, etc.)!
- Not only Pregel: batteries are included!

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
- [ ] Betweenness centrality
- [ ] Gremlin
- [ ] OpenCypher

## Inspirations

- [GraphFrames](https://github.com/graphframes/graphframes)
- [Spark GraphX](https://spark.apache.org/graphx/)
