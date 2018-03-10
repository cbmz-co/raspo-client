import asyncio
import websockets
import pyspeedtest
from uuid import getnode as get_mac


async def open_web_socket(uri):
    async with websockets.connect(uri) as websocket:
        mac = str(get_mac())
        st = pyspeedtest.SpeedTest()
        speed = pyspeedtest.pretty_speed(st.download())
        await websocket.send("MAC Address:"+mac+" Download Speed: "+speed)


def main():
    asyncio.get_event_loop().run_until_complete(open_web_socket('wss://ywxygb7-raspobackend.wedeploy.io/ciao'))


main()
