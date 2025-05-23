from fastapi import FastAPI, Request
import requests
import logging
from datetime import datetime
import pytz

app = FastAPI()

logging.basicConfig(level=logging.INFO)

GHL_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ims3Um9lUUtUMDZPZHY4Um9GT2pnIiwidmVyc2lvbiI6MSwiaWF0IjoxNzQzNjEzNDkwOTUzLCJzdWIiOiJyTjlhazB3czJ1YWJUa2tQQllVYiJ9.dFA5LRcQ2qZ4zBSfVRhG423LsEhrDgrbDcQfFMSMv0k"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1"


def crear_contacto_en_ghl(phone_number, name):
    url = f"{GHL_BASE_URL}/contacts/"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }

    name = (name or "").strip()
    if name:
        parts = name.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""
    else:
        first_name = "Contacto"
        last_name = "Aircall"

    payload = {
        "firstName": first_name,
        "lastName": last_name,
        "phone": phone_number,
        "source": "Aircall"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in (200, 201):
            logging.info(f"✅ Contacto creado: {first_name} {last_name}")
            return response.json().get("id")
        else:
            logging.error(f"❌ Error creando contacto: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error en la solicitud HTTP: {e}")
        return None


def add_note_to_contact(contact_id, note_content):
    url = f"{GHL_BASE_URL}/contacts/{contact_id}/notes"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "body": note_content
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code in (200, 201)

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

def buscar_contacto_en_ghl(phone_number: str, ghl_api_key: str) -> str:

    url = f"https://rest.gohighlevel.com/v2/contacts/search?phone={phone_number}"
    headers = {
        "Authorization": f"Bearer {ghl_api_key}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data.get("contacts"):
            return "El contacto está en GHL"
        else:
            return "No está"
    else:
        return f"Error al buscar el contacto: {response.status_code} - {response.text}"


@app.post("/aircall/webhook")
async def handle_aircall_webhook(request: Request):
    payload = await request.json()
    logging.info(f"📞 Payload recibido: {payload}")

    try:
        event_type = payload.get("event")
        data = payload.get("data", {})

        if event_type == "call.answered":
            logging.info("📞 Evento 'call.answered' recibido, verificando contacto en GHL...")

            # Obtener el número de teléfono
            phone_number = data.get("raw_digits") or data.get("number", {}).get("raw") or data.get("number", {}).get("digits")
            if not phone_number:
                logging.warning("⚠️ No se pudo obtener el número de teléfono.")
                return {"status": "missing phone number"}

            # Limpiar el número (opcional)
            phone_number = phone_number.replace(" ", "").replace("-", "")

            # Verificar si el contacto existe en GHL
            contacto = buscar_contacto_ghl_por_telefono(phone_number)

            if contacto:
                contact_id = contacto.get("id")
                owner_id = contacto.get("ownerId") or "No asignado"
                logging.info(f"✅ El contacto con número {phone_number} existe en GHL.")
                logging.info(f"🆔 Contact ID: {contact_id}")
                logging.info(f"👤 Asignado a (ownerId): {owner_id}")
            else:
                logging.info(f"❌ El contacto con número {phone_number} NO existe en GHL.")

        else:
            logging.info(f"🔔 Evento no manejado: {event_type}")

    except Exception as e:
        logging.error(f"❌ Error procesando el webhook: {e}")

    return {"status": "ok"}
