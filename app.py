from custom_app import App,Response

app = App()

@app.route("/hi")
async def homepage(request):
    return Response("Hi this is homepage")

@app.route("/echo",methods=["POST"])
async def echo(request):
    body=await request.body()
    return Response(f"You sent: {body.decode()}")