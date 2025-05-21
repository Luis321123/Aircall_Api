from fastapi import FastAPI, Request, HTTPException
import requests
import logging
from datetime import datetime
import phonenumbers

app = FastAPI()

# Configura tu API Key y URL base de GHL
GHL_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ims3Um9lUUtUMDZPZHY4Um9GT2pnIiwidmVyc2lvbiI6MSwiaWF0IjoxNzQzNjEzNDkwOTUzLCJzdWIiOiJyTjlhazB3czJ1YWJUa2tQQllVYiJ9.dFA5LRcQ2qZ4zBSfVRhG423LsEhrDgrbDcQfFMSMv0k"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1"

# Setup de logs
logging.basicConfig(level=logging.INFO)

# Normaliza un número de teléfono a formato E.164
def normalize_phone(phone_number: str) -> str:
    try:
        parsed = phonenumbers.parse(phone_number, "US")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return phone_number  # Si falla, lo deja como está

# Busca un contacto por teléfono (CORREGIDO: POST en vez de GET)
def find_contact_by_phone(phone_number: str):
    phone_number = normalize_phone(phone_number)
    url = f"{GHL_BASE_URL}/contacts/search"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"phone": phone_number}
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    if data.get("contacts"):
        return data["contacts"][0]["id"]
    return None

# Webhook que recibe datos
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        logging.info("Payload recibido: %s", data)

        user = data.get("user")
        if not user:
            logging.error("Campo 'user' no encontrado en el JSON recibido.")
            raise HTTPException(status_code=400, detail="Missing 'user' field")

        phone = user.get("phone") or user.get("phone_number")
        if not phone:
            logging.error("Número de teléfono no encontrado en 'user'")
            raise HTTPException(status_code=400, detail="Missing phone number")

        # Busca contacto en GHL
        contact_id = find_contact_by_phone(phone)
        if contact_id:
            logging.info(f"Contacto encontrado: {contact_id}")
        else:
            logging.info("No se encontró contacto con ese teléfono.")

        return {"status": "ok", "contact_id": contact_id}

    except requests.HTTPError as e:
        logging.error("Error HTTP al consultar GHL: %s", str(e))
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logging.error("Error en webhook: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal error")
