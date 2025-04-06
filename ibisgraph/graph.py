from enum import Enum

import ibis
from typing_extensions import Self


class IbisGraphConstants(Enum):
    """Constants for standardizing column names and identifiers in graph data structures.

    These constants provide a consistent naming convention for graph-related columns
    to ensure compatibility and ease of use across different graph processing operations.
    """

    ID = "id_"
    SRC = "src_"
    DST = "dst_"
    WEIGHT = "weight_"
    EDGE = "edge_"


class IbisGraph:
    """A graph representation using Ibis tables for nodes and edges.

    This class provides a flexible graph data structure that can handle:
    - Directed and undirected graphs
    - Optional weighted edges
    - Integer-based node and edge identifiers

    Attributes:
        nodes (ibis.Table): Table containing node information.
        edges (ibis.Table): Table containing edge connections.
        directed (bool): Whether the graph is directed or undirected.
        num_nodes (int): Total number of nodes in the graph.
        num_edges (int): Total number of edges in the graph.
    """

    def __init__(
        self,
        nodes: ibis.Table,
        edges: ibis.Table,
        directed: bool = False,
        id_col: str = "id",
        src_col: str = "src",
        dst_col: str = "dst",
        weight_col: str | None = None,
    ) -> None:
        """Initialize an IbisGraph with nodes and edges.

        Args:
            nodes: Table containing node information.
            edges: Table containing edge connections.
            directed: Whether the graph is directed. Defaults to False.
            id_col: Column name for node IDs. Defaults to "id".
            src_col: Column name for source node in edges. Defaults to "src".
            dst_col: Column name for destination node in edges. Defaults to "dst".
            weight_col: Column name for edge weights. Defaults to None.

        Raises:
            ValueError: If input columns are missing or have incorrect data types.
        """
        if id_col not in nodes.schema().keys():
            raise ValueError(
                f"ID column {id_col} is not present. Did you mean one of {nodes.schema().names}"
            )

        if not nodes.schema()[id_col].is_integer():
            raise ValueError(
                f"ID data type is {nodes.schema()[id_col]} but only integer-like types are supported for nodes!"
            )
        if src_col not in edges.schema().keys():
            raise ValueError(
                f"ID column {src_col} is not present. Did you mean one of {edges.schema().names}"
            )
        if dst_col not in edges.schema().keys():
            raise ValueError(
                f"ID column {dst_col} is not present. Did you mean one of {edges.schema().names}"
            )

        if not edges.schema()[src_col].is_integer():
            raise ValueError(
                f"SRC data type is {edges.schema()[src_col]} but only integer-like types are supported for nodes!"
            )

        if not edges.schema()[dst_col].is_integer():
            raise ValueError(
                f"DST data type is {edges.schema()[dst_col]} but only integer-like types are supported for nodes!"
            )

        self._nodes = nodes.rename({IbisGraphConstants.ID.value: id_col})
        self._edges = edges.rename(
            {IbisGraphConstants.SRC.value: src_col, IbisGraphConstants.DST.value: dst_col}
        )
        if weight_col is not None:
            self._edges = self._edges.rename({IbisGraphConstants.WEIGHT.value: weight_col})
            self._is_weighted = True
        else:
            self._is_weighted = False
        self._directed = directed

    def set_directed(self, value: bool) -> Self:
        """Set the directionality of the graph.

        Args:
            value: Whether the graph should be directed or undirected.

        Returns:
            The current graph instance for method chaining.
        """
        self._directed = value
        return self

    @property
    def nodes(self) -> ibis.Table:
        """Get the nodes table of the graph.

        Returns:
            A table containing node information with node identifiers.
        """
        return self._nodes

    @property
    def edges(self) -> ibis.Table:
        """Get the edges table of the graph.

        Returns:
            A table containing edges information with edges identifiers.
        """
        return self._edges

    @property
    def num_nodes(self) -> int:
        """Get the number of nodes in the graph.

        Returns:
            The total number of nodes in the graph.
        """
        return int(self._nodes.count().to_pandas())

    @property
    def num_edges(self) -> int:
        """Get the number of edges in the graph.

        Returns:
            The total number of edges in the graph.
        """
        return int(self._edges.count().to_pandas())

    @property
    def is_directed(self) -> bool:
        """Check if the graph is directed.

        Returns:
            True if the graph is directed, False otherwise.
        """
        return self._directed
