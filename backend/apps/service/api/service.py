import asyncio
import websockets

import django

from threading import Thread

from ctypes import *

from apps.service.acdp.acdp import ACDP_UDP_PORT, ACDP_IP_ADDR
from .protocols import UDPProtocol, ws_client_data, ws_client_log, ws_graphs_client

TIME_TO_SEC = 150 * 1000000
#HOST = '192.168.0.100'
HOST = '0.0.0.0'

PORT = ACDP_UDP_PORT
WS_URI = "ws://localhost:8000/ws/micro/"


async def service():
    loop = asyncio.get_running_loop()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPProtocol(),
        local_addr=(HOST,PORT)
    )
    asyncio.ensure_future(ws_client_data())
    asyncio.ensure_future(ws_client_log())
    asyncio.ensure_future(ws_graphs_client())

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
         transport.close()


def start_service():
    loop = asyncio.new_event_loop()
    t = Thread(target=start_loop, args=(loop,), daemon=True)
    t.start()
    asyncio.run_coroutine_threadsafe(service(), loop)
    

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()