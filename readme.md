# Minimal HTTP Server over TCP (Asyncio)

## Overview

This project is a **basic HTTP/1.1 server built directly on top of TCP** using `asyncio`.
It manually reads raw bytes from a socket, parses the HTTP request line, and sends back a plain-text HTTP response.

This version does **not** use ASGI — it exists to show how HTTP works at the lowest level.

## What This Implements

* TCP server using `asyncio.start_server`
* Manual reading of raw HTTP request bytes
* Parsing of:

  * HTTP method
  * Request path
  * HTTP version
* Manual construction of an HTTP/1.1 response
* Clean connection close

## Flow

```
Client connects
   ↓
Raw bytes read from socket
   ↓
HTTP request line parsed
   ↓
Response headers constructed
   ↓
Response body written
   ↓
Connection closed
```

## Example Behavior

For a request:

```
GET /test HTTP/1.1
```

Response body:

```
Hello you requested the path /test, This was sent by the server
```

## How to Run

```bash
python simpleHTTP.py
```

Server runs at:

```
http://127.0.0.1:8888
```

Test with:

```bash
curl http://127.0.0.1:8888/test
```
