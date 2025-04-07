import pytest

from ibisgraph.clustering import label_propagation


def test_label_propagation(karate_club):
    rr = label_propagation(karate_club).to_pandas()
    assert rr.shape[0] == karate_club.num_nodes


if __name__ == "__main__":
    pytest.main()
