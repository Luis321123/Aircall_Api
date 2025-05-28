import asyncio
import httpx
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

MAX_CONCURRENT_REQUESTS = 10
contact_cache = {}  # Estructura: {phone_number: (resultado, expiry_datetime)}
CACHE_TTL_SECONDS = 60


async def search_page(client: httpx.AsyncClient, page: int, normalized_number: str, sem: asyncio.Semaphore) -> dict | None:
    url = f"https://api.hubspot.com/crm/v3/objects/contacts/search"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ims3Um9lUUtUMDZPZHY4Um9GT2pnIiwidmVyc2lvbiI6MSwiaWF0IjoxNzQzNjEzNDkwOTUzLCJzdWIiOiJyTjlhazB3czJ1YWJUa2tQQllVYiJ9.dFA5LRcQ2qZ4zBSfVRhG423LsEhrDgrbDcQfFMSMv0k",
        "Content-Type": "application/json"
    }
    query = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "phone",
                        "operator": "EQ",
                        "value": normalized_number
                    }
                ]
            }
        ],
        "properties": ["phone"],
        "limit": 1,
        "after": (page - 1) * 1  # paginado simulado
    }

    async with sem:
        try:
            response = await client.post(url, json=query, headers=headers)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if results:
                return {
                    "id": results[0]["id"],
                    "phone": results[0]["properties"]["phone"]
                }
        except Exception as e:
            logger.warning(f"⚠️ Error en página {page}: {e}")
    return None


async def find_contact_by_phone(normalized_number: str) -> str:
    now = datetime.utcnow()

    # ✅ Revisión de caché
    if normalized_number in contact_cache:
        cached_result, expiry = contact_cache[normalized_number]
        if now < expiry:
            logger.info(f"♻️ Cache HIT para número: {normalized_number}")
            return cached_result
        else:
            del contact_cache[normalized_number]  # expirado

    logger.info(f"🔎 Buscando contacto con número: {normalized_number}")
    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with httpx.AsyncClient() as client:
        tasks = [
            asyncio.create_task(search_page(client, page, normalized_number, sem))
            for page in range(1, 61)
        ]

        try:
            for completed in asyncio.as_completed(tasks):
                result = await completed
                if result:
                    # Cancelar tareas restantes
                    for task in tasks:
                        if not task.done():
                            task.cancel()

                    logger.info(f"✅ Contacto encontrado: Número {normalized_number} | ID={result['id']} | Tel={result['phone']}")
                    # ✅ Guardar en cache con tiempo de expiración
                    contact_cache[normalized_number] = (f"OK - ID: {result['id']}", now + timedelta(seconds=CACHE_TTL_SECONDS))
                    return f"OK - ID: {result['id']}"
        except Exception as e:
            logger.warning(f"⚠️ Error durante búsqueda asincrónica: {e}")

    logger.info(f"❌ Número no encontrado: {normalized_number}")
    contact_cache[normalized_number] = ("NOT FOUND", now + timedelta(seconds=CACHE_TTL_SECONDS))
    return "NOT FOUND"
