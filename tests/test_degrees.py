import pytest
from ibisgraph.centrality import degrees


def test_degrees(karate_club):
    g = karate_club
    deg = degrees(g).to_pandas()

    assert deg.loc[deg["node_id"] == 1, "degree"].values[0] == 16
    assert deg.loc[deg["node_id"] == 2, "degree"].values[0] == 9
    assert deg.loc[deg["node_id"] == 3, "degree"].values[0] == 10


if __name__ == "__main__":
    pytest.main()
