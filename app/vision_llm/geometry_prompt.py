GEOMETRY_PROMPT = """
You analyze ONE window construction image.

Your task:
detect window geometry.

Allowed segment kinds:

- FIX
- R
- RU

Rules:

FIX
- fixed glazing
- no opening symbol

R
- side opening
- single opening diagonal

RU
- tilt-turn opening
- more complex opening symbol
- usually crossing diagonals

Return STRICT JSON ONLY.

Also return confidence from 0.0 to 1.0.

Example:

{
  "category": "WINDOW",
  "segments": [
    {
      "kind": "FIX"
    },
    {
      "kind": "RU"
    }
  ]
}
"""