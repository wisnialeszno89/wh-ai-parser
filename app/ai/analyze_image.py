from openai import OpenAI
import pandas as pd
import json
from prompt import WINDOW_PROMPT
from normalize import normalize_window
from validate import validate_construction
from report import generate_report

# ============================================
# OPENAI
# ============================================

client = OpenAI(
    api_key="KLUCZ AI"
)

# ============================================
# IMAGE URL
# ============================================

IMAGE_URL = "https://i.imgur.com/AUTGT7J.jpeg"

# ============================================
# REQUEST
# ============================================

response = client.responses.create(
    model="gpt-4.1-mini",

    input=[{
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": WINDOW_PROMPT
            },
            {
                "type": "input_image",
                "image_url": IMAGE_URL
            }
        ]
    }]
)

# ============================================
# OUTPUT TEXT
# ============================================

result = response.output_text

print(result)

# ============================================
# PARSE JSON
# ============================================

data = json.loads(result)

data = [normalize_window(w) for w in data]

for c in data:

    errors = validate_construction(c)

    if errors:

        print("\n[!] Błędy walidacji:")

        for e in errors:
            print("-", e)

# ============================================
# DATAFRAME
# ============================================

df = pd.DataFrame(data)

print(df)

# ============================================
# EXPORT EXCEL
# ============================================

df.to_excel("oferta.xlsx", index=False)

generate_report(data)

print("\n[+] Zapisano oferta.xlsx")