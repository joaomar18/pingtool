import asyncio
from typing import Optional, Dict, Callable
from rich.live import Live
from rich.table import Table
from models.request import RequestMetrics
from models.queues import RequestUpdateMessage, RequestUpdateOperation
import util.view as util

HandlerMethod = Callable[[RequestUpdateMessage], None]


class CLIView:

    __BLOCKS = "▁▂▃▄▅▆▇█"
    __BLOCKS_LEVELS = 8
    __request_metrics: Dict[str, RequestMetrics] = {}
    __update_queue: Optional[asyncio.Queue[RequestUpdateMessage]] = None
    __handler_methods: Dict[RequestUpdateOperation, HandlerMethod] = {}

    @staticmethod
    def set_update_queue(queue: asyncio.Queue[RequestUpdateMessage]) -> None:
        CLIView.__update_queue = queue

    @staticmethod
    def __init_handler_methods() -> None:
        CLIView.__handler_methods[RequestUpdateOperation.UPDATE] = CLIView.__update_request_entry
        CLIView.__handler_methods[RequestUpdateOperation.DELETE] = CLIView.__delete_request_entry

    @staticmethod
    def __render_table_header() -> Table:
        table = Table(show_header=True, header_style="bold green")
        table.add_column("Host")
        table.add_column("Callers")
        table.add_column("Sent")
        table.add_column("OK")
        table.add_column("NOK")
        table.add_column("Loss (%)")
        table.add_column("Avg (ms)")
        table.add_column("Last (ms)")
        table.add_column("Min. (ms)")
        table.add_column("Max. (ms)")
        table.add_column("Trend", no_wrap=True)

        return table

    @staticmethod
    def __render_histogram(metrics: RequestMetrics) -> str:

        trend: str = ""
        in_min_value = metrics.min_time_ms
        in_max_value = metrics.max_time_ms
        out_min_value = 0
        out_max_value = CLIView.__BLOCKS_LEVELS - 1

        if in_min_value is None or in_max_value is None or in_min_value == in_max_value:
            return trend

        histogram_copy = metrics.histogram_values.copy()

        while len(histogram_copy) > 0:
            value = histogram_copy.popleft()
            if value is None:
                trend += " "
                continue

            trend_value = util.scale_value(x=value, in_min=in_min_value, in_max=in_max_value, out_min=out_min_value, out_max=out_max_value)
            trend_value = round(trend_value)
            if trend_value < out_min_value:
                trend_value = out_min_value
            elif trend_value > out_max_value:
                trend_value = out_max_value

            trend += str(CLIView.__BLOCKS[trend_value])

        return trend

    @staticmethod
    def __render_table() -> Table:

        table = CLIView.__render_table_header()
        for address, metrics in CLIView.__request_metrics.items():
            view_metrics = metrics.convert_to_view()
            table.add_row(
                address,
                view_metrics.callers_number,
                view_metrics.total_number,
                view_metrics.sucess_number,
                view_metrics.error_number,
                view_metrics.loss_percentage,
                view_metrics.average_time_ms,
                view_metrics.last_time_ms,
                view_metrics.min_time_ms,
                view_metrics.max_time_ms,
                CLIView.__render_histogram(metrics),
            )

        return table

    @staticmethod
    def init() -> None:
        CLIView.__init_handler_methods()
        asyncio.create_task(CLIView.__receive_updates())

    @staticmethod
    def __handle_refresh(screen: Live) -> None:
        screen.update(CLIView.__render_table(), refresh=True)

    @staticmethod
    async def __receive_updates() -> None:
        if CLIView.__update_queue is None:
            raise RuntimeError(f"Update Queue is not defined in the CLI View")

        with Live(CLIView.__render_table(), auto_refresh=False) as live:
            while True:
                message = await CLIView.__update_queue.get()
                method = CLIView.__handler_methods.get(message.operation)
                if not method:
                    raise KeyError(f"Received message of address {message.address} with unknown operation {message.operation}.")

                method(message)
                CLIView.__handle_refresh(live)

    @staticmethod
    def __update_request_entry(message: RequestUpdateMessage) -> None:
        if message.metrics is None:
            raise KeyError(f"Received message of address {message.address} with update operation but without metrics.")

        CLIView.__request_metrics[message.address] = message.metrics

    @staticmethod
    def __delete_request_entry(message: RequestUpdateMessage) -> None:
        CLIView.__request_metrics.pop(message.address)
