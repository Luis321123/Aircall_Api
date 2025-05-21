from fastapi import FastAPI, Request
import requests
import logging
from dotenv import load_dotenv
import os

app = FastAPI()

# Configura el logging para que puedas ver los logs en la consola
logging.basicConfig(level=logging.INFO)

# Reemplaza con tu API key real de GoHighLevel
GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_BASE_URL = os.getenv("GHL_BASE_URL")

# Esta función crea o actualiza un contacto en GHL
def create_or_update_contact(phone_number, first_name, user_name):
    url = f"{GHL_BASE_URL}/contacts/"
    headers = {
        "Authorization": GHL_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "phone": phone_number,
        "firstName": first_name,
        "customField": {
            "Llamado por": user_name  # Si no tienes este custom field aún en GHL, podemos omitirlo
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    logging.info("📤 Enviado a GHL: %s", payload)
    logging.info("📥 Respuesta de GHL: %s", response.text)

    return response.json()

# Este endpoint recibe los webhooks de Aircall
@app.post("/aircall/webhook")
async def handle_aircall_webhook(request: Request):
    payload = await request.json()
    logging.info(f"📞 Payload recibido: {payload}")

    try:
        event_type = payload.get("event")
        data = payload.get("data", {})

        if event_type == "call.ended":
            call_id = data.get("id")
            recording_url = data.get("recording")
            user = data.get("user", {})
            logging.info(f"📞 Llamada terminada: ID={call_id}, URL grabación={recording_url}, Usuario={user.get('name')}")
            # Aquí puedes hacer algo con esos datos

        elif event_type == "user.connected":
            user = data
            logging.info(f"👤 Usuario conectado: {user.get('name')} - {user.get('email')}")
            # Aquí puedes manejar datos del usuario conectado

        else:
            logging.info(f"🔔 Evento no manejado: {event_type}")

    except Exception as e:
        logging.error(f"Error extrayendo datos: {e}")

    return {"status": "ok"}
