from fastapi import FastAPI, Request
import httpx
import re

app = FastAPI()

# 🔐 API Key de GoHighLevel
GHL_API_KEY = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ims3Um9lUUtUMDZPZHY4Um9GT2pnIiwidmVyc2lvbiI6MSwiaWF0IjoxNzQzNjEzNDkwOTUzLCJzdWIiOiJyTjlhazB3czJ1YWJUa2tQQllVYiJ9.dFA5LRcQ2qZ4zBSfVRhG423LsEhrDgrbDcQfFMSMv0k"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1/contacts/"

# 🧼 Normaliza números (ej. +1 555-123-4567 -> 15551234567)
def normalize_phone(phone: str) -> str:
    return re.sub(r"[^\d]", "", phone)

# 🔍 Busca contacto en GHL
async def find_contact_by_phone(normalized_number: str) -> str:
    async with httpx.AsyncClient() as client:
        for page in range(1, 61):  # 60 páginas
            response = await client.get(
                GHL_BASE_URL,
                headers={"Authorization": GHL_API_KEY},
                params={"limit": 100, "page": page}
            )
            if response.status_code != 200:
                print(f"Error en página {page}: {response.text}")
                continue

            contacts = response.json().get("contacts", [])
            for contact in contacts:
                contact_phone = contact.get("phone")
                if contact_phone:
                    normalized_contact_phone = normalize_phone(contact_phone)
                    if normalized_contact_phone.endswith(normalized_number) or normalized_number.endswith(normalized_contact_phone):
                        print(f"✅ Contacto encontrado: {contact['id']}")
                        return "OK"
    return "NOT FOUND"

# 📞 Webhook Aircall
@app.post("/webhook/aircall")
async def handle_aircall_webhook(request: Request):
    body = await request.json()
    
    # Extraemos el número (ajustar según el formato que mande Aircall)
    raw_phone = body.get("call", {}).get("from_number")
    
    if not raw_phone:
        return {"status": "ERROR", "detail": "No se recibió número de teléfono"}

    normalized_number = normalize_phone(raw_phone)
    print(f"🔎 Buscando número: {normalized_number}")
    
    result = await find_contact_by_phone(normalized_number)
    return {"status": result}
