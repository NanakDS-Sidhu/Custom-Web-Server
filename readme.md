# Custom Async HTTP Server – Architecture Overview

This project implements a custom asynchronous HTTP server built on top of asyncio, following ASGI-style semantics for request/response handling and routing.

The goal is to understand how low-level socket handling, the asyncio event loop, and application-level routing fit together.


This repository is organized into **multiple branches**, each implementing the server at a **different abstraction level**.
Refer to the README in each branch to understand the functionality and design at that stage.

### Branch Overview

* **`TCP-calls`**
  Raw TCP socket handling and echo-style communication.

* **`HTTP-handler`**
  Basic HTTP server built directly on top of TCP.

* **`ASGI-GET`**
  Minimal ASGI-style server supporting **GET requests only**.

* **`ASGI-GET-POST`**
  Extended ASGI-style server with **GET and POST support**.

* **`ASGI-Custom-app`**
  ASGI server executing a custom ASGI application.

* **`ASGI-starlette-demo`**
  Demo showing compatibility with a real ASGI framework (**Starlette**).

* **`main`**
  Full ASGI-compliant server implementation.

---



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


## Runtime & Reliability Enhancements
The server was extended with several production-style runtime controls to improve stability under load and enable observability.

### Connection Pooling
A global concurrency limit was introduced using an asyncio.Semaphore to restrict the number of simultaneous active client handlers.

#### Purpose:

- Prevent unbounded task creation

- Limit resource contention

- Maintain predictable server performance

Effect: New connections wait when capacity is reached instead of overwhelming the system.

### Backpressure Control
Incoming connections are regulated using a bounded request queue. If the queue reaches capacity, the server immediately responds with: HTTP 503 Service Unavailable.

#### Purpose:

- Prevent overload collapse

- Maintain responsiveness during traffic spikes

Effect: Excess traffic is rejected gracefully rather than causing server failure.

### Bounded Request Buffering
Request body reads are limited by a configurable maximum body size. If the request exceeds the configured limit, the server responds with: HTTP 413 Payload Too Large.

#### Purpose:

- Prevent memory exhaustion
 
- Protect against large payload abuse

Effect: Memory usage remains bounded regardless of client behavior.

### Keep-Alive Connection Handling
Connections remain open to allow multiple HTTP requests per TCP session.

#### Purpose:

- Reduce connection overhead

- Improve throughput and latency

Effect: Multiple requests are processed sequentially on the same socket.

### Server Metrics & Observability
Runtime counters were added to monitor server behavior.

#### Tracked Metrics:

- active_connections

- total_requests

- rejected_connections

- uptime_seconds

Exposed via: GET /metrics

#### Purpose:

Enable runtime visibility

Support performance testing

Aid debugging and reliability analysis

Graceful Connection Lifecycle Management
Connection open and close events update runtime counters and ensure proper resource cleanup.

Purpose:

Avoid resource leakage

Maintain accurate runtime statistics

Effect: Connections are tracked seamlessly throughout their entire lifecycle