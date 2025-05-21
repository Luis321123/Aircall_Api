from fastapi import FastAPI, Request, HTTPException
import requests
import logging
from datetime import datetime
import phonenumbers

app = FastAPI()

# Configuración de tu API Key y URL de GHL
GHL_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ims3Um9lUUtUMDZPZHY4Um9GT2pnIiwidmVyc2lvbiI6MSwiaWF0IjoxNzQzNjEzNDkwOTUzLCJzdWIiOiJyTjlhazB3czJ1YWJUa2tQQllVYiJ9.dFA5LRcQ2qZ4zBSfVRhG423LsEhrDgrbDcQfFMSMv0k"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1"

logging.basicConfig(level=logging.INFO)

def normalize_phone(phone_number: str) -> str:
    try:
        parsed = phonenumbers.parse(phone_number, "US")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        return phone_number

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

@app.post("/webhook")
async def webhook(request: Request):
    try:
        payload = await request.json()
        logging.info("Payload recibido: %s", payload)

        # Extraer el número de teléfono desde el campo correcto
        phone = payload.get("data", {}).get("raw_digits")
        if not phone:
            logging.warning("No se encontró el campo 'raw_digits' en el payload")
            raise HTTPException(status_code=400, detail="Phone number not found in payload")

        contact_id = find_contact_by_phone(phone)
        if contact_id:
            logging.info(f"Contacto encontrado en GHL: {contact_id}")
        else:
            logging.info("No se encontró contacto con ese número.")

        return {"status": "ok", "contact_id": contact_id}

    except requests.HTTPError as e:
        logging.error("Error HTTP al consultar GHL: %s", str(e))
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logging.exception("Error inesperado en el webhook")
        raise HTTPException(status_code=500, detail="Internal server error")
