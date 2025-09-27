import asyncio
from typing import List, Dict, Optional
from service.request import Request, RequestMetrics
from models.queues import RequestUpdateMessage, RequestUpdateOperation


class PingManager:
    __requests: Dict[str, List[Request]] = {}
    __update_queue: Optional[asyncio.Queue[RequestUpdateMessage]] = None

    @staticmethod
    def set_update_queue(queue: asyncio.Queue[RequestUpdateMessage]) -> None:
        PingManager.__update_queue = queue

    @staticmethod
    async def add_request(request: Request):

        request.set_update_callback(PingManager.__request_updated_handler)
        await request.start()

        if PingManager.__requests.get(request.address) is None:
            PingManager.__requests[request.address] = [request]
        else:
            PingManager.__requests[request.address].append(request)

    @staticmethod
    async def add_request_list(list: List[Request]):
        for request in list:
            await PingManager.add_request(request)

    @staticmethod
    async def remove_requests_by_address(address: str) -> None:

        requests_list = PingManager.__requests.get(address)
        if requests_list is None:
            raise KeyError(f"The address {address} is not active in the Ping Manager.")

        requests = [request for request in requests_list if request.address == address]

        for request in requests:
            await request.stop()

        if PingManager.__update_queue is None:
            raise RuntimeError(f"Update Queue is not defined in the Ping Manager")

        await PingManager.__update_queue.put(RequestUpdateMessage(RequestUpdateOperation.DELETE, address, None))

        PingManager.__requests.pop(address)

    @staticmethod
    async def __request_updated_handler(address: str, metrics: RequestMetrics):
        if PingManager.__update_queue is None:
            raise RuntimeError(f"Update Queue is not defined in the Ping Manager")

        await PingManager.__update_queue.put(RequestUpdateMessage(RequestUpdateOperation.UPDATE, address, metrics))
