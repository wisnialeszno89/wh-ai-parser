MULTI_LAYOUT_PROMPT = """
You analyze a technical window offer page.

The image may contain:
- multiple constructions
- multiple window groups
- dimensions
- technical annotations

Your task:

Detect ALL separate constructions visible on the page.

For each construction return:

- category
- width_mm
- height_mm
- segments
- confidence

Allowed segment kinds:

- FIX
- R
- RU

Return STRICT JSON ONLY.

{
  "constructions": [

    {
      "category": "WINDOW",

      "width_mm": 2300,
      "height_mm": 1310,

      "confidence": 0.95,

      "segments": [
        {
          "kind": "RU"
        },
        {
          "kind": "RU"
        }
      ]
    },

    {
      "category": "WINDOW",

      "width_mm": 1180,
      "height_mm": 1310,

      "confidence": 0.97,

      "segments": [
        {
          "kind": "RU"
        }
      ]
    }
  ]
}
"""