# Custom Async HTTP Server – Architecture Overview

This project implements a custom asynchronous HTTP server built on top of asyncio, following ASGI-style semantics for request/response handling and routing.

The goal is to understand how low-level socket handling, the asyncio event loop, and application-level routing fit together.

### High-Level Request Lifecycle
```scss
start_server()
   ↓
(listening socket)
   ↓
client connects
   ↓
handle_client task CREATED
   ↓
task runs → await readuntil() → PAUSE
   ↓
client sends headers
   ↓
task resumes → parse headers
   ↓
await readexactly() → PAUSE
   ↓
client sends body
   ↓
task resumes
   ↓
await app() → CONTROL TRANSFER
   ↓
send() writes response
```
## Server Responsibility

The custom HTTP server:

- Listens for incoming TCP connections using asyncio.start_server

- Creates a new asyncio Task for each client connection

- Handles parsing of raw HTTP data from the socket

- Translates socket data into ASGI-compatible events

- Delegates request handling to the application layer

Each client connection is handled by the `handle_client` coroutine, which is executed independently by the event loop.

## handle_client Flow

For each connected client:

- Read and parse HTTP headers

- Read the request body (if present)

- Construct an ASGI scope object

- Provide the application with:

- scope (request metadata)

- receive() (pull-based request body access)

- send() (push-based response writer)

- Await the application to process the request

The server itself does not contain routing or business logic.

## Application Layer (app)

The application passed into the HTTP server follows the ASGI calling convention:

```await app(scope, receive, send)```


Its responsibilities include:

- Routing requests to the correct endpoint

- Creating request and response abstractions

- Coordinating request data consumption and response emission

- Routing System

The custom application contains:

- An App class that initializes a Router

- A router that maps (method, path) → endpoint functions

Routes registered using decorators

> Example flow:
> - Incoming request enters the app
> - Router matches the request path and method
> - The corresponding endpoint function is invoked

## Request Handling

Each endpoint receives a Request object, which:

- Pulls request body data using the receive() callable

- Provides a structured interface over raw ASGI events

- Abstracts away socket and protocol details

This allows endpoints to focus only on request data and logic.

- Response Handling

- Endpoints return a Response object.

The response is sent back to the client using two ASGI messages:

Response start
``` json
{
  "type": "http.response.start",
  "status": status_code,
  "headers": headers
}
```

Response body
```json
{
  "type": "http.response.body",
  "body": content
}
```

These messages are passed to the send() callable provided by the HTTP server, which writes the data to the underlying socket.

## Endpoint Definition

Endpoints are defined in app.py using decorators that attach:

- HTTP method

- Path

- Handler function

This keeps route definitions declarative and centralized.

## Server Startup

The application is started by initializing the HTTP server with the application instance:

``` python
asyncio.start_server(handle_client, host, port)
```

This binds the application, server, and event loop into a complete request-handling system.

## Design Philosophy

Socket handling is isolated to the server

Routing and business logic live in the application layer

Communication between layers follows ASGI-style message passing

The event loop controls execution flow via await boundaries

This structure mirrors the internal architecture of production servers such as uvicorn, while remaining simple and educational.

