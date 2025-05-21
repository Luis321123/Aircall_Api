from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    print("Payload recibido:", payload)
    return {"message": "Payload recibido"}