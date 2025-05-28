from fastapi import FastAPI, Request
import httpx
import re
import logging

# ⚙️ Configuración del logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

# 🔐 API Key de GoHighLevel
GHL_API_KEY = "Bearer TU_API_KEY_AQUI"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1/contacts/"

# 🧼 Normaliza números (ej. +1 555-123-4567 -> 15551234567)
def normalize_phone(phone: str) -> str:
    normalized = re.sub(r"[^\d]", "", phone)
    logger.debug(f"Número normalizado: {normalized}")
    return normalized

# 🔍 Busca contacto en GHL
async def find_contact_by_phone(normalized_number: str) -> str:
    logger.info(f"🔎 Iniciando búsqueda de contacto por número: {normalized_number}")

    async with httpx.AsyncClient() as client:
        for page in range(1, 61):
            logger.debug(f"🔄 Consultando página {page}")
            response = await client.get(
                GHL_BASE_URL,
                headers={"Authorization": GHL_API_KEY},
                params={"limit": 100, "page": page}
            )

            if response.status_code != 200:
                logger.warning(f"⚠️ Error en página {page}: {response.status_code} - {response.text}")
                continue

            data = response.json()
            contacts = data.get("contacts", [])

            logger.debug(f"📦 Página {page}: {len(contacts)} contactos recibidos")

            for contact in contacts:
                contact_phone = contact.get("phone")
                if contact_phone:
                    normalized_contact_phone = normalize_phone(contact_phone)
                    if normalized_contact_phone.endswith(normalized_number) or normalized_number.endswith(normalized_contact_phone):
                        logger.info(f"✅ Contacto encontrado: ID={contact['id']} | Tel={contact_phone}")
                        return "OK"

    logger.info("❌ Contacto no encontrado")
    return "NOT FOUND"

# 📞 Webhook Aircall
@app.post("/webhook/aircall")
async def handle_aircall_webhook(request: Request):
    body = await request.json()
    logger.info(f"📩 Webhook recibido: {body}")

    raw_phone = body.get("call", {}).get("from_number")

    if not raw_phone:
        logger.error("📛 Número de teléfono no encontrado en la petición")
        return {"status": "ERROR", "detail": "No se recibió número de teléfono"}

    normalized_number = normalize_phone(raw_phone)
    logger.info(f"📲 Número recibido: {raw_phone} | Normalizado: {normalized_number}")

    result = await find_contact_by_phone(normalized_number)
    logger.info(f"🧪 Resultado final: {result}")
    return {"status": result}