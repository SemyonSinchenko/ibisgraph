import ibis
import pytest

from ibisgraph import IbisGraphConstants
from ibisgraph.pregel import Pregel

from .utils import assert_ibis_all


def test_chain(chain_graph) -> None:
    g = chain_graph

    pregel = Pregel(g)
    result = (
        pregel.add_vertex_col(
            "value",
            ibis.ifelse(
                ibis._[IbisGraphConstants.ID.value] == ibis.literal(1),
                ibis.literal(1),
                ibis.literal(0),
            ),
            ibis.ifelse(
                pregel.pregel_msg() > ibis._.value,
                pregel.pregel_msg(),
                ibis._.value,
            ),
        )
        .add_message_to_dst(
            ibis.ifelse(
                pregel.pregel_dst("value") <= pregel.pregel_src("value"),
                pregel.pregel_src("value"),
                ibis.null("int"),
            )
        )
        .set_agg_expression_func(lambda msg: msg.collect().maxs())
        .run()
    )

    assert assert_ibis_all(result, ibis._.value == ibis.literal(1))


if __name__ == "__main__":
    pytest.main()
