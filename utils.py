import requests
import os
from dotenv import load_dotenv

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


