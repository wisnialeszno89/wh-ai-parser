# WH Object Model

## Confirmed Classes

| Class | Meaning |
|---|---|
| CKwatera | Segment / field |
| CSkrzydlo | Sash |
| CSzyba | Glass |
| CSlupek | Mullion |
| COsciez | Frame |
| CLacznik | Connector |
| CRoletaParapet | Roller shutter / sill |
| CDziura | Opening / cutout |
| CPosition | Positioning |
| CSkladnik | Component |

---

## Notes

Payload is zlib-compressed.

Format appears to be:
HEADER + ZLIB + serialized object graph.

Potential serialization:
- Delphi
- C++ Builder
- custom RTTI serializer