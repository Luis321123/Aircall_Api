from fastapi import FastAPI, Request
from utils import create_or_update_contact, create_call_activity
from datetime import datetime

app = FastAPI()


@app.post("/aircall/webhook")
async def receive_aircall_call(request: Request):
    body = await request.json()

    if body.get("event") != "call.ended":
        return {"message": "Evento no procesado"}

    call = body["data"]

    user = call["user"]
    phone = call["number"]["digits"]
    contact_number = call["via_number"]["digits"] if "via_number" in call else None
    duration = call.get("duration")
    status = call.get("status")
    recording_url = call.get("recording")

    # Crear o actualizar contacto
    contact_data = {
        "phone": contact_number,
        "first_name": "Contacto sin nombre",
        "customFields": {
            "Último número que llamó": phone,
            "Usuario que llamó": user["name"]
        }
    }

    contact_response = create_or_update_contact(contact_data)
    contact_id = contact_response.get("contact", {}).get("id")

    if not contact_id:
        return {"error": "No se pudo crear o identificar el contacto"}

    # Crear actividad
    activity_data = {
        "type": "call",
        "status": status,
        "duration": duration,
        "note": f"Llamada realizada por {user['name']} desde el número {phone}",
        "recording_url": recording_url,
        "timestamp": datetime.utcnow().isoformat()
    }

    activity_response = create_call_activity(contact_id, activity_data)

    return {
        "message": "Llamada registrada",
        "contact_id": contact_id,
        "activity": activity_response
    }
