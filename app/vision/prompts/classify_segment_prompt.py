CLASSIFY_SEGMENT_PROMPT = """
You analyze ONE isolated window segment.

Classify ONLY:

- FIX
- R
- RU

Definitions:

FIX
- no opening lines

R
- single opening diagonal

RU
- opening diagonal
- plus tilt opening marker
- usually two directional opening lines

Important:
RU has more complex opening geometry than R.

Return ONLY JSON.

Example:

{
  "kind": "RU"
}
"""