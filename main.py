from fastapi import FastAPI, Request, HTTPException
import requests

app = FastAPI()

# Configura tu API Key de GoHighLevel aquí
GHL_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ims3Um9lUUtUMDZPZHY4Um9GT2pnIiwidmVyc2lvbiI6MSwiaWF0IjoxNzQzNjEzNDkwOTUzLCJzdWIiOiJyTjlhazB3czJ1YWJUa2tQQllVYiJ9.dFA5LRcQ2qZ4zBSfVRhG423LsEhrDgrbDcQfFMSMv0k"
GHL_API_BASE = "https://api.gohighlevel.com/v1"

def search_contact(phone: str):
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }
    params = {"phone": phone}
    response = requests.get(f"{GHL_API_BASE}/contacts/search", headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        contacts = data.get("contacts", [])
        if contacts:
            return contacts[0]["id"]
    return None

def create_note(contact_id: str, content: str):
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "contactId": contact_id,
        "note": content
    }
    response = requests.post(f"{GHL_API_BASE}/notes", headers=headers, json=payload)
    return response.status_code == 201

@app.post("/webhook")
async def aircall_webhook(request: Request):
    data = await request.json()
    call = data.get("call")
    if not call:
        raise HTTPException(status_code=400, detail="No se encontró información de llamada")

    # Extraer info de la llamada
    phone = call.get("number")
    duration = call.get("duration", 0)
    answered = call.get("answered", False)
    user = call.get("user", {}).get("name", "Desconocido")
    recording_url = call.get("recording", {}).get("url", "No disponible")

    if not phone:
        raise HTTPException(status_code=400, detail="No se encontró número de teléfono en la llamada")

    # Buscar contacto en GHL
    contact_id = search_contact(phone)
    if not contact_id:
        raise HTTPException(status_code=404, detail="Contacto no encontrado en GoHighLevel")

    # Crear contenido de la nota
    note_content = (
        f"Llamada Aircall:\n"
        f"Número: {phone}\n"
        f"Usuario: {user}\n"
        f"Duración: {duration} segundos\n"
        f"Atendida: {'Sí' if answered else 'No'}\n"
        f"Grabación: {recording_url}"
    )

    # Crear nota en GHL
    success = create_note(contact_id, note_content)
    if not success:
        raise HTTPException(status_code=500, detail="Error al crear nota en GoHighLevel")

    return {"status": "ok", "message": "Llamada registrada correctamente"}

