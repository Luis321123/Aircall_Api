from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook")
async def aircall_webhook(request: Request):
    payload = await request.json()
    print("Webhook recibido:", payload)
    return {"message": "Webhook recibido correctamente"}

@app.get("/")
def read_root():
    return {"status": "FastAPI corriendo correctamente en Railway 🚀"}