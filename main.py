from fastapi import FastAPI, Request
import requests
import logging
from datetime import datetime
import pytz
import os

app = FastAPI()

logging.basicConfig(level=logging.INFO)

GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_BASE_URL = os.getenv("GHL_BASE_URL")

def buscar_contacto_ghl_por_telefono(phone_number: str):
    url = f"{GHL_BASE_URL}/contacts/search"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json={"phone": phone_number}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        contacts = data.get("contacts", [])
        return contacts[0] if contacts else None
    else:
        logging.error(f"❌ Error buscando contacto: {response.status_code} - {response.text}")
        return None

def crear_nota_llamada_en_ghl(call_data):
    contact_phone = call_data["contact"]["phone_numbers"][0]
    user_name = call_data["user"]["name"]
    duration = call_data.get("duration", 0)
    recording_url = call_data.get("recording", {}).get("url") if call_data.get("recording") else None
    start_time = call_data["started_at"]

    dt_obj = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    formatted_time = dt_obj.astimezone(pytz.timezone("America/Mexico_City")).strftime("%d/%m/%Y %H:%M")

    nota = f"""📞 Llamada atendida por {user_name} el {formatted_time}
Duración: {duration} segundos
Grabación: {recording_url if recording_url else 'No disponible'}"""

    contacto = buscar_contacto_ghl_por_telefono(contact_phone)
    if not contacto:
        logging.warning("❌ Contacto no encontrado en GHL para el teléfono: %s", contact_phone)
        return False

    contact_id = contacto["id"]
    url = f"{GHL_BASE_URL}/contacts/{contact_id}/notes"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json={"body": nota}, headers=headers)

    if response.status_code == 200:
        logging.info("✅ Nota creada en GHL para contacto %s", contact_id)
        return True
    else:
        logging.error(f"❌ Error creando nota: {response.status_code} - {response.text}")
        return False

@app.post("/aircall/webhook")
async def handle_aircall_webhook(request: Request):
    payload = await request.json()
    logging.info(f"📞 Payload recibido: {payload}")

    try:
        event_type = payload.get("event")
        data = payload.get("data", {})

        if event_type == "call.ended" and data.get("answered", False):
            logging.info("📞 Llamada respondida, creando nota en GHL...")
            success = crear_nota_llamada_en_ghl(data)
            if success:
                return {"message": "Nota creada en GHL"}
            else:
                return {"message": "No se encontró contacto en GHL o error al crear nota"}

        elif event_type == "user.connected":
            user = data
            logging.info(f"👤 Usuario conectado: {user.get('name')} - {user.get('email')}")

        else:
            logging.info(f"🔔 Evento no manejado: {event_type}")

    except Exception as e:
        logging.error(f"Error procesando webhook: {e}")

    return {"status": "ok"}
