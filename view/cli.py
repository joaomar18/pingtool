import asyncio
import time
import random
from typing import Optional, Dict, Callable
from rich.live import Live
from rich.table import Table
from rich.console import Console
from models.request import ViewRequestMetrics
from models.queues import RequestUpdateMessage, RequestUpdateOperation

HandlerMethod = Callable[[RequestUpdateMessage], None]


class CLIView:

    __console = Console()
    __request_metrics: Dict[str, ViewRequestMetrics] = {}
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
        table.add_column("Sent")
        table.add_column("OK")
        table.add_column("NOK")
        table.add_column("Loss (%)")
        table.add_column("Avg (ms)")
        table.add_column("Last (ms)")
        table.add_column("Min. (ms)")
        table.add_column("Max. (ms)")

        return table

    @staticmethod
    def __render_table() -> Table:

        table = CLIView.__render_table_header()
        for address, metrics in CLIView.__request_metrics.items():
            table.add_row(
                address,
                metrics.total_number,
                metrics.sucess_number,
                metrics.error_number,
                metrics.loss_percentage,
                metrics.average_time_ms,
                metrics.last_time_ms,
                metrics.min_time_ms,
                metrics.max_time_ms,
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

        CLIView.__request_metrics[message.address] = message.metrics.convert_to_view()

    @staticmethod
    def __delete_request_entry(message: RequestUpdateMessage) -> None:
        CLIView.__request_metrics.pop(message.address)
