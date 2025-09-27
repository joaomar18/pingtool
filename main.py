import asyncio
import signal
from service.request import Request
from service.manager import PingManager
from view.cli import CLIView
import data.queues


shutdown_event = asyncio.Event()


def shutdown() -> None:
    print(f"Shutting down tool...")
    shutdown_event.set()


async def add_shutdown_handlers() -> None:
    for sig in (signal.SIGTERM, signal.SIGINT):
        asyncio.get_running_loop().add_signal_handler(sig, shutdown)


async def clean_up_tasks() -> None:

    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]

    if tasks:
        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)


async def main() -> None:
    await add_shutdown_handlers()

    PingManager.set_update_queue(data.queues.request_update_queue)
    CLIView.set_update_queue(data.queues.request_update_queue)

    google_ping = Request(address="www.google.pt", polling_interval=0.1, callers_number=10)
    home_ping = Request(address="192.168.0.20", polling_interval=0.01)
    await PingManager.add_request_list([google_ping, home_ping])
    CLIView.init()

    await shutdown_event.wait()
    await clean_up_tasks()


if __name__ == "__main__":
    asyncio.new_event_loop().run_until_complete(main())
