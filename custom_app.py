class Response:
    def __init__(self, content, status=200, headers=None):
        self.content = content.encode() if isinstance(content, str) else content
        self.status = status
        self.headers = headers or {"content-type": "text/plain"}

    async def __call__(self, send):
        if "content-length" not in self.headers:
            self.headers["content-length"] = str(len(self.content))
            
        await send({
            "type": "http.response.start",
            "status": self.status,
            "headers": [(k.encode("latin-1"), v.encode("latin-1")) for (k, v) in self.headers.items()]
        })
        await send({"type": "http.response.body", "body": self.content})

class Request:
    def __init__(self, scope, receive):
        self.scope = scope
        self.receive = receive
        self.method = scope["method"]
        self.path = scope["path"]
    
    async def body(self):
        body = b""
        while True:
            msg = await self.receive()
            body += msg.get("body", b"")
            if not msg.get("more_body", False):
                break
        return body

class Route:
    def __init__(self, path, endpoint, methods=["GET"]):
        self.path = path
        self.endpoint = endpoint
        self.methods = methods

    def matches(self, scope):
        return scope["path"] == self.path and scope["method"] in self.methods

class Router:
    def __init__(self, routes=None):
        self.routes = routes or []

    async def __call__(self, scope, receive, send):
        for route in self.routes:
            if route.matches(scope): 
                request = Request(scope, receive)
                response = await route.endpoint(request)
                return await response(send)
        await Response("Not Found", status=404)(send)

class App:
    def __init__(self):
        self.router = Router()

    def route(self, path, methods=["GET"]):
        def decorator(func):
            self.router.routes.append(Route(path, func, methods))
            return func
        return decorator

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                msg = await receive()
                if msg["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif msg["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        return await self.router(scope, receive, send)