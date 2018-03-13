#!/usr/bin/env python3
import asyncio
import websockets
import pyspeedtest
import json
from uuid import getnode as get_mac

MAC_ADDRESS = str(get_mac())
USR_TOKEN = input('Type your token: ')


@asyncio.coroutine
def send_speed_test(ws):
    st = pyspeedtest.SpeedTest()
    ping = round(st.ping(), 2)
    download_speed = pyspeedtest.pretty_speed(st.download())
    upload_speed = pyspeedtest.pretty_speed(st.upload())
    msg = {'token': USR_TOKEN, 'mac': MAC_ADDRESS, 'ping': ping, 'dw_speed': download_speed, 'up_speed': upload_speed}
    json_msg = json.dumps(msg)
    yield from ws.send(json_msg)


@asyncio.coroutine
def open_ws(uri):
    ws = yield from websockets.connect(uri)
    msg = {'token': USR_TOKEN, 'mac': MAC_ADDRESS}
    json_msg = json.dumps(msg)
    yield from ws.send(json_msg)
    while True:
        try:
            print("Waiting instruction from backend...")
            msg = yield from asyncio.wait_for(ws.recv(), timeout=60)
        except websockets.ConnectionClosed:
            print("The connection is closed,  i try to reconnect!")
            return
        except asyncio.TimeoutError:
            # No data in 60 seconds, check the connection.
            try:
                pong_waiter = yield from ws.ping()
                yield from asyncio.wait_for(pong_waiter, timeout=10)
            except asyncio.TimeoutError:
                # No response to ping in 10 seconds, disconnect.
                print("No response from server, i try to reconnect!")
                ws.close()
                return
        else:
            # TODO Switch messages
            print("Received a message: " + msg )
            try:
                yield from asyncio.wait_for(send_speed_test(ws), timeout=30)
            except (asyncio.TimeoutError, websockets.ConnectionClosed) as error:
                print(error)
                print("There are network problems... soon i'm trying to reconnect to the web socket.")
                return


@asyncio.coroutine
def main():
    while True:
        try:
            yield from open_ws('wss://ywxygb7-raspobackend.wedeploy.io/ciao')
            yield from asyncio.sleep(10)
        except (asyncio.TimeoutError, websockets.ConnectionClosed) as error:
            print(error)
            print("There are network problems... soon i'm trying to reconnect to the web socket.")
            yield from asyncio.sleep(60)
        except Exception as e:
            print(e)
            print("Something went wrong... retry.")
            yield from asyncio.sleep(60)


event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(main())



