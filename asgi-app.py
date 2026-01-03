import asyncio

async def app(scope,receive,send):
    if scope["type"]=="http":
        request_data=await receive()
        content=request_data.get("body",b"").decode()
        path=scope["path"]
        method=scope["method"]

        response_text = f"Method: {method} \n Path {path} \n Received Body:{content}"
        body=response_text.encode()

        await send({
            "type":"http.response.start",
            "status":200,
            "headers":[(b"Content-Type",b"text/plain"),(b"Content-Length",str(len(body)).encode())]
        })

        await send({
            "type":"http.response.body",
            "body": body
        })
               
async def handle_connection(reader,writer):

    raw_data= await reader.read(4096)
    if not raw_data:
        writer.close()
        return 

    header_section,_,body_section = raw_data.partition(b"\r\n\r\n")
    header_lines=header_section.decode().split("\r\n")

    request_line= header_lines[0].split(" ")
    if len(request_line)>3:
        writer.close()
        return
    method,path,version=request_line

    scope={
        "type":"http",
        "method":method,
        "path":path,
        "headers":[]
    }

    async def receive():
        return {
            "type": "http.request",
            "body":body_section,
            "more_body":False
        }
    async def send(message):
        if message["type"]=="http.response.start":
            status=message["status"]
            headers= message.get("headers",[])

            resp=f"HTTP/1.1 {status} OK\r\n"
            writer.write(resp.encode())

            for key,value in headers:
                writer.write(key + b": " + value + b"\r\n")
            writer.write(b"\r\n")
        
        elif message["type"] == "http.response.body":
            writer.write(message.get("body",b""))
            await writer.drain()
    try:
        await app(scope,receive,send)
    finally:
        writer.close()
        await writer.wait_closed()
        
        
async def main():
    host="127.0.0.1"
    port=8000

    server=await asyncio.start_server(lambda r,w : handle_connection(r,w),host,port)
    print(f"HTTP server running at http://{host}:{port}")

    async with server:
        await server.serve_forever()

asyncio.run(main())