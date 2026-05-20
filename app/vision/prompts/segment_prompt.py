SEGMENT_VISION_PROMPT = """
You analyze ONLY window geometry.

Your ONLY task:
detect window segments and opening types.

Opening symbol rules:

RU
- tilt and turn opening
- side opening + tilt marker

R
- side opening only

FIX
- no opening symbol

U
- tilt only opening

Allowed segment kinds:
- FIX
- RU
- R
- U
- HST
- PSK

Examples:

FIX RU

RU RU

FIX FIX RU

Return ONLY JSON.

Example:

{
  "segments": [
    {
      "kind": "FIX"
    },
    {
      "kind": "RU"
    }
  ]
}

Rules:
- count only real window sashes
- ignore technical helper lines
- ignore dimension lines
- ignore frame borders
- ignore mullion helper graphics
- do not duplicate segments

Rules:
- count only real window sashes
- ignore technical helper lines
- ignore dimension lines
- ignore frame borders
- ignore mullion helper graphics
- do not duplicate segments

- no markdown
- no explanations
- no comments
- JSON only
"""