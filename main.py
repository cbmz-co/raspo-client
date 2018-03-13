#!/usr/bin/env python3
import asyncio
import websockets
import pyspeedtest
import json
from uuid import getnode as get_mac

# TODO rewrite for python >3.4

MAC_ADDRESS = str(get_mac())
USR_TOKEN = input('Type your token: ')


async def send_speed_test(ws):
    st = pyspeedtest.SpeedTest()
    ping = st.ping()
    download_speed = pyspeedtest.pretty_speed(st.download())
    upload_speed = pyspeedtest.pretty_speed(st.upload())
    msg = {'token': USR_TOKEN, 'mac': MAC_ADDRESS, 'ping': ping, 'dw_speed': download_speed, 'up_speed': upload_speed}
    json_msg = json.dumps(msg)
    await ws.send(json_msg)


async def open_ws(uri):
    async with websockets.connect(uri) as ws:
        msg = {'token': USR_TOKEN, 'mac': MAC_ADDRESS}
        json_msg = json.dumps(msg)
        await ws.send(json_msg)
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
                # TODO Switch messages
                print("Received a message: {" + msg + "}")
                try:
                    await asyncio.wait_for(send_speed_test(ws), timeout=30)
                except (asyncio.TimeoutError, websockets.ConnectionClosed) as error:
                    print(error)
                    print("There are network problems... soon i'm trying to reconnect to the web socket.")
                    return


async def main():
    while True:
        try:
            await open_ws('wss://ywxygb7-raspobackend.wedeploy.io/ciao')
            await asyncio.sleep(10)
        except (asyncio.TimeoutError, websockets.ConnectionClosed) as error:
            print(error)
            print("There are network problems... soon i'm trying to reconnect to the web socket.")
            await asyncio.sleep(60)
        except Exception as e:
            print(e)
            print("Something went wrong... retry.")
            await asyncio.sleep(60)


event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(main())



