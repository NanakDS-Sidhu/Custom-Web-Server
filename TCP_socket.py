import asyncio

async def handle_client(reader,writer):
    addr=writer.get_extra_info("peername")
    print(f"We are connected with {addr}")

    while True:
        data= await reader.read(1024)

        if not data:
            break
        
        print(f"Received {data.decode().strip()}")
        newD=data.decode() + "This code was reviewed by NDS"
        writer.write(newD.encode())
        await writer.drain()

    print("Closing Connection")
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(
        handle_client,
        host="127.0.0.1",
        port=8888
    )

    addr= "".join(str(sock.getsockname() for sock in server.sockets))
    print(f"Serving on {addr}")
    async with server:
        await server.serve_forever()

asyncio.run(main())
