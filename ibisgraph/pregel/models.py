from dataclasses import dataclass
from enum import Enum

from ibis import Value


class PregelConstants(Enum):
    MSG_COL_NAME = "_pregel_msg"
    ACTIVE_VERTEX_FLAG = "_active_flag"


@dataclass
class PregelVertexColumn:
    col_name: str
    initial_expr: Value
    update_expr: Value

@dataclass
class PregelMessage:
    target_column: Value
    msg_expr: Value
