import requests
from fastapi import FastAPI, Request

app = FastAPI()

GHL_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ims3Um9lUUtUMDZPZHY4Um9GT2pnIiwidmVyc2lvbiI6MSwiaWF0IjoxNzQzNjEzNDkwOTUzLCJzdWIiOiJyTjlhazB3czJ1YWJUa2tQQllVYiJ9.dFA5LRcQ2qZ4zBSfVRhG423LsEhrDgrbDcQfFMSMv0k"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1"

HEADERS_GHL = {
    "Authorization": f"Bearer {GHL_API_KEY}",
    "Content-Type": "application/json"
}

def find_or_create_lead(phone_number: str):
    # Buscar contacto por teléfono
    url = f"{GHL_BASE_URL}/contacts/?phone={phone_number}"
    r = requests.get(url, headers=HEADERS_GHL)
    data = r.json()
    
    if data.get("contacts"):
        # Retornamos el primer contacto encontrado
        return data["contacts"][0]
    else:
        # Crear contacto nuevo
        payload = {
            "phone": phone_number,
            "firstName": "Desconocido"  # opcional, o extraer del webhook si tienes nombre
        }
        r = requests.post(f"{GHL_BASE_URL}/contacts/", headers=HEADERS_GHL, json=payload)
        return r.json()

def create_call_activity(lead_id: str, call_data: dict):
    # Crear un registro (nota, tarea o actividad) en GHL para la llamada
    # Esto depende de cómo GHL maneje actividades (ajustar según la API actual)
    payload = {
        "leadId": lead_id,
        "type": "call",
        "duration": call_data.get("duration"),
        "callStatus": "answered" if call_data.get("answered") else "missed",
        "recordingUrl": call_data.get("recording_url"),
        "user": call_data.get("user"),
        "phone": call_data.get("phone_number")
    }
    # Ejemplo, ajustar endpoint según doc GHL
    r = requests.post(f"{GHL_BASE_URL}/activities/", headers=HEADERS_GHL, json=payload)
    return r.json()

@app.post("/webhook")
async def aircall_webhook(request: Request):
    payload = await request.json()
    
    call = payload.get("call", {})
    
    # Extraer número y datos
    phone_number = call.get("from", {}).get("number") or call.get("to", {}).get("number")
    user = call.get("from", {}).get("user", "Desconocido")
    duration = call.get("duration", 0)
    answered = call.get("answered", False)
    recording_url = call.get("recording", {}).get("url", "")
    
    if not phone_number:
        return {"error": "Número no encontrado en el webhook"}
    
    # Buscar o crear lead en GHL
    lead = find_or_create_lead(phone_number)
    lead_id = lead.get("id")
    
    # Crear registro de llamada
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
