# import json
from google.cloud import translate_v3 as translate
# from google.oauth2 import service_account

# # 🔹 Path to your downloaded service account JSON key
# KEY_PATH = r"C:\Users\shenyanjian\Desktop\CodeRepo\translator\church-translatior-d03ffc4a4850.json"
#
# # Load credentials explicitly from the JSON key
# credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
# print(credentials)
# # Read project_id directly from the same JSON file
# with open(KEY_PATH, "r", encoding="utf-8") as f:
#     key_data = json.load(f)
# PROJECT_ID = key_data["project_id"]

def translate_text(text: str, source_language: str = "en", target_language: str = "zh", credentials=None, PROJECT_ID=''):
    # Create Translation client with explicit credentials
    client = translate.TranslationServiceClient(credentials=credentials)
    parent = f"projects/{PROJECT_ID}/locations/global"

    response = client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "mime_type": "text/plain",   # can also use "text/html"
            "source_language_code": source_language,
            "target_language_code": target_language,
        }
    )

    return response.translations[0].translated_text

if __name__ == "__main__":
    english_text = "How are you?"
    chinese_text = translate_text(english_text)
    print("English:", english_text)
    print("Chinese:", chinese_text)
