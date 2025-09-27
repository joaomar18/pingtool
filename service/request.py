import time
import asyncio
from typing import Optional, Callable, Awaitable
import ping3
from models.request import RequestMetrics

AsyncCallback = Callable[[str, RequestMetrics], Awaitable[None]]


class Request:
    def __init__(
        self,
        address: str,
        timeout: int = 10,
        request_family=None,
        polling_interval: float = 1,
        callers_number: int = 1,
        update_callback: AsyncCallback | None = None,
    ):
        self.address = address
        self.timeout = timeout
        self.request_family = request_family
        self.polling_interval = polling_interval
        self.callers_number = callers_number
        self.update_callback = update_callback
        self.metrics = RequestMetrics(callers_number=self.callers_number)

        self.average_time_sum_ms = 0.0

        self.task: Optional[asyncio.Task] = None

    async def start(self) -> None:

        if self.task is not None:
            raise RuntimeWarning(f"The request with address {self.address} is already started")
        self.task = asyncio.create_task(self.__manage_requests())

    async def stop(self) -> None:

        if self.task is None:
            raise RuntimeWarning(f"The request with address {self.address} is already stopped")

        self.task.cancel("Stopping task")
        try:
            await self.task
        except asyncio.CancelledError:
            if not self.task.done():
                raise RuntimeError(f"Request {self.address} did not end it's task sucessfully")

        self.task = None
        self.__reset_metrics()

    def set_update_callback(self, callback: AsyncCallback) -> None:
        self.update_callback = callback

    async def __manage_requests(self) -> None:

        initial_time, end_time, polling_interval = 0.0, 0.0, 0.0

        while True:
            initial_time = time.time()
            tasks = [self.__run_request() for i in range(self.callers_number)]
            await asyncio.gather(*tasks)
            end_time = time.time()
            polling_interval = self.polling_interval - (end_time - initial_time)
            if polling_interval > 0.0:
                await asyncio.sleep(polling_interval)

    async def __run_request(self) -> None:

        request_delay: Optional[float] = None

        try:
            thread = asyncio.to_thread(ping3.ping, self.address, self.timeout)
            ping_return = await thread
            if isinstance(ping_return, bool):
                request_delay = None
            else:
                request_delay = ping_return

        except Exception as e:
            print(f"Ping error for {self.address}: {type(e).__name__}: {e}")

        self.__update_metrics(request_delay)
        if self.update_callback:
            await self.update_callback(self.address, self.get_metrics())

    def __update_metrics(self, delay: Optional[float]) -> None:

        self.metrics.total_number += 1

        if delay is not None:

            delay *= 1000
            self.metrics.sucess_number += 1
            self.average_time_sum_ms += delay

            if self.metrics.average_time_ms is None:
                self.metrics.average_time_ms = delay

            else:
                self.metrics.average_time_ms = self.average_time_sum_ms / self.metrics.sucess_number

            if self.metrics.min_time_ms is None:
                self.metrics.min_time_ms = delay
            else:
                if self.metrics.min_time_ms > delay:
                    self.metrics.min_time_ms = delay

            if self.metrics.max_time_ms is None:
                self.metrics.max_time_ms = delay
            else:
                if self.metrics.max_time_ms < delay:
                    self.metrics.max_time_ms = delay

            self.metrics.last_time_ms = delay
        else:
            self.metrics.error_number += 1

        self.metrics.loss_percentage = (self.metrics.error_number / self.metrics.total_number) * 100

    def __reset_metrics(self) -> None:
        self.metrics.reset_values()

    def get_metrics(self) -> RequestMetrics:
        return self.metrics.get_values_formated()

    def __hash__(self) -> int:
        return hash((self.address,))
