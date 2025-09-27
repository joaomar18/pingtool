from typing import Optional
from dataclasses import dataclass


@dataclass
class ViewRequestMetrics:
    callers_number: str
    total_number: str
    sucess_number: str
    error_number: str
    loss_percentage: str
    average_time_ms: str
    min_time_ms: str
    max_time_ms: str
    last_time_ms: str


@dataclass
class RequestMetrics:
    callers_number: int
    total_number: int = 0
    sucess_number: int = 0
    error_number: int = 0
    loss_percentage: float = 0.0
    average_time_ms: Optional[float] = None
    min_time_ms: Optional[float] = None
    max_time_ms: Optional[float] = None
    last_time_ms: Optional[float] = None

    def reset_values(self):
        self.total_number = 0
        self.sucess_number = 0
        self.error_number = 0
        self.loss_percentage = 0
        self.average_time_ms = 0
        self.min_time_ms = 0
        self.max_time_ms = 0
        self.last_time_ms = 0

    def get_values_formated(self, decimal_places: int = 2) -> "RequestMetrics":
        loss_percentage = round(self.loss_percentage, decimal_places)
        average_time_ms = round(self.average_time_ms, decimal_places) if self.average_time_ms is not None else None
        min_time_ms = round(self.min_time_ms, decimal_places) if self.min_time_ms is not None else None
        max_time_ms = round(self.max_time_ms, decimal_places) if self.max_time_ms is not None else None
        last_time_ms = round(self.last_time_ms, decimal_places) if self.last_time_ms is not None else None

        return RequestMetrics(
            callers_number=self.callers_number,
            total_number=self.total_number,
            sucess_number=self.sucess_number,
            error_number=self.error_number,
            loss_percentage=loss_percentage,
            average_time_ms=average_time_ms,
            min_time_ms=min_time_ms,
            max_time_ms=max_time_ms,
            last_time_ms=last_time_ms,
        )

    def convert_to_view(self, number_of_chars_for_null: int = 3) -> ViewRequestMetrics:

        null_value = "-" * number_of_chars_for_null

        return ViewRequestMetrics(
            callers_number=str(self.callers_number),
            total_number=str(self.total_number),
            sucess_number=str(self.sucess_number),
            error_number=str(self.error_number),
            loss_percentage=str(self.loss_percentage),
            average_time_ms=str(self.average_time_ms) if self.average_time_ms is not None else null_value,
            min_time_ms=str(self.min_time_ms) if self.min_time_ms is not None else null_value,
            max_time_ms=str(self.max_time_ms) if self.max_time_ms is not None else null_value,
            last_time_ms=str(self.last_time_ms) if self.last_time_ms is not None else null_value,
        )
