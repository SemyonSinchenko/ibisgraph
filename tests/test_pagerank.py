import ibis
import pytest

from ibisgraph.centrality.page_rank import page_rank


def test_karate_club(karate_club):
    g = karate_club
    pr = page_rank(g)
    rr = pr.select((ibis._.pagerank > 0).name("is_pr_gr_0")).distinct().to_pandas()
    assert len(rr) == 1
    assert rr.values[0]


if __name__ == "__main__":
    pytest.main()
