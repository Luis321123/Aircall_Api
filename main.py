from fastapi import FastAPI, Request
import requests
import logging

app = FastAPI()

# Configura el logging para que puedas ver los logs en la consola
logging.basicConfig(level=logging.INFO)

# Reemplaza con tu API key real de GoHighLevel
GHL_API_KEY = "Bearer TU_API_KEY"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1"

# Esta función crea o actualiza un contacto en GHL
def create_or_update_contact(phone_number, first_name, user_name):
    url = f"{GHL_BASE_URL}/contacts/"
    headers = {
        "Authorization": GHL_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "phone": phone_number,
        "firstName": first_name,
        "customField": {
            "Llamado por": user_name  # Si no tienes este custom field aún en GHL, podemos omitirlo
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    logging.info("📤 Enviado a GHL: %s", payload)
    logging.info("📥 Respuesta de GHL: %s", response.text)

    return response.json()

# Este endpoint recibe los webhooks de Aircall
@app.post("/aircall/webhook")
async def receive_aircall_call(request: Request):
    payload = await request.json()
    logging.info("📞 Payload recibido: %s", payload)

    try:
        phone = payload["call"]["contact"]["phone_numbers"][0]["value"]
        user_name = payload["call"]["user"]["name"]
    except KeyError as e:
        logging.error(f"Error extrayendo datos: {e}")
        return {"error": "Datos incompletos"}

    # Crea o actualiza el contacto en GHL
    ghl_response = create_or_update_contact(phone, "Lead de llamada", user_name)

    return {"status": "ok", "ghl_response": ghl_response}
