# IbisGraph

*Under development!*

<p align="center">
  <img src="https://github.com/SemyonSinchenko/ibisgraph/blob/initial-development/static/logo.png?raw=true" alt="IbisGraph logo" width="600px"/>
</p>

![](./static/logo.png)

IbisGraph is an experimental implementation of [Pregel](https://research.google/pubs/pregel-a-system-for-large-scale-graph-processing/) on top of [Ibis](https://ibis-project.org/) `DataFrames`.

## Features

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
