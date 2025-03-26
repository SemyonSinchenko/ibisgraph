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


if __name__ == "__main__":
    pytest.main()
