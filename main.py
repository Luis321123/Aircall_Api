from fastapi import FastAPI, Request
import json
import logging

app = FastAPI()

# Configurar logs
logging.basicConfig(level=logging.INFO, filename="aircall_webhooks.log", filemode="a", format="%(asctime)s - %(message)s")

@app.post("/api/aircall/webhook")
async def aircall_webhook(request: Request):
    try:
        payload = await request.json()
        logging.info("Webhook recibido:\n%s", json.dumps(payload, indent=4))
        print("Webhook recibido:", json.dumps(payload, indent=4))  # Para ver en consola
        return {"status": "ok"}
    except Exception as e:
        logging.error("Error al procesar webhook: %s", str(e))
        return {"status": "error", "message": str(e)}
