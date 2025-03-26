from enum import Enum

import ibis
from pandas.core.algorithms import is_integer
from typing_extensions import Self


class IbisGraphConstants(Enum):
    ID = "id_"
    SRC = "src_"
    DST = "dst_"
    WEIGHT = "weight_"
    EDGE = "edge_"


class IbisGraph:
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
        self._directed = value
        return self

    @property
    def nodes(self) -> ibis.Table:
        return self._nodes

    @property
    def edges(self) -> ibis.Table:
        return self._edges

    @property
    def num_nodes(self) -> int:
        return int(self._nodes.count().to_pandas())

    @property
    def num_edges(self) -> int:
        return int(self._edges.count().to_pandas())

    @property
    def directed(self) -> bool:
        return self._directed
