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
GHL_OAUTH_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoQ2xhc3MiOiJMb2NhdGlvbiIsImF1dGhDbGFzc0lkIjoiazdSb2VRS1QwNk9kdjhSb0ZPamciLCJzb3VyY2UiOiJJTlRFR1JBVElPTiIsInNvdXJjZUlkIjoiNjgzNWVhNWU0ZTFlMzM0NDljNTExMzljLW1iNnZuM3l2IiwiY2hhbm5lbCI6Ik9BVVRIIiwicHJpbWFyeUF1dGhDbGFzc0lkIjoiazdSb2VRS1QwNk9kdjhSb0ZPamciLCJvYXV0aE1ldGEiOnsic2NvcGVzIjpbImNvbnRhY3RzLnJlYWRvbmx5IiwiY29udGFjdHMud3JpdGUiXSwiY2xpZW50IjoiNjgzNWVhNWU0ZTFlMzM0NDljNTExMzljIiwidmVyc2lvbklkIjoiNjgzNWVhNWU0ZTFlMzM0NDljNTExMzljIiwiY2xpZW50S2V5IjoiNjgzNWVhNWU0ZTFlMzM0NDljNTExMzljLW1iNnZuM3l2In0sImlhdCI6MTc0ODM3NTg4MS42NDUsImV4cCI6MTc0ODQ2MjI4MS42NDV9.JYhphBUZyNMK2Wya9EXzzVGtsG2DY1Pbxhru-V5w5xTHUqQsq4CCXbAs7Lkd0DBM-IqkzBRE1SvWmbHZeJkKV4TdIrYOGTyBupn0PKBakDfKr_5aC-lH9p-fnvC5xjB_yiU3ckaJ4bb7Beq847gwWriGyHyNciBwnsM5mu4NFA1xytwJ87IMKWno_cLjo9DufVzz57wflgddi6RBg4Y3yuKfHz2wf_VpePQO9yWdHT8NwpTV6K5uvdvaa8cYNPM1_MvqFJJfU8e918BTDf4raON1MfNUu-nDPm90X7kx1Bu6v9UrNau1CmT4eMo2xF3F1D_lgQX6MIiWE17vArhz0HKDOzmKVNFnMqxIzmcPvDeqEHui3TrYxi1hePuw4mLePF1upKs2NTqguitVGjPKROnWW-wqGwMiCHlBJ9_WkuySFbfzuYD08usANYVjBV5eJTq53Uy8T-uWrFM_Y2chDnZUd3ii6sJiRr1OyVUMrhd_Kys0cA-4mcG8f8lhnVVWz4dpaSimQXOPrh0J5KZTHvYN4Fmr4m48c6Y_moAf-suwgSEIFFC3jHkmgrflRDKqHjVq_D8vNnBNFgLyCeIwvC6_7s84l9gzTRAoakyVZ1KMz2NUzDZOHeLqU054qeCzptwPBzG-fheppeVO8LFors71Orwm07tuD0MN5b1wkyI"  # el token que obtuviste vía OAuth2
GHL_BASE_URL_V2 = "https://api.gohighlevel.com/v2"

HEADERS_V2 = {
    "Authorization": f"Bearer {GHL_OAUTH_TOKEN}",
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

def normalizar_numero(numero: str) -> str:
    """Quita todo menos dígitos y devuelve los últimos 10."""
    dígitos = re.sub(r'\D', '', numero)
    return dígitos[-10:]

def buscar_contacto_por_telefono_v2(numero_busqueda: str):
    """
    Usa el endpoint v2 para buscar un contacto por teléfono.
    Devuelve el objeto contacto o None si no existe.
    """
    payload = {"phone": normalizar_numero(numero_busqueda)}
    resp = requests.post(f"{GHL_BASE_URL_V2}/contacts/search",
                         headers=HEADERS_V2,
                         json=payload)
    if resp.status_code == 200:
        data = resp.json()
        contactos = data.get("contacts", [])
        if contactos:
            logging.info(f"✅ Contacto encontrado en v2: {contactos[0]['phone']}")
            return contactos[0]
        else:
            logging.info("🔍 No hay coincidencias en v2")
            return None
    else:
        logging.error(f"❌ Error v2 search: {resp.status_code} {resp.text}")
        return None

@app.post("/aircall/webhook")
async def handle_aircall_webhook(request: Request):
    payload = await request.json()
    logging.info(f"📞 Payload recibido: {payload}")

    if payload.get("event") != "call.answered":
        logging.info("🔔 Evento no manejado.")
        return {"status": "ok"}

    data = payload["data"]
    raw = data.get("raw_digits", "")
    cliente_tel = normalizar_numero(raw)
    if not cliente_tel:
        logging.warning("⚠️ Número cliente inválido.")
        return {"status": "missing phone"}

    contacto = buscar_contacto_por_telefono_v2(cliente_tel)
    if contacto:
        logging.info(f"✅ Cliente {cliente_tel} existe en CRM (v2). ID: {contacto['id']}")
    else:
        logging.info(f"❌ Cliente {cliente_tel} NO existe en CRM (v2).")

    return {"status": "ok"}