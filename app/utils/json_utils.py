def clean_json(text):
    text = text.replace("```json", "")
    text = text.replace("```", "")
    return text.strip()