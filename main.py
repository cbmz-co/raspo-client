#!/usr/bin/env python3
import asyncio
import websockets
import pyspeedtest
import json
from uuid import getnode as get_mac

MAC_ADDRESS = str(get_mac())
USER_ID = "5ab0e9d8491df1ca3c49adf1"
WS_URI = 'ws://localhost:8080/websocket/raspo?'+MAC_ADDRESS


@asyncio.coroutine
def send_speed_test(ws):
    print("Preparing message for server...")
    try:
        st = pyspeedtest.SpeedTest()
        st.connect('speedtestba1.telecomitalia.it')
        ping = round(st.ping(), 2)
        download_speed = pyspeedtest.pretty_speed(st.download())
        upload_speed = pyspeedtest.pretty_speed(st.upload())
        msg = {
            'type': "speedTestClient",
            'message': "",
            'userId': USER_ID,
            'mac': MAC_ADDRESS,
            'ping': ping,
            'dw_speed': download_speed,
            'up_speed': upload_speed
        }
    except Exception as e:
        print(e)
    json_msg = json.dumps(msg)
    yield from ws.send(json_msg)
    print("Message sent to the web socket: " + json_msg)


@asyncio.coroutine
def open_ws(uri):
    ws = yield from websockets.connect(uri)
    msg = {
        'type': "initClient",
        'message': "",
        'userId': USER_ID,
        'mac': MAC_ADDRESS
    }
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
                print("Received a timeout, sending a ping... ")
                pong_waiter = yield from ws.ping()
                yield from asyncio.wait_for(pong_waiter, timeout=10)
            except asyncio.TimeoutError:
                # No response to ping in 10 seconds, disconnect.
                print("No response from server, i try to reconnect!")
                ws.close()
                return
            except Exception as e:
                print("Unhandled exception on ping: " + e)
        except Exception as e:
            print("Unhandled exception on recv(): " + e)
        else:
            # TODO Switch messages
            try:
                json_msg = json.loads(msg)
            except json.JSONDecodeError:
                print("Received a NON-JSON Document : " + msg)
            except Exception as e:
                print("Unhandled exception on parse json: " + e)
            else:
                print("Received a JSON Document: " + json.dumps(json_msg))
                try:
                    yield from asyncio.wait_for(send_speed_test(ws), timeout=30)
                except (asyncio.TimeoutError, websockets.ConnectionClosed) as error:
                    print(error)
                    print("There are network problems... soon i'm trying to reconnect to the web socket.")
                    return
                except Exception as e:
                    print("Unhandled exception on send message: " + e)


@asyncio.coroutine
def main():
    while True:
        try:
            yield from open_ws(WS_URI)
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



