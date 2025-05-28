from fastapi import FastAPI, Request
import httpx
import re
import logging
import asyncio

# ⚙️ Configuración del logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

# 🔐 API Key de GoHighLevel
GHL_API_KEY = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ims3Um9lUUtUMDZPZHY4Um9GT2pnIiwidmVyc2lvbiI6MSwiaWF0IjoxNzQzNjEzNDkwOTUzLCJzdWIiOiJyTjlhazB3czJ1YWJUa2tQQllVYiJ9.dFA5LRcQ2qZ4zBSfVRhG423LsEhrDgrbDcQfFMSMv0k"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1/contacts/"
MAX_CONCURRENT_REQUESTS = 1

# 🧼 Normaliza números
def normalize_phone(phone: str) -> str:
    return re.sub(r"[^\d]", "", phone)

# 🔍 Subproceso para buscar contactos en una página
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
            return None
    return None

# 🔍 Búsqueda principal
async def find_contact_by_phone(normalized_number: str) -> str:
    logger.info(f"🔎 Buscando contacto con número: {normalized_number}")
    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with httpx.AsyncClient() as client:
        tasks = [asyncio.create_task(search_page(client, page, normalized_number, sem)) for page in range(1, 61)]

        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()  # Cancelamos tareas pendientes

        for task in done:
            result = task.result()
            if result:
                logger.info(f"✅ Contacto encontrado: ID={result['id']} | Tel={result['phone']}")
                return f"OK - ID: {result['id']}"

    logger.info("❌ Contacto no encontrado")
    return "NOT FOUND"

# 📞 Webhook Aircall
@app.post("/webhook/aircall")
async def handle_aircall_webhook(request: Request):
    body = await request.json()
    logger.info("📩 Webhook recibido")

    try:
        raw_phone = body.get("data", {}).get("raw_digits")
        if not raw_phone:
            return {"status": "ERROR", "detail": "No se recibió número de teléfono"}

        normalized_number = normalize_phone(raw_phone)
        result = await find_contact_by_phone(normalized_number)
        return {"status": result}

    except Exception as e:
        logger.exception(f"❌ Error procesando el webhook: {e}")
        return {"status": "ERROR", "detail": str(e)}
