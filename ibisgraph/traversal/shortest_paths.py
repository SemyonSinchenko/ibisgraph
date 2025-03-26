from collections.abc import Sequence

import ibis

from ibisgraph import IbisGraph


def shortest_paths(graph: IbisGraph, landmarks: Sequence[int]) -> ibis.Table: ...
