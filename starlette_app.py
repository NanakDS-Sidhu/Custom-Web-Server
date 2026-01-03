from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from HTTP_server import HTTPServer
import asyncio


async def homepage(request):
    return JSONResponse({"hello": "world", "context": "running on custom ASGI server"})

async def user_profile(request):
    user_id = request.path_params['username']
    return JSONResponse({"user": user_id, "status": "active"})

starlette_app = Starlette(debug=True, routes=[
    Route('/', homepage),
    Route('/user/{username}', user_profile),
])


async def main():
    server_logic = HTTPServer(starlette_app) 
    server = await asyncio.start_server(server_logic.handle_client, "127.0.0.1", 8000)
    
    print("Starlette API running on http://127.0.0.1:8000")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())