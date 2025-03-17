import trio


default_timeout = 5
rx_buff_size = 1024

class FocusSweepGuiInterface:

    connected = False
    
    def __init__(self, nursery, _ip="localhost", _port=5556, _timeout=default_timeout):
        self.nursery = nursery
        self.connection = (_ip, _port)
        self.timeout = _timeout
        self.nursery.start_soon(self.run)

    def connect_tip_tilt_controller(self, ttc):
        self.ttc = ttc
        pass

        
    async def run(self):
        """Continuously listens for incoming messages and spawns tasks to handle them."""
        if not self.connected:
            
            await self.start_server()
        
        while True:
            await trio.sleep(0)  # Give the server a chance to handle tasks
    
    async def start_server(self):
        """Starts the server to listen for incoming client connections."""
        try:
            self.listener = await trio.open_tcp_listeners(self.connection[1], host=self.connection[0])
            self.connected = True
            print(f"Server listening on {self.connection[0]}:{self.connection[1]}")
            
            # Accept and handle client connections
            async with self.listener[0]:
                while True:
                    stream = await self.listener[0].accept()  # Accept a new client connection
                    self.nursery.start_soon(self.handle_client, stream)  # Handle the client in a new task
                
        except Exception as e:
            print(f"Error while starting server: {e}")
            self.connected = False

    async def handle_client(self, stream):
        """Handles communication with a single client."""
        try:
            print("Client connected")
            async with stream:
                while True:
                    message = await stream.receive_some(rx_buff_size)
                    if not message:
                        break  # Client disconnected
                    
                    decoded_message = message.decode()
                    print(f"Received: {decoded_message}")
                    if decoded_message.startswith("Hello"):
                        response = "Hello from server!"
                    elif decoded_message.startswith("focus: "):
                        magnitude = float(decoded_message.split("focus: ")[1])
                        print(f"Moving relative focus by {magnitude}")
                        moved_mag = self.ttc.external_move_command(magnitude)
                        response = f"{moved_mag}"
                    await trio.sleep(1.0)
                    await stream.send_all(response.encode())

            print("Client disconnected")

        except trio.BrokenResourceError:
            print("Client disconnected unexpectedly")
            self.connected = False
