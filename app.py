from custom_app import App,Response
import asyncio
from HTTP_server import HTTPServer,active_connections,total_requests,rejected_connections

app = App()

@app.route("/", methods=["GET"])
async def home(request):
    return Response("<h1 style='background:blue;'>Welcome Home</h1>", headers={"content-type": "text/html"})

@app.route("/echo", methods=["POST"])
async def echo(request):
    data = await request.body()
    return Response(f"You posted: {data.decode()}")

@app.route("/hi", methods=["GET"])
async def home(request):
    return Response("<h1 style='background:blue;'>Welcome to page hi</h1>", headers={"content-type": "text/html"})

@app.route("/metrics")
async def metrics(request):

        return Response(
            f"""
    active_connections {active_connections}
    total_requests {total_requests}
    rejected_connections {rejected_connections}
    """
    )

async def main():
    server_logic = HTTPServer(app)
    server = await asyncio.start_server(server_logic.handle_client, "127.0.0.1", 8000,backlog=200)
    print("Full-Stack Custom Server running on http://127.0.0.1:8000")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())