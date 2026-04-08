import asyncio
import logging
import time
import fast_parser

# =========================
# Logging Configuration
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("HybridServer")

# =========================
# Limits / Config
# =========================
MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB
HEADER_TIMEOUT = 5
MAX_HEADER_SIZE = 8192
MAX_REQUESTS_PER_CONN = 100

# =========================
# Metrics
# =========================
server_start_time = time.time()
active_connections = 0
total_requests = 0
rejected_connections = 0
metrics_lock = asyncio.Lock()

class HTTPServer:
    def __init__(self, app, max_connections=1000):
        self.app = app
        self.connection_semaphore = asyncio.Semaphore(max_connections)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        global active_connections, total_requests, rejected_connections
        
        addr = writer.get_extra_info('peername')

        # Backpressure Reject
        if self.connection_semaphore.locked():
            async with metrics_lock:
                rejected_connections += 1
            logger.warning(f"Connection rejected (Max capacity): {addr}")
            writer.write(b"HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\n\r\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        async with self.connection_semaphore:
            async with metrics_lock:
                active_connections += 1
            
            try:
                request_count = 0
                while not writer.is_closing():
                    request_count += 1
                    if request_count > MAX_REQUESTS_PER_CONN:
                        logger.info(f"Closing keep-alive connection: {addr} (Max requests reached)")
                        break

                    try:
                        header_data = await asyncio.wait_for(
                            reader.readuntil(b"\r\n\r\n"),
                            timeout=HEADER_TIMEOUT
                        )

                        if not header_data:
                            break

                        if len(header_data) > MAX_HEADER_SIZE:
                            logger.warning(f"431 Header Too Large from {addr}")
                            writer.write(b"HTTP/1.1 431 Request Header Fields Too Large\r\n\r\n")
                            await writer.drain()
                            break

                        async with metrics_lock:
                            total_requests += 1

                        raw_request_str = header_data.decode('utf-8', errors='ignore')
                        parsed = fast_parser.parse_http(raw_request_str)
                        
                        logger.info(f"{addr} - \"{parsed.method} {parsed.path} HTTP/1.1\"")

                        headers = []
                        content_length = 0
                        for k, v in parsed.headers.items():
                            k_bytes = k.lower().encode('utf-8')
                            headers.append((k_bytes, v.encode('utf-8')))
                            if k_bytes == b"content-length":
                                content_length = int(v)

                        queue = asyncio.Queue()

                        async def receive():
                            return await queue.get()

                        response_status = 200
                        response_headers = []

                        async def send(message):
                            nonlocal response_status, response_headers
                            if message["type"] == "http.response.start":
                                response_status = message["status"]
                                response_headers = [(k.decode('utf-8'), v.decode('utf-8')) 
                                                   for k, v in message.get("headers", [])]
                            elif message["type"] == "http.response.body":
                                body_bytes = message.get("body", b"")
                                raw_response = fast_parser.serialize_response(
                                    response_status, response_headers, body_bytes
                                )
                                writer.write(raw_response)
                                await asyncio.wait_for(writer.drain(), timeout=5)

                        # Body Handling
                        request_body = b""
                        if content_length > 0:
                            if content_length > MAX_BODY_SIZE:
                                logger.warning(f"413 Payload Too Large from {addr}")
        # Fixed the malformed string here:
                                writer.write(
                                b"HTTP/1.1 413 Payload Too Large\r\n"
                                b"Content-Type: text/plain\r\n"
                                b"Content-Length: 17\r\n"
                                b"Connection: close\r\n"
                                b"\r\n"
                                b"Payload Too Large"
                            )
                                await writer.drain() # Crucial: ensure bytes are sent before closing
                                return
                            request_body = await reader.readexactly(content_length)
                            
                        await queue.put({"type": "http.request", "body": request_body, "more_body": False})
                        
                        scope = {
                            "type": "http",
                            "method": parsed.method,
                            "path": parsed.path,
                            "headers": headers,
                        }

                        await self.app(scope, receive, send)

                    except asyncio.TimeoutError:
                        logger.debug(f"Header timeout for {addr}")
                        break
                    except asyncio.IncompleteReadError:
                        logger.debug(f"Incomplete Read for {addr}")

                        break
                    except Exception as e:
                        logger.error(f"Error handling request from {addr}: {e}")
                        break

            finally:
                logger.info("helo")
                async with metrics_lock:
                    active_connections -= 1
                writer.close()
                await writer.wait_closed()
