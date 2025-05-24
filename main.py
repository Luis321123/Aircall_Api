from fastapi import FastAPI, Request
import requests
import logging
from datetime import datetime
import pytz
import re

app = FastAPI()

logging.basicConfig(level=logging.INFO)

GHL_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ims3Um9lUUtUMDZPZHY4Um9GT2pnIiwidmVyc2lvbiI6MSwiaWF0IjoxNzQzNjEzNDkwOTUzLCJzdWIiOiJyTjlhazB3czJ1YWJUa2tQQllVYiJ9.dFA5LRcQ2qZ4zBSfVRhG423LsEhrDgrbDcQfFMSMv0k"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1"


HEADERS = {
    "Authorization": f"Bearer {GHL_API_KEY}",
    "Content-Type": "application/json"
}


def normalizar_numero(numero: str) -> str:
    return re.sub(r'\D', '', numero)

def numeros_coinciden(numero_aircall: str, numero_crm: str) -> bool:
    n1 = normalizar_numero(numero_aircall)
    n2 = normalizar_numero(numero_crm)
    return n1[-10:] == n2[-10:]

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
    
def obtener_todos_los_contactos_ghl(limit=100):
    url = f"https://rest.gohighlevel.com/v1/contacts?limit={limit}"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("contacts", [])
    else:
        logging.error(f"❌ Error al obtener contactos: {response.status_code} - {response.text}")
        return []



def buscar_staff_por_email(email: str):
    url = "https://rest.gohighlevel.com/v1/users/"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        staff_list = response.json().get("users", [])
        for user in staff_list:
            if user.get("email", "").lower() == email.lower():
                return user
        return None
    else:
        logging.error(f"❌ Error al obtener staff de GHL: {response.status_code} - {response.text}")
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


def buscar_contacto_ghl_por_email(email: str):
    url = f"https://rest.gohighlevel.com/v1/contacts/search?email={email}"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        contacts = data.get("contacts", [])
        return contacts[0] if contacts else None
    else:
        logging.error(f"❌ Error buscando contacto por email: {response.status_code} - {response.text}")
        return None

def buscar_contacto_ghl_por_telefono(numero_busqueda: str):
    per_page = 100
    start_after_id = None

    while True:
        params = {"limit": per_page}
        if start_after_id:
            params["startAfterId"] = start_after_id

        response = requests.get(GHL_BASE_URL, headers=HEADERS, params=params)

        if response.status_code != 200:
            logging.error(f"❌ Error al obtener contactos de GHL: {response.text}")
            break

        data = response.json()
        contactos = data.get("contacts", [])

        if not contactos:
            break  # No hay más contactos

        for contacto in contactos:
            telefono_contacto = contacto.get("phone")
            if telefono_contacto:
                logging.info(f"🔍 Comparando {numero_busqueda} con {telefono_contacto}")
                if numeros_coinciden(numero_busqueda, telefono_contacto):
                    logging.info(f"✅ Coincidencia encontrada con {telefono_contacto}")
                    return contacto  # Match encontrado

        # Preparar para la siguiente página
        start_after_id = contactos[-1].get("id")

    return None  # No se encontró coincidencia





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

    url = f"https://rest.gohighlevel.com/v1/contacts/search?phone={phone_number}"
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
            logging.info("📞 Evento 'call.answered' recibido.")

            user_email = data.get("user", {}).get("email")
            if not user_email:
                logging.warning("⚠️ No se pudo obtener el correo del usuario.")
                return {"status": "missing user email"}

            # Verificar si el usuario está en el staff
            staff_user = buscar_staff_por_email(user_email)
            if staff_user:
                logging.info(f"✅ Usuario {user_email} está en el staff.")
            else:
                logging.info(f"❌ Usuario {user_email} no está en el staff.")

            # Obtener y normalizar el número del cliente
            raw_phone = data.get("raw_digits", "")
            client_phone_normalizado = normalizar_numero(raw_phone)

            if not client_phone_normalizado:
                logging.warning("⚠️ No se pudo obtener el número del cliente.")
                return {"status": "missing or invalid client phone"}

            # Obtener lista de contactos del CRM (podrías modificar esta función para traer varios contactos)
            contactos = obtener_todos_los_contactos_ghl()  # Implementa esta función para obtener una lista de contactos

            # Buscar contacto con número que coincida
            contacto_encontrado = None
            for contacto in contactos:
                # Suponiendo que el contacto tiene un campo 'phone'
                numero_crm = contacto.get("phone", "")
                if numero_crm and numeros_coinciden(client_phone_normalizado, numero_crm):
                    contacto_encontrado = contacto
                    break

            if contacto_encontrado:
                logging.info(f"✅ Cliente con teléfono {client_phone_normalizado} está registrado en el CRM.")
            else:
                logging.info(f"❌ Cliente con teléfono {client_phone_normalizado} no está registrado en el CRM.")

        else:
            logging.info(f"🔔 Evento no manejado: {event_type}")

    except Exception as e:
        logging.error(f"❌ Error procesando el webhook: {e}")

    return {"status": "ok"}

