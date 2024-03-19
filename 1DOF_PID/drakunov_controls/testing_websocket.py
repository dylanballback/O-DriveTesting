# pip3 install python-socketio[client]

import json
from time import sleep
import socketio


class CustomDataStreamer:
    def __init__(self, ws_uri, namespace=None):
        self.ws_uri = ws_uri
        self.namespace = namespace
        self.sio = socketio.Client(logger=True, engineio_logger=True)  # Optional logging
        self.sio.connect(self.ws_uri, namespaces=[self.namespace])

    def emit_data(self, event, data):
        # Serialize data to JSON format (or any format suitable for your data)
        serialized_data = json.dumps(data)
        # Emit data to Flask app
        if self.namespace:
            self.sio.emit(event, serialized_data, namespace=self.namespace)
        else:
            self.sio.emit(event, serialized_data)

    def start_streaming(self, event, get_data_func, interval=1):
        # Continuously stream data
        try:
            while True:
                data = get_data_func()  # Get data from a function passed as argument
                self.emit_data(event, data)
                sleep(interval)
        except KeyboardInterrupt:
            self.sio.disconnect()


# Example usage
if __name__ == '__main__':
    ws_uri = 'http://192.168.1.12:5000'  # Flask-SocketIO server URI
    # Example function that generates data
    def get_custom_data():
        # Your logic to fetch or generate multiple data points
        return {'temperature': 22, 'humidity': 45}
    
    data_streamer = CustomDataStreamer(ws_uri)
    data_streamer.start_streaming('my_custom_event', get_custom_data, 2)