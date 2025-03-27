from dataclasses import dataclass
from enum import Enum

from ibis import Deferred, Value


class PregelConstants(Enum):
    MSG_COL_NAME = "_pregel_msg"
    ACTIVE_VERTEX_FLAG = "_active_flag"


@dataclass
class PregelVertexColumn:
    col_name: str
    initial_expr: Value | Deferred
    update_expr: Value | Deferred

@dataclass
class PregelMessage:
    target_column: Value
    msg_expr: Value
