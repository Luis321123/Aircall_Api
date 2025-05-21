import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

load_dotenv()

GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_BASE_URL = os.getenv("GHL_BASE_URL")

headers = {
    "Authorization": f"Bearer {GHL_API_KEY}",
    "Content-Type": "application/json"
}


def create_or_update_contact(contact_data):
    url = f"{GHL_BASE_URL}/contacts/"
    response = requests.post(url, headers=headers, json=contact_data)
    return response.json()


def create_call_activity(contact_id, activity_data):
    url = f"{GHL_BASE_URL}/contacts/{contact_id}/activities"
    response = requests.post(url, headers=headers, json=activity_data)
    return response.json()


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
        print(f"❌ Error al buscar contacto: {response.status_code} - {response.text}")
        return None

def crear_nota_llamada_en_ghl(call_data):
    contact_phone = call_data["contact"]["phone_numbers"][0]
    user_name = call_data["user"]["name"]
    duration = call_data["duration"]
    recording_url = call_data.get("recording", {}).get("url")
    start_time = call_data["started_at"]

    dt_obj = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    formatted_time = dt_obj.astimezone(pytz.timezone("America/Mexico_City")).strftime("%d/%m/%Y %H:%M")

    nota = f"""📞 Llamada atendida por {user_name} el {formatted_time}
📆 Duración: {duration} segundos
🔗 Grabación: {recording_url if recording_url else 'No disponible'}"""

    contacto = buscar_contacto_ghl_por_telefono(contact_phone)
    if not contacto:
        print("❌ Contacto no encontrado en GHL")
        return

    contact_id = contacto["id"]
    url = f"{GHL_BASE_URL}/contacts/{contact_id}/notes"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json={"body": nota}, headers=headers)
    if response.status_code == 200:
        print("✅ Nota creada exitosamente")
    else:
        print(f"❌ Error al crear nota: {response.status_code} - {response.text}")
