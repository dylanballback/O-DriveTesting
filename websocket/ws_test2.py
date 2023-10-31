# client.py
import asyncio
import websockets
import json

async def send_data():
    uri = "ws://192.168.1.2:5025/socket.io/?EIO=4&transport=websocket"  # Change server_address to your server's IP
    async with websockets.connect(uri) as websocket:
        data = [1, 2, 3, 4, 5]  # Your list of integers
        # Flask-SocketIO uses a custom message format, so we need to format it properly:
        message = '42["send_data", {}]'.format(json.dumps(data))
        await websocket.send(message)

asyncio.get_event_loop().run_until_complete(send_data())
