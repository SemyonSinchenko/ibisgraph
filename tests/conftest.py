import pathlib
from dataclasses import dataclass

import ibis
import pytest

from ibisgraph import IbisGraph

PROJECT_ROOT = pathlib.Path(__file__).parent.parent


@dataclass
class LDBCDataset:
    name: str
    graph: IbisGraph
    bfs_results: ibis.Table
    properties: dict[str, str]


@pytest.hookimpl()
def pytest_sessionstart(session):
    ibis.connect("duckdb://")
    ibis.options.interactive = False


@pytest.hookimpl()
def pytest_sessionfinish(session):
    ibis.get_backend().disconnect()


@pytest.fixture
def chain_graph():
    n = 5
    nodes = ibis.memtable({"id": list(range(1, n + 1))})
    edges = ibis.memtable({"src": list(range(1, n)), "dst": list(range(2, n + 1))})

    yield IbisGraph(nodes, edges)


@pytest.fixture
def karate_club():
    # https://en.wikipedia.org/wiki/Zachary%27s_karate_club
    original_edges = [
        [2, 1],
        [3, 1],
        [3, 2],
        [4, 1],
        [4, 2],
        [4, 3],
        [5, 1],
        [6, 1],
        [7, 1],
        [7, 5],
        [7, 6],
        [8, 1],
        [8, 2],
        [8, 3],
        [8, 4],
        [9, 1],
        [9, 3],
        [10, 3],
        [11, 1],
        [11, 5],
        [11, 6],
        [12, 1],
        [13, 1],
        [13, 4],
        [14, 1],
        [14, 2],
        [14, 3],
        [14, 4],
        [17, 6],
        [17, 7],
        [18, 1],
        [18, 2],
        [20, 1],
        [20, 2],
        [22, 1],
        [22, 2],
        [26, 24],
        [26, 25],
        [28, 3],
        [28, 24],
        [28, 25],
        [29, 3],
        [30, 24],
        [30, 27],
        [31, 2],
        [31, 9],
        [32, 1],
        [32, 25],
        [32, 26],
        [32, 29],
        [33, 3],
        [33, 9],
        [33, 15],
        [33, 16],
        [33, 19],
        [33, 21],
        [33, 23],
        [33, 24],
        [33, 30],
        [33, 31],
        [33, 32],
        [34, 9],
        [34, 10],
        [34, 14],
        [34, 15],
        [34, 16],
        [34, 19],
        [34, 20],
        [34, 21],
        [34, 23],
        [34, 24],
        [34, 27],
        [34, 28],
        [34, 29],
        [34, 30],
        [34, 31],
        [34, 32],
        [34, 33],
    ]

    nodes = ibis.memtable({"id": list(range(1, 35))})
    edges = ibis.memtable(
        {"src": [ee[0] for ee in original_edges], "dst": [ee[1] for ee in original_edges]}
    )

    yield IbisGraph(nodes, edges)


@pytest.fixture
def ldbc_kgs():
    ldbc_kgs_root = PROJECT_ROOT.joinpath("resources").joinpath("ldbc").joinpath("kgs")
    nodes = ibis.read_csv(ldbc_kgs_root.joinpath("kgs.v"), delim=" ", header=False, names=["id"])
    edges = ibis.read_csv(
        ldbc_kgs_root.joinpath("kgs.e"), delim=" ", header=False, names=["src", "dst", "weight"]
    )
    graph = IbisGraph(nodes, edges, directed=False)

    bfs_results = ibis.read_csv(
        ldbc_kgs_root.joinpath("kgs-BFS"), delim=" ", header=False, names=["node_id", "distance"]
    )
    properties = {}
    with ldbc_kgs_root.joinpath("kgs.properties").open("r") as file:
        for line in file:
            if "=" in line:
                key, value = line.split("=", 1)
                properties[key.strip()] = value.strip()

    yield LDBCDataset(
        name="kgs",
        graph=graph,
        bfs_results=bfs_results,
        properties=properties,
    )
