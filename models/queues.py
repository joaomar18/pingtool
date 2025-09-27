from enum import Enum
from typing import Optional
from dataclasses import dataclass
from models.request import RequestMetrics


class RequestUpdateOperation(str, Enum):
    UPDATE = "UPDATE"
    DELETE = "DELETE"


@dataclass
class RequestUpdateMessage:
    operation: RequestUpdateOperation
    address: str
    metrics: Optional[RequestMetrics] = None
