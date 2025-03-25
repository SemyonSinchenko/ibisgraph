import pytest


def test_num_nodes(karate_club):
    assert karate_club.num_nodes == 33


def test_num_edges(karate_club):
    assert karate_club.num_edges == 78


if __name__ == "__main__":
    pytest.main()
