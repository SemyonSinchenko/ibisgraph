import ibis
import pytest

from ibisgraph.clustering import label_propagation


def test_label_propagation(karate_club):
    rr = label_propagation(karate_club)
    label_counts = rr.group_by(rr["label"]).aggregate(ibis._.count().name("cnt")).to_pandas()
    # it looks like it is deterministic with duckdb backend
    assert label_counts.shape[0] == 7
    assert (
        label_counts.sort_values("cnt", ascending=True)["cnt"].values.reshape(-1).tolist()[0] == 2
    )


if __name__ == "__main__":
    pytest.main()
