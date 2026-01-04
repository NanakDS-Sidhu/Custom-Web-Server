# Minimal ASGI-like HTTP Server (Asyncio)
## Overview

This project is a minimal HTTP server built using asyncio that demonstrates how an ASGI-style application can be executed on top of a raw TCP server.

It manually:

- Parses HTTP requests from a socket

- Constructs an ASGI scope

- Implements receive and send callables

- Executes an ASGI-compatible app

## What This Implements

- TCP server using asyncio.start_server

- Basic HTTP request parsing (headers + body)

- ASGI-style application interface:

```async def app(scope, receive, send)```


- Manual HTTP response construction using ASGI messages:

```http.response.start```

```http.response.body```

## how to run 
 You can run the file ```asgi-app.py``` as 
 ```python
 python3 asgi-app.py
 ```

to serve on http://127.0.0.1/8000

You can hit the endpoint using postman or curl

