# Window Intelligence Platform (WIP)

## Vision

Window Intelligence Platform jest systemem AI, którego celem jest
automatyczne przygotowanie kompletnej oferty stolarki okiennej
na podstawie wiadomości klienta.

System analizuje:

- e-mail
- PDF
- zdjęcia
- OCR
- formularze
- API

Następnie:

- rozpoznaje potrzeby klienta
- dobiera produkty
- podejmuje decyzje handlowe
- waliduje ofertę
- wykonuje ofertę w WH
- uczy się z kolejnych przypadków

---

# High Level Architecture

```
                Customer Input
                       │
                       ▼
              Mail Understanding
                       │
                       ▼
           Requirement Extraction
                       │
                       ▼
             Knowledge Engine
                       │
                       ▼
             Decision Engine
                       │
                       ▼
           Offer Specification
                       │
                       ▼
             Offer Validation
                       │
                       ▼
             WH Runtime Adapter
                       │
                       ▼
             Vision Verification
                       │
                       ▼
               Learning Engine
```

---

# Layers

## Input Layer

Responsible for reading:

- Mail
- PDF
- OCR
- Images
- API

---

## Knowledge Layer

Contains:

- Profiles
- Hardware
- Glazing
- Colors
- Rules

---

## Decision Layer

Chooses:

- profile
- hardware
- glazing

---

## Runtime Layer

Executes operations inside WH.

Contains no business logic.

---

## Learning Layer

Learns from:

- previous offers
- corrections
- accepted quotations
- failures
