import pytest

from ibisgraph.similarity.similarity import jaccard_similarity


def test_jaccard(karate_club):
    jaccard = jaccard_similarity(karate_club).to_pandas()
    assert jaccard.loc[
        (jaccard["node_id_left"] == 1) & (jaccard["node_id_right"] == 33), "jaccard_similarity"
    ].values.reshape(-1).tolist()[0] == pytest.approx(0.12, 1e-4)


if __name__ == "__main__":
    pytest.main()
