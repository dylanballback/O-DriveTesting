import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to server')
    send_data()

@sio.event
def disconnect():
    print('Disconnected from server')

def send_data():
    data = [1, 2, 3, 4, 5]
    sio.emit('send_data', data)
    print(f"Sent data: {data}")

if __name__ == '__main__':
    try:
        # Replace 'server_address' with the IP of the machine running the Flask server
        sio.connect('http://server_address:5000')
        sio.wait()
    except Exception as e:
        print(f"Error: {e}")
