import requests
from fastapi import FastAPI, Request
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)

GHL_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ims3Um9lUUtUMDZPZHY4Um9GT2pnIiwidmVyc2lvbiI6MSwiaWF0IjoxNzQzNjEzNDkwOTUzLCJzdWIiOiJyTjlhazB3czJ1YWJUa2tQQllVYiJ9.dFA5LRcQ2qZ4zBSfVRhG423LsEhrDgrbDcQfFMSMv0k"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1"

HEADERS_GHL = {
    "Authorization": f"Bearer {GHL_API_KEY}",
    "Content-Type": "application/json"
}

def find_or_create_lead(phone_number: str):
    logging.info(f"Buscando lead con teléfono: {phone_number}")
    url = f"{GHL_BASE_URL}/contacts/?phone={phone_number}"
    r = requests.get(url, headers=HEADERS_GHL)
    data = r.json()
    logging.info(f"Respuesta búsqueda lead: {data}")
    
    if data.get("contacts"):
        logging.info(f"Lead encontrado: {data['contacts'][0].get('id')}")
        return data["contacts"][0]
    else:
        payload = {
            "phone": phone_number,
            "firstName": "Desconocido"
        }
        r = requests.post(f"{GHL_BASE_URL}/contacts/", headers=HEADERS_GHL, json=payload)
        data = r.json()
        logging.info(f"Lead creado: {data}")
        return data

def create_call_activity(lead_id: str, call_data: dict):
    logging.info(f"Creando actividad de llamada para lead_id={lead_id} con datos: {call_data}")
    payload = {
        "leadId": lead_id,
        "type": "call",
        "duration": call_data.get("duration"),
        "callStatus": "answered" if call_data.get("answered") else "missed",
        "recordingUrl": call_data.get("recording_url"),
        "user": call_data.get("user"),
        "phone": call_data.get("phone_number")
    }
    r = requests.post(f"{GHL_BASE_URL}/activities/", headers=HEADERS_GHL, json=payload)
    data = r.json()
    logging.info(f"Actividad creada: {data}")
    return data

@app.post("/webhook")
async def aircall_webhook(request: Request):
    payload = await request.json()
    logging.info(f"Webhook recibido con payload: {payload}")
    
    call = payload.get("call", {})
    
    phone_number = call.get("from", {}).get("number") or call.get("to", {}).get("number")
    user = call.get("from", {}).get("user", "Desconocido")
    duration = call.get("duration", 0)
    answered = call.get("answered", False)
    recording_url = call.get("recording", {}).get("url", "")
    
    if not phone_number:
        logging.warning("Número no encontrado en el webhook")
        return {"error": "Número no encontrado en el webhook"}
    
    lead = find_or_create_lead(phone_number)
    lead_id = lead.get("id")
    
    call_data = {
        "duration": duration,
        "answered": answered,
        "recording_url": recording_url,
        "user": user,
        "phone_number": phone_number
    }
    activity = create_call_activity(lead_id, call_data)
    
    return {
        "message": "Llamada registrada en GHL",
        "lead_id": lead_id,
        "activity": activity
    }
