
# GET-only ASGI-style HTTP Server (Asyncio)

## Overview

This project is a **minimal GET-only HTTP server** built on top of raw TCP using `asyncio`.
It demonstrates the **core ASGI execution model** (`scope`, `receive`, `send`) without implementing the full ASGI or HTTP specification.

This is intentionally kept small to focus only on **how an ASGI app is invoked**.

## What This Implements

* TCP server using `asyncio.start_server`
* Basic parsing of the HTTP request line
* ASGI-style application interface:

  ```python
  async def app(scope, receive, send)
  ```
* Manual wiring of:

  * `scope`
  * `receive()`
  * `send()`
* **GET-only request handling**

## Flow

``` scss
Client connects
   ↓
Raw TCP data read
   ↓
HTTP request line parsed
   ↓
ASGI scope constructed
   ↓
app(scope, receive, send) called
   ↓
ASGI response converted to HTTP bytes
   ↓
Connection closed
```

## Example Behavior

For a request:

```
GET /hello HTTP/1.1
```

Response body:

```
You said hi /hello
```

## How to Run

```bash
python asgi-get.py
```

Server runs at:

```
http://127.0.0.1:8000
```

Test with:

```bash
curl http://127.0.0.1:8000/hello
```



