# Domain Model

## Customer

Represents company or private customer.

---

## CustomerRequest

Represents everything customer requested.

Contains:

- language
- products
- installation
- transport
- notes
- attachments

---

## ProductRequest

Represents requested product.

Examples:

- Window
- Balcony Door
- Entrance Door
- HS
- Roller Shutter
- Mosquito Net

---

## Profile

Represents profile system.

Examples:

- VEKA Softline 82 MD
- VEKA Softline 76 MD

---

## Hardware

Examples:

- MACO
- Winkhaus
- Siegenia

---

## Glazing

Examples:

- Double
- Triple

---

## Decision

Represents business decision.

Contains:

- profile
- hardware
- glazing
- confidence
- explanation

---

## OfferSpecification

Represents final offer before WH execution.

Contains:

- products
- transport
- installation
- notes
