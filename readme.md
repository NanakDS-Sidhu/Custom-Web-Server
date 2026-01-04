
# Minimal TCP Echo Server (Asyncio)

## Overview

This project is a **basic TCP echo server** built using Python’s `asyncio`.
It accepts client connections, reads raw data from the socket, and sends the data back with a small modification.

This example focuses purely on **TCP-level communication**, without any HTTP or ASGI abstractions.

## What This Implements

* TCP server using `asyncio.start_server`
* Handling multiple client connections asynchronously
* Continuous read loop per connection
* Echoing received data back to the client
* Graceful connection close

## Flow

```
Client connects
   ↓
Connection accepted
   ↓
Data read from socket
   ↓
Data logged and modified
   ↓
Response written back to client
   ↓
Client disconnects
   ↓
Connection closed
```

## Example Behavior

Client sends:

```
Hello server
```

Server responds with:

```
Hello serverThis code was reviewed by NDS
```

## How to Run

```bash
python main.py
```

Server runs at:

```
127.0.0.1:8888
```

I have added two files socket_call_linux  and socket_call_win
You can test the socket app with these according to your operating system

Type any message and see it echoed back.


