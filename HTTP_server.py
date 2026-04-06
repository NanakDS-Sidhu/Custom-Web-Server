import asyncio
import traceback
from typing import Callable, Dict, Any
import fast_parser  

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
        while not writer.is_closing():
            try:
                # 1. READ PATH: Let asyncio handle the network I/O
                header_data = await reader.readuntil(b"\r\n\r\n")
                if not header_data:
                    break
                
                raw_request_str = header_data.decode('utf-8', errors='ignore')
                
                # Hand off string parsing to C++
                parsed = fast_parser.parse_http(raw_request_str)
                
                headers = []
                content_length = 0
                for k, v in parsed.headers.items():
                    k_bytes = k.lower().encode('utf-8')
                    v_bytes = v.encode('utf-8')
                    headers.append((k_bytes, v_bytes))
                    if k_bytes == b"content-length":
                        content_length = int(v)

                queue = asyncio.Queue()

                async def receive():
                    return await queue.get()

                # 2. WRITE PATH: State variables for building the response
                response_status = 200
                response_headers = []

                async def send(message):
                    nonlocal response_status, response_headers
                    
                    if message["type"] == "http.response.start":
                        response_status = message["status"]
                        # Convert ASGI byte tuples to strings for the C++ serializer
                        response_headers = [
                            (k.decode('utf-8'), v.decode('utf-8')) 
                            for k, v in message.get("headers", [])
                        ]
                        
                    elif message["type"] == "http.response.body":
                        body_bytes = message.get("body", b"")
                        
                        # Hand off string serialization to C++
                        raw_response = fast_parser.serialize_response(
                            response_status, 
                            response_headers, 
                            body_bytes
                        )
                        
                        writer.write(raw_response)
                        await writer.drain()

                body_read = 0
                request_body = b""
                if content_length > 0:
                    request_body = await reader.readexactly(content_length)
                
                await queue.put({"type": "http.request", "body": request_body, "more_body": False})

                scope = {
                    "type": "http",
                    "method": parsed.method,
                    "path": parsed.path,
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
    host = "127.0.0.1"
    port = 8000
    server_logic = HTTPServer(app)
    server = await asyncio.start_server(server_logic.handle_client, host, port)
    print(f"Hybrid C++/Python ASGI server running on http://{host}:{port}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())