from datetime import datetime
from schema_drawer import draw_schema


def generate_report(data):

    lines = []

    lines.append("=" * 60)
    lines.append("RAPORT KONSTRUKCJI OKIENNYCH")
    lines.append("=" * 60)
    lines.append(
        f"Wygenerowano: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    lines.append("")

    for c in data:

        lines.append("-" * 60)
        lines.append(
            f"KONSTRUKCJA {c.get('construction_id')}"
        )
        lines.append("-" * 60)

        lines.append(
            f"Schemat: {c.get('schema')}"
        )
        lines.append("")
        lines.append(draw_schema(c))
        lines.append("")

        lines.append(
            f"Wymiary: {c.get('total_width_mm')} x {c.get('height_mm')} mm"
        )

        lines.append(
            f"Materiał: {c.get('material')}"
        )

        lines.append(
            f"Ilość: {c.get('quantity')}"
        )

        lines.append(
            f"Łącznik: {'TAK' if c.get('connector') else 'NIE'}"
        )

        lines.append(
            f"Słupek ruchomy: {'TAK' if c.get('movable_mullion') else 'NIE'}"
        )

        terrace = c.get('terrace_system')

        if terrace:
            lines.append(
                f"System tarasowy: {terrace}"
            )

        lines.append("")
        lines.append("SEGMENTY:")

        for idx, s in enumerate(c.get('segments', []), start=1):

            direction = s.get('opening_direction')

            dir_text = direction if direction else "-"

            lines.append(
                f"  {idx}. {s.get('type')} | "
                f"{s.get('width_mm')} mm | "
                f"otwieranie: {dir_text}"
            )

        notes = c.get('notes')

        if notes:
            lines.append("")
            lines.append(f"Uwagi: {notes}")

        lines.append("")
    print("\n[+] Zapisano raport.txt")