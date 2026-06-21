import os
import json
import base64
from mistralai.client import Mistral

_TEXT_MODEL = "mistral-small-latest"
_VISION_MODEL = "pixtral-12b-2409"

_SYSTEM = (
    "Sei un assistente medico che analizza documenti sanitari italiani. "
    "Rispondi SEMPRE e SOLO con JSON valido, senza testo aggiuntivo, senza markdown."
)

_JSON_SCHEMA = """{
  "conditions": [{"nome": "...", "data_diagnosi": "YYYY-MM-DD o null", "note": "..."}],
  "medications": [{"nome": "...", "dosaggio": "...", "data_inizio": "YYYY-MM-DD o null", "orari": ["HH:MM"]}],
  "appointments": [{"specialista": "...", "data_prossima": "YYYY-MM-DD o null"}],
  "exams": [{"tipo": "...", "data_prossima": "YYYY-MM-DD o null"}],
  "prescriptions": [{"farmaco": "...", "data_prossima": "YYYY-MM-DD o null"}]
}"""

_INSTRUCTION = (
    "Estrai le informazioni cliniche rilevanti e restituiscile nel formato JSON seguente.\n"
    "Se una categoria non ha dati, usa un array vuoto []. Non inventare informazioni.\n\n"
    + _JSON_SCHEMA
)


def _client() -> Mistral:
    return Mistral(api_key=os.getenv("MISTRAL_API_KEY"))


def _parse(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)


def extract_from_text(text: str) -> dict:
    resp = _client().chat.complete(
        model=_TEXT_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"{_INSTRUCTION}\n\nTesto documento:\n{text}"},
        ],
    )
    return _parse(resp.choices[0].message.content)


def extract_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    b64 = base64.standard_b64encode(image_bytes).decode()
    data_url = f"data:{mime_type};base64,{b64}"
    resp = _client().chat.complete(
        model=_VISION_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": _INSTRUCTION},
                ],
            },
        ],
    )
    return _parse(resp.choices[0].message.content)
