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
    url = f"{GHL_BASE_URL}/contacts/?phone={phone_number}"
    r = requests.get(url, headers=HEADERS_GHL)
    r.raise_for_status()
    data = r.json()

    if data.get("contacts"):
        return data["contacts"][0]
    else:
        payload = {
            "phone": phone_number,
            "firstName": "Desconocido"
        }
        r = requests.post(f"{GHL_BASE_URL}/contacts/", headers=HEADERS_GHL, json=payload)
        r.raise_for_status()
        return r.json()

def create_call_note(lead_id: str, call_data: dict):
    note_text = (
        f"Llamada {'contestada' if call_data.get('answered') else 'no contestada'}\n"
        f"Duración: {call_data.get('duration')} segundos\n"
        f"Teléfono: {call_data.get('phone_number')}\n"
        f"Usuario que llamó: {call_data.get('user')}\n"
        f"Grabación: {call_data.get('recording_url') or 'No disponible'}"
    )
    payload = {
        "contactId": lead_id,
        "note": note_text
    }
    r = requests.post(f"{GHL_BASE_URL}/notes/", headers=HEADERS_GHL, json=payload)
    r.raise_for_status()
    return r.json()

@app.post("/webhook")
async def aircall_webhook(request: Request):
    payload = await request.json()

    call = payload.get("call", {})

    phone_number = call.get("from", {}).get("number") or call.get("to", {}).get("number")
    user = call.get("from", {}).get("user", "Desconocido")
    duration = call.get("duration", 0)
    answered = call.get("answered", False)
    recording_url = call.get("recording", {}).get("url", "")

    if not phone_number:
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
    activity = create_call_note(lead_id, call_data)

    return {
        "message": "Llamada registrada en GHL como nota",
        "lead_id": lead_id,
        "activity": activity
    }
