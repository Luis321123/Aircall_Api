import httpx
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

GHL_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ims3Um9lUUtUMDZPZHY4Um9GT2pnIiwidmVyc2lvbiI6MSwiaWF0IjoxNzQzNjEzNDkwOTUzLCJzdWIiOiJyTjlhazB3czJ1YWJUa2tQQllVYiJ9.dFA5LRcQ2qZ4zBSfVRhG423LsEhrDgrbDcQfFMSMv0k"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1"

HEADERS_GHL = {
    "Authorization": f"Bearer {GHL_API_KEY}",
    "Content-Type": "application/json"
}

async def find_or_create_lead(phone_number: str):
    async with httpx.AsyncClient() as client:
        # Buscar contacto por teléfono (GHL usa /contacts con filtros)
        search_url = f"{GHL_BASE_URL}/contacts/"
        params = {"phone": phone_number}
        r = await client.get(search_url, headers=HEADERS_GHL, params=params)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Error buscando contacto en GHL: {r.text}")
        data = r.json()
        
        contacts = data.get("contacts", [])
        if contacts:
            return contacts[0]
        
        # Si no existe, crear contacto nuevo
        create_payload = {
            "firstName": "Desconocido",
            "phone": phone_number
        }
        r = await client.post(search_url, headers=HEADERS_GHL, json=create_payload)
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail=f"Error creando contacto en GHL: {r.text}")
        return r.json()

async def create_call_activity(lead_id: str, call_data: dict):
    async with httpx.AsyncClient() as client:
        activity_url = f"{GHL_BASE_URL}/contacts/{lead_id}/activities"
        
        # Payload para actividad llamada (ajustar según docs GHL)
        payload = {
            "activityType": "call",
            "duration": call_data.get("duration", 0),
            "callStatus": "answered" if call_data.get("answered") else "missed",
            "recordingUrl": call_data.get("recording_url"),
            "user": call_data.get("user"),
            "phone": call_data.get("phone_number"),
            "notes": f"Llamada { 'atendida' if call_data.get('answered') else 'perdida' } por usuario {call_data.get('user')}"
        }
        
        r = await client.post(activity_url, headers=HEADERS_GHL, json=payload)
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail=f"Error creando actividad en GHL: {r.text}")
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
        raise HTTPException(status_code=400, detail="Número no encontrado en el webhook")

    lead = await find_or_create_lead(phone_number)
    lead_id = lead.get("id")
    if not lead_id:
        raise HTTPException(status_code=500, detail="No se pudo obtener ID del lead en GHL")

    call_data = {
        "duration": duration,
        "answered": answered,
        "recording_url": recording_url,
        "user": user,
        "phone_number": phone_number,
    }
    activity = await create_call_activity(lead_id, call_data)

    return {
        "message": "Llamada registrada en GHL",
        "lead_id": lead_id,
        "activity": activity,
    }
import httpx
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

GHL_API_KEY = "TU_API_KEY_GHL"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1"

HEADERS_GHL = {
    "Authorization": f"Bearer {GHL_API_KEY}",
    "Content-Type": "application/json"
}

async def find_or_create_lead(phone_number: str):
    async with httpx.AsyncClient() as client:
        # Buscar contacto por teléfono (GHL usa /contacts con filtros)
        search_url = f"{GHL_BASE_URL}/contacts/"
        params = {"phone": phone_number}
        r = await client.get(search_url, headers=HEADERS_GHL, params=params)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Error buscando contacto en GHL: {r.text}")
        data = r.json()
        
        contacts = data.get("contacts", [])
        if contacts:
            return contacts[0]
        
        # Si no existe, crear contacto nuevo
        create_payload = {
            "firstName": "Desconocido",
            "phone": phone_number
        }
        r = await client.post(search_url, headers=HEADERS_GHL, json=create_payload)
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail=f"Error creando contacto en GHL: {r.text}")
        return r.json()

async def create_call_activity(lead_id: str, call_data: dict):
    async with httpx.AsyncClient() as client:
        activity_url = f"{GHL_BASE_URL}/contacts/{lead_id}/activities"
        
        # Payload para actividad llamada (ajustar según docs GHL)
        payload = {
            "activityType": "call",
            "duration": call_data.get("duration", 0),
            "callStatus": "answered" if call_data.get("answered") else "missed",
            "recordingUrl": call_data.get("recording_url"),
            "user": call_data.get("user"),
            "phone": call_data.get("phone_number"),
            "notes": f"Llamada { 'atendida' if call_data.get('answered') else 'perdida' } por usuario {call_data.get('user')}"
        }
        
        r = await client.post(activity_url, headers=HEADERS_GHL, json=payload)
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail=f"Error creando actividad en GHL: {r.text}")
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
        raise HTTPException(status_code=400, detail="Número no encontrado en el webhook")

    lead = await find_or_create_lead(phone_number)
    lead_id = lead.get("id")
    if not lead_id:
        raise HTTPException(status_code=500, detail="No se pudo obtener ID del lead en GHL")

    call_data = {
        "duration": duration,
        "answered": answered,
        "recording_url": recording_url,
        "user": user,
        "phone_number": phone_number,
    }
    activity = await create_call_activity(lead_id, call_data)

    return {
        "message": "Llamada registrada en GHL",
        "lead_id": lead_id,
        "activity": activity,
    }
