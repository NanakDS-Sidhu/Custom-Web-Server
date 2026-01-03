import asyncio

async def app(scope,receive,send):
    assert scope["type"] == "http"

    await send({
        "type":"http.response.start",
        "status":200,
        "headers":[(b"content-type",b"text-plain")]
    })
     
    body =f" You said hi {scope['path']}".encode()

    await send({
        "type":"http.response.body",
        "body":body
    })

async def get_TCP(app,reader,writer):
    async def receive():
        return {
            "type":"http.request",
            "body":"b",
            "more_body":False,
        }

    async def send(message):
        if message["type"]=="http.response.start":
            status=message["status"]
            headers=message.get("headers",[])

            status_line=f"HTTP/1.1 {status} OK"
            writer.write(status_line.encode())
            
            for k,v in headers:
                writer.write(k+b": "+ v + b"\r\n" )
            writer.write(b"\r\n")
            
        elif message["type"]=="http.response.body":
            body=message.get("body",b"")
            writer.write(body)
            await writer.drain()
            writer.close()

    while True:
        data = await reader.read(1024)

        if not data:
            break
            
        text = data.decode(errors="ignore")
        lines=text.split("\r\n")
        request_line=lines[0]
        parts=request_line.split(" ")
        if len(parts)>3:
            writer.close()
            return
        method,path,version=parts
        scope = {
            "type":"http",
            "http_version":"1.1",
            "method":method,
            "path":path,
            "headers":[]
        }
        await app(scope,receive,send)

async def main():
    host="127.0.0.1"
    port=8000

    server=await asyncio.start_server(lambda r,w : get_TCP(app,r,w),host,port)
    print(f"HTTP server running at http://{host}:{port}")

    async with server:
        await server.serve_forever()

asyncio.run(main())