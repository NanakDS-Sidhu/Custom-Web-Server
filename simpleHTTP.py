import asyncio

async def handle_client(reader,writer):
    request_data=await reader.read(2048)
    request_text =request_data.decode()

    request_line= request_text.split("\r\n")[0]
    method,path,version=request_line.split()
    print(f"Received {method} for path {path} ")

    response_body=f"Hello you requested the path {path}, This was sent by the server \n".encode()
    response_headers = (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Length: {len(response_body)}\r\n"
        "Content-Type: text/plain\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    print(response_headers)
    response_headers=response_headers.encode()
    writer.write(response_headers+response_body)
    await writer.drain()

    writer.close()
    await writer.wait_closed()

async def main():
    host="127.0.0.1"
    port=8888
    server=await asyncio.start_server(handle_client,host,port)
    print(f"HTTP server running at http://{host}:{port}")
    async with server:
        await server.serve_forever()
    
asyncio.run(main())