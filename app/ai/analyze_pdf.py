from openai import OpenAI
import fitz
import base64
import pandas as pd
import json
from normalize import normalize_window
from prompt import WINDOW_PROMPT
from validate import validate_construction
from report import generate_report

# ============================================
# OPENAI
# ============================================

client = OpenAI(
    api_key="TU_API_KEY"
)

# ============================================
# LOAD PDF PAGE
# ============================================

pdf = fitz.open("projekt.pdf")

page = pdf[0]

pix = page.get_pixmap()

image_path = "page.png"

pix.save(image_path)

# ============================================
# BASE64
# ============================================

with open(image_path, "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

# ============================================
# AI REQUEST
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
                "image_url": f"data:image/png;base64,{image_base64}"
            }
        ]
    }]
)

# ============================================
# OUTPUT
# ============================================

result = response.output_text

print(result)

# ============================================
# EXCEL
# ============================================

data = json.loads(result)

data = [normalize_window(w) for w in data]

for c in data:

    errors = validate_construction(c)

    if errors:

        print("\n[!] Błędy walidacji:")

        for e in errors:
            print("-", e)

df = pd.DataFrame(data)

df.to_excel("oferta.xlsx", index=False)

generate_report(data)

print("\n[+] Zapisano oferta.xlsx")