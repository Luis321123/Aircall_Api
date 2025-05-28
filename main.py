from fastapi import FastAPI, Request
import httpx
import re
import logging
from datetime import datetime
import asyncio
from zoneinfo import ZoneInfo

# Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI()

# Configuración
GHL_API_KEY = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ims3Um9lUUtUMDZPZHY4Um9GT2pnIiwidmVyc2lvbiI6MSwiaWF0IjoxNzQzNjEzNDkwOTUzLCJzdWIiOiJyTjlhazB3czJ1YWJUa2tQQllVYiJ9.dFA5LRcQ2qZ4zBSfVRhG423LsEhrDgrbDcQfFMSMv0k"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1/contacts/"
MAX_CONCURRENT_REQUESTS = 1

# Normaliza números
def normalize_phone(phone: str) -> str:
    return re.sub(r"[^\d]", "", phone)

# Agrega nota a un contacto
async def add_note_to_contact(contact_id: str, description: str):
    colombia_time = datetime.now(ZoneInfo("America/Bogota")).strftime("%Y-%m-%d %H:%M:%S")
    note_text = f"{description}\n🕒 Guardado el {colombia_time} (hora Colombia)"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://rest.gohighlevel.com/v1/contacts/{contact_id}/notes/",
            headers={
                "Authorization": GHL_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "body": note_text
            }
        )
        if response.status_code == 200:
            logger.info(f"📝 Nota agregada al contacto {contact_id}")
        else:
            logger.error(f"❌ Error al agregar nota: {response.status_code} - {response.text}")

# Busca contactos por página
async def search_page(client, page, normalized_number, sem: asyncio.Semaphore):
    async with sem:
        try:
            response = await client.get(
                GHL_BASE_URL,
                headers={"Authorization": GHL_API_KEY},
                params={"limit": 100, "page": page}
            )
            if response.status_code != 200:
                return None

            contacts = response.json().get("contacts", [])
            for contact in contacts:
                contact_phone = contact.get("phone")
                if contact_phone:
                    normalized_contact_phone = normalize_phone(contact_phone)
                    if normalized_contact_phone.endswith(normalized_number) or normalized_number.endswith(normalized_contact_phone):
                        return contact
        except Exception:
            pass
    return None

# Busca contacto y agrega una nota enriquecida
async def find_contact_by_phone(normalized_number: str) -> str:
    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    async with httpx.AsyncClient() as client:
        tasks = [asyncio.create_task(search_page(client, page, normalized_number, sem)) for page in range(1, 61)]
        try:
            for completed_task in asyncio.as_completed(tasks):
                result = await completed_task
                if result:
                    # Cancelar tareas restantes
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    # 🔒 Log final si se encontró
                    logger.info(f"✅ Contacto encontrado | ID={result['id']} | Tel={result['phone']}")
                    return f"OK - ID: {result['id']}"
        except Exception as e:
            logger.warning(f"⚠️ Error durante la búsqueda: {e}")
    
    # 🔒 Log final si no se encontró
    logger.info(f"❌ Contacto NO encontrado: {normalized_number}")
    return "NOT FOUND"


# Webhook de Aircall enriquecido
@app.post("/webhook/aircall")
async def handle_aircall_webhook(request: Request):
    body = await request.json()

    if body.get("event") != "call.ended":
        return {"status": "IGNORED", "detail": "No es una llamada finalizada"}

    raw_phone = body.get("data", {}).get("raw_digits")
    if not raw_phone:
        return {"status": "ERROR", "detail": "Número de teléfono no presente"}

    normalized_number = normalize_phone(raw_phone)

    # Datos adicionales para la nota
    agent = body.get("data", {}).get("user", {}).get("name", "Desconocido")
    answered = "Sí" if body.get("data", {}).get("answered") else "No"
    duration = body.get("data", {}).get("duration", 0)
    recording_url = body.get("data", {}).get("recordings", [{}])[0].get("url", "No disponible")

    nota = (
        f"📞 Llamada registrada desde Aircall\n"
        f"👤 Agente: {agent}\n"
        f"✅ Atendida: {answered}\n"
        f"⏱️ Duración: {duration} segundos\n"
        f"🎙️ Grabación: {recording_url}"
    )

    result = await find_contact_and_add_note(normalized_number, nota)
    return {"status": result}
