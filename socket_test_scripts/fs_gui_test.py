import trio

async def client():
    # Connect to the server at localhost:5555
    stream = await trio.open_tcp_stream('localhost', 5556)
    
    # Send a message to the server
    message = "Hello, server!"
    print(f"Sending message: {message}")
    await stream.send_all(message.encode())
    
    # Receive the echo response from the server
    response = await stream.receive_some(1024)
    print(f"Received response: {response.decode()}")
    
    # Close the connection
    await stream.aclose()

async def main():
    # Run the client after a short delay to ensure the server is up
    await trio.sleep(1)  # Give the server a moment to start
    await client()

trio.run(main)
