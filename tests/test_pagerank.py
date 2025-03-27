import ibis
import pytest

from ibisgraph.centrality.page_rank import page_rank
from ibisgraph.graph import IbisGraph


def test_karate_club(karate_club):
    pr = page_rank(karate_club)
    rr = pr.select((ibis._.pagerank > 0).name("is_pr_gr_0")).distinct().to_pandas()
    assert len(rr) == 1
    assert rr.values[0]
    assert pr.select(ibis._.pagerank).to_pandas()["pagerank"].sum() == pytest.approx(1.0, 1e-4)


def test_simple_graph():
    nodes = ibis.memtable(
        {
            "id": [
                0,
                1,
                2,
                3,
                4,
            ]
        }
    )
    edges = ibis.memtable(
        {
            "src": [
                0,
                1,
                2,
                2,
                3,
                4,
                4,
            ],
            "dst": [1, 2, 4, 0, 4, 0, 2],
        }
    )
    g = IbisGraph(nodes, edges, directed=True)
    pr = page_rank(g, max_iters=5)
    rr = pr.order_by("node_id").select(ibis._.pagerank).to_pandas().values.reshape(-1).tolist()
    assert sum(rr) == pytest.approx(1.0, 1e-4)
    assert all(abs(real - exp) < 0.005 for real, exp in zip(rr, [0.245, 0.224, 0.303, 0.03, 0.197]))


if __name__ == "__main__":
    pytest.main()
