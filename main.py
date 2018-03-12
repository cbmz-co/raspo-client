#!/usr/bin/env python3
import asyncio
import websockets
import pyspeedtest
from uuid import getnode as get_mac


async def send_speed_test(ws):
    st = pyspeedtest.SpeedTest()
    speed = pyspeedtest.pretty_speed(st.download())
    await ws.send("MAC Address:"+mac+" Download Speed: "+speed)


async def open_ws(uri):
    async with websockets.connect(uri) as ws:
        mac = str(get_mac())
        await ws.send("MAC Address:" + mac)
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=60)
            except websockets.ConnectionClosed:
                print("Connection is closed, try to reconnect!")
                return
            except asyncio.TimeoutError:
                # No data in 60 seconds, check the connection.
                try:
                    pong_waiter = await ws.ping()
                    await asyncio.wait_for(pong_waiter, timeout=10)
                except asyncio.TimeoutError:
                    # No response to ping in 10 seconds, disconnect.
                    print("No response, try to reconnect!")
                    ws.close()
                    return
            else:
                print("Received a message: {" + msg + "}")
                try:
                    await asyncio.wait_for(send_speed_test(ws), timeout=30)
                except (asyncio.TimeoutError, websockets.ConnectionClosed) as error:
                    print(error)
                    return


async def main():
    while True:
        try:
            await open_ws('wss://ywxygb7-raspobackend.wedeploy.io/ciao')
            await asyncio.sleep(10)
        except:
            print("Something went wrong... retry connection.")
            await asyncio.sleep(60)


event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(main())



