from fastapi import FastAPI, Request, HTTPException
import requests
import logging

app = FastAPI()

GHL_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ims3Um9lUUtUMDZPZHY4Um9GT2pnIiwidmVyc2lvbiI6MSwiaWF0IjoxNzQzNjEzNDkwOTUzLCJzdWIiOiJyTjlhazB3czJ1YWJUa2tQQllVYiJ9.dFA5LRcQ2qZ4zBSfVRhG423LsEhrDgrbDcQfFMSMv0k"
GHL_BASE_URL = "https://rest.gohighlevel.com/v1"

def add_call_to_ghl(contact_id: str, call_info: dict):
    url = f"{GHL_BASE_URL}/contacts/{contact_id}/notes"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "note": f"Llamada de {call_info['user_name']} al número {call_info['number']}. Duración: {call_info['duration']} segundos. Estado: {'Atendida' if call_info['answered'] else 'No atendida'}. Grabación: {call_info.get('recording_url', 'No disponible')}"
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def find_contact_by_phone(phone_number: str):
    url = f"{GHL_BASE_URL}/contacts/search"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}"
    }
    params = {"phone": phone_number}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    if data.get('contacts'):
        return data['contacts'][0]['id']
    return None

@app.post("/webhook")
async def webhook(request: Request):
    try:
        payload = await request.json()
        logging.info(f"Payload recibido: {payload}")
        
        call_data = payload['data']
        user = call_data['user']
        number = call_data['raw_digits']
        duration = call_data.get('duration', 0)
        answered = call_data['answered_at'] is not None
        recording_url = call_data.get('recording')

        contact_id = find_contact_by_phone(number)
        if not contact_id:
            logging.warning(f"No se encontró contacto con número: {number}")
            return {"error": "Contacto no encontrado en GHL"}

        call_info = {
            "user_name": user['name'],
            "number": number,
            "duration": duration,
            "answered": answered,
            "recording_url": recording_url
        }

        result = add_call_to_ghl(contact_id, call_info)
        return {"status": "success", "result": result}
    except Exception as e:
        logging.error(f"Error en webhook: {e}")
        raise HTTPException(status_code=400, detail=str(e))
