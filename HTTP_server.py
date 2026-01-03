import asyncio
import traceback
from typing import Callable, Dict, Any, List, Tuple

async def app(scope: Dict[str, Any], receive: Callable, send: Callable):
    try:
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return

        if scope["type"] == "http":
            body = b""
            while True:
                message = await receive()
                body += message.get("body", b"")
                if not message.get("more_body", False):
                    break

            response_body = f"Hello from Production! Path: {scope['path']}".encode()
            
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"text/plain"),
                    (b"content-length", str(len(response_body)).encode()),
                    (b"connection", b"keep-alive"),
                ]
            })
            await send({
                "type": "http.response.body",
                "body": response_body,
            })
    except Exception:
        print(traceback.format_exc())

class HTTPServer:
    def __init__(self, app):
        self.app = app

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handles a persistent TCP connection."""
        while not writer.is_closing():
            try:
                header_data = await reader.readuntil(b"\r\n\r\n")
                if not header_data:
                    break
                
                lines = header_data.decode().split("\r\n")
                method, path, version = lines[0].split(" ")
                
                headers = []
                content_length = 0
                for line in lines[1:]:
                    if ": " in line:
                        k, v = line.split(": ", 1)
                        headers.append((k.lower().encode(), v.encode()))
                        if k.lower() == "content-length":
                            content_length = int(v)

                queue = asyncio.Queue()

                async def receive():
                    return await queue.get()

                async def send(message):
                    if message["type"] == "http.response.start":
                        status = message["status"]
                        writer.write(f"HTTP/1.1 {status} OK\r\n".encode())
                        for k, v in message.get("headers", []):
                            writer.write(k + b": " + v + b"\r\n")
                        writer.write(b"\r\n")
                    elif message["type"] == "http.response.body":
                        writer.write(message.get("body", b""))
                        await writer.drain()

                body_read = 0
                request_body = await reader.readexactly(content_length)
                await queue.put({"type": "http.request", "body": request_body, "more_body": False})

                scope = {
                    "type": "http",
                    "method": method,
                    "path": path,
                    "headers": headers,
                }
                
                await self.app(scope, receive, send)

            except asyncio.IncompleteReadError:
                break
            except Exception as e:
                print(f"Error handling request: {e}")
                break
        
        writer.close()
        await writer.wait_closed()

async def main():
    host="127.0.0.1"
    port=8000
    server_logic=HTTPServer(app)
    server = await asyncio.start_server(server_logic.handle_client,host,port)
    print(f"ASGI server running on  http://{host}:{port}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())