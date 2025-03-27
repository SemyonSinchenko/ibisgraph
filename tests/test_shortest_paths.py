import os

import ibis
import pytest

from ibisgraph.traversal import shortest_paths


def test_karate(karate_club):
    sp = shortest_paths(karate_club, [1, 34])
    rr = (
        sp.order_by("node_id")
        .select(sp["distances"]["distance_to_1"].name("dist"))
        .to_pandas()
        .values.reshape(-1)
        .tolist()
    )

    assert rr[:5] == [0, 1, 1, 1, 1]
    assert rr[-1] == 2


@pytest.mark.skipif("TEST_LDBC" not in os.environ, reason="Disable long-running tests in CI")
def test_ldbc_kgs(ldbc_kgs):
    landmarks = [int(ldbc_kgs.properties.get(f"graph.{ldbc_kgs.name}.bfs.source-vertex"))]
    rr = shortest_paths(ldbc_kgs.graph, landmarks).cache()
    rr = rr.select(rr["node_id"], rr["distances"][f"distance_to_{landmarks[0]}"].name("got"))
    with_expected = rr.left_join(
        ldbc_kgs.bfs_results,
        ["node_id"],
    )
    print(with_expected.head().to_pandas())
    assert with_expected.count().to_pandas() == ldbc_kgs.graph.num_nodes
    assert with_expected.filter(ibis._["got"] != ibis._["distance"]).count().to_pandas() == 0


if __name__ == "__main__":
    pytest.main()
