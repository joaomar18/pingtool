import asyncio

request_update_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
