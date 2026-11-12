"""Window-table aggregation and a small OOXML export for the Windows agent.

No spreadsheet application or third-party Python dependency is required at runtime.
The output is a snapshot report; area and quantity totals retain editable Excel formulas.
"""
from collections import Counter
from decimal import Decimal
from html import escape
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile
import json
import os
import unicodedata
import webbrowser

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
HEADERS = ['Lp.', 'Plik źródłowy', 'Pozycja źródłowa', 'Opis', 'Szerokość [mm]', 'Wysokość [mm]', 'Sztuki', 'Pow. 1 szt. [m²]', 'Pow. razem [m²]', 'Powtórzenie', 'Wystąpienia']


def q(name):
    return '{' + NS + '}' + name


def normalize_label(label):
    return ' '.join(unicodedata.normalize('NFKC', label).casefold().split())


def aggregate(sources):
    """Preserve order and quantities; repeats are candidates, not removals."""
    entries = []
    for source in sources:
        for index, row in enumerate(source['rows'], 1):
            area = Decimal(row['width_mm']) * Decimal(row['height_mm']) / Decimal(1000000)
            entries.append({**row, 'source': source['folder'] + '/' + source['file_name'], 'source_row': index,
                            'area_each': str(area), 'area_total': str(area * row['quantity'])})
    if not entries or len(entries) > 2500:
        raise ValueError('Raport wymaga 1–2500 pozycji.')
    key = lambda row: (normalize_label(row['label']), row['width_mm'], row['height_mm'])
    counts = Counter(key(row) for row in entries)
    groups = {value: 'D' + str(i + 1) for i, value in enumerate(value for value, count in counts.items() if count > 1)}
    for row in entries:
        row['duplicate'] = groups.get(key(row), '')
        row['occurrences'] = counts[key(row)]
    summary = {'files': len(sources), 'positions': len(entries), 'quantity': sum(row['quantity'] for row in entries),
               'area_m2': str(sum((Decimal(row['area_total']) for row in entries), Decimal(0))),
               'duplicate_rows': sum(bool(row['duplicate']) for row in entries), 'duplicate_groups': len(groups)}
    return entries, summary


def xml_bytes(element):
    return ET.tostring(element, encoding='utf-8', xml_declaration=True)


def cell(row, ref, value, style=0, formula=None):
    attrs = {'r': ref, 's': str(style)}
    if isinstance(value, str) and formula is None:
        attrs['t'] = 'inlineStr'
        element = ET.SubElement(row, q('c'), attrs)
        inline = ET.SubElement(element, q('is'))
        text = ET.SubElement(inline, q('t'), {'{http://www.w3.org/XML/1998/namespace}space': 'preserve'})
        text.text = value
    else:
        element = ET.SubElement(row, q('c'), attrs)
        if formula:
            ET.SubElement(element, q('f')).text = formula
        ET.SubElement(element, q('v')).text = str(value)
    return element


def worksheet(entries, summary):
    last = len(entries) + 7
    root = ET.Element(q('worksheet'))
    ET.SubElement(root, q('dimension'), {'ref': f'A1:K{last}'})
    view = ET.SubElement(ET.SubElement(root, q('sheetViews')), q('sheetView'), {'workbookViewId': '0', 'showGridLines': '0'})
    ET.SubElement(view, q('pane'), {'ySplit': '7', 'topLeftCell': 'A8', 'activePane': 'bottomLeft', 'state': 'frozen'})
    ET.SubElement(root, q('sheetFormatPr'), {'defaultRowHeight': '18'})
    cols = ET.SubElement(root, q('cols'))
    for index, width in enumerate([6, 48, 12, 40, 18, 18, 10, 20, 20, 16, 14], 1):
        ET.SubElement(cols, q('col'), {'min': str(index), 'max': str(index), 'width': str(width), 'customWidth': '1'})
    data = ET.SubElement(root, q('sheetData'))
    title = ET.SubElement(data, q('row'), {'r': '1', 'ht': '30', 'customHeight': '1'})
    cell(title, 'A1', 'NaviMind · zestawienie okien', 1)
    summary_row = ET.SubElement(data, q('row'), {'r': '2', 'ht': '26', 'customHeight': '1'})
    for ref, value in [('A2', 'Pliki'), ('D2', 'Pozycje'), ('G2', 'Sztuki'), ('J2', 'Pow. [m²]')]:
        cell(summary_row, ref, value, 3)
    cell(summary_row, 'B2', summary['files'], 3)
    cell(summary_row, 'E2', summary['positions'], 3)
    cell(summary_row, 'H2', summary['quantity'], 3, f'SUM(G8:G{last})')
    cell(summary_row, 'K2', Decimal(summary['area_m2']), 5, f'SUM(I8:I{last})')
    note = ET.SubElement(data, q('row'), {'r': '3', 'ht': '34', 'customHeight': '1'})
    cell(note, 'A3', 'Powtórzenia oznaczono, bez usuwania. Sumy obejmują wszystkie wiersze. Oznaczenia powtórzeń dotyczą chwili generowania.', 7)
    duplicates = ET.SubElement(data, q('row'), {'r': '4'})
    cell(duplicates, 'A4', 'Powtórzone wiersze', 3)
    cell(duplicates, 'E4', summary['duplicate_rows'], 3)
    cell(duplicates, 'G4', 'Grupy powtórzeń', 3)
    cell(duplicates, 'K4', summary['duplicate_groups'], 3)
    header = ET.SubElement(data, q('row'), {'r': '7', 'ht': '28', 'customHeight': '1'})
    for column, label in zip('ABCDEFGHIJK', HEADERS):
        cell(header, column + '7', label, 2)
    for index, entry in enumerate(entries, 8):
        row = ET.SubElement(data, q('row'), {'r': str(index)})
        style = 4 if entry['duplicate'] else 0
        values = [index - 7, entry['source'], entry['source_row'], entry['label'], entry['width_mm'], entry['height_mm'], entry['quantity']]
        for column, value in zip('ABCDEFG', values):
            cell(row, column + str(index), value, style)
        area_style = 6 if entry['duplicate'] else 5
        cell(row, f'H{index}', Decimal(entry['area_each']), area_style, f'E{index}*F{index}/1000000')
        cell(row, f'I{index}', Decimal(entry['area_total']), area_style, f'H{index}*G{index}')
        cell(row, f'J{index}', entry['duplicate'], style)
        cell(row, f'K{index}', entry['occurrences'], style)
    ET.SubElement(root, q('autoFilter'), {'ref': f'A7:K{last}'})
    merges = ET.SubElement(root, q('mergeCells'), {'count': '4'})
    ET.SubElement(merges, q('mergeCell'), {'ref': 'A1:K1'})
    ET.SubElement(merges, q('mergeCell'), {'ref': 'A3:K3'})
    ET.SubElement(merges, q('mergeCell'), {'ref': 'A4:D4'})
    ET.SubElement(merges, q('mergeCell'), {'ref': 'G4:J4'})
    ET.SubElement(root, q('pageMargins'), {'left': '0.25', 'right': '0.25', 'top': '0.5', 'bottom': '0.5', 'header': '0.2', 'footer': '0.2'})
    ET.SubElement(root, q('pageSetup'), {'orientation': 'landscape', 'paperSize': '9', 'fitToWidth': '1', 'fitToHeight': '0'})
    return xml_bytes(root)


STYLES = '''<?xml version="1.0" encoding="UTF-8"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="1"><numFmt numFmtId="164" formatCode="0.000"/></numFmts>
<fonts count="4"><font><sz val="11"/><name val="Calibri"/><color rgb="FF172033"/></font><font><b/><sz val="18"/><name val="Calibri"/><color rgb="FFFFFFFF"/></font><font><b/><sz val="10"/><name val="Calibri"/><color rgb="FFFFFFFF"/></font><font><b/><sz val="11"/><name val="Calibri"/><color rgb="FF172033"/></font></fonts>
<fills count="5"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF18324D"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFE9F1F8"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFFFE8BB"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="8">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
<xf numFmtId="0" fontId="2" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment wrapText="1" vertical="center"/></xf>
<xf numFmtId="0" fontId="3" fillId="3" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
<xf numFmtId="0" fontId="0" fillId="4" borderId="0" xfId="0" applyFill="1"/>
<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="164" fontId="0" fillId="4" borderId="0" xfId="0" applyNumberFormat="1" applyFill="1"/>
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="center"/></xf>
</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>'''


def write_xlsx(path, entries, summary):
    wb = ET.Element(q('workbook'), {'xmlns:r': REL})
    sheets = ET.SubElement(wb, q('sheets'))
    ET.SubElement(sheets, q('sheet'), {'name': 'Zestawienie', 'sheetId': '1', '{'+REL+'}id': 'rId1'})
    ET.SubElement(wb, q('calcPr'), {'calcId': '191029', 'fullCalcOnLoad': '1'})
    with ZipFile(path, 'x', compression=ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', '''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>''')
        archive.writestr('_rels/.rels', '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>''')
        archive.writestr('xl/workbook.xml', xml_bytes(wb))
        archive.writestr('xl/_rels/workbook.xml.rels', '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>''')
        archive.writestr('xl/styles.xml', STYLES)
        archive.writestr('xl/worksheets/sheet1.xml', worksheet(entries, summary))


def verify_xlsx(path, entries, summary):
    with ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('Uszkodzony plik arkusza.')
        sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        expected_rows = [1, 2, 3, 4, 7] + list(range(8, len(entries)+8))
        if [int(row.attrib['r']) for row in sheet.find(q('sheetData'))] != expected_rows:
            raise ValueError('Liczba wierszy arkusza różni się od raportu.')
        cells = {node.attrib['r']: node for node in sheet.iter(q('c'))}
        def value(ref):
            node = cells[ref]
            return node.findtext(q('is')+'/'+q('t')) if node.attrib.get('t') == 'inlineStr' else node.findtext(q('v'))
        if int(value('B2')) != summary['files'] or int(value('E2')) != len(entries) or int(value('H2')) != summary['quantity'] or Decimal(value('K2')) != Decimal(summary['area_m2']):
            raise ValueError('Podsumowanie arkusza nie zgadza się z odczytanymi danymi.')
        if int(value('E4')) != summary['duplicate_rows'] or int(value('K4')) != summary['duplicate_groups']:
            raise ValueError('Liczba powtórzeń nie zgadza się z raportem.')
        for index, entry in enumerate(entries, 8):
            expected = [index-7, entry['source'], entry['source_row'], entry['label'], entry['width_mm'], entry['height_mm'], entry['quantity'], entry['area_each'], entry['area_total'], entry['duplicate'], entry['occurrences']]
            for column, item in zip('ABCDEFGHIJK', expected):
                if str(value(column+str(index)) or '') != str(item):
                    raise ValueError('Wiersz arkusza nie zgadza się ze źródłem.')
            if cells[f'H{index}'].findtext(q('f')) != f'E{index}*F{index}/1000000' or cells[f'I{index}'].findtext(q('f')) != f'H{index}*G{index}':
                raise ValueError('Nieprawidłowa formuła powierzchni.')
        last = len(entries)+7
        if cells['H2'].findtext(q('f')) != f'SUM(G8:G{last})' or cells['K2'].findtext(q('f')) != f'SUM(I8:I{last})':
            raise ValueError('Nieprawidłowa formuła podsumowania.')
    return True


def write_preview(path, entries, summary):
    rows = []
    for index, entry in enumerate(entries, 1):
        values = [index, entry['source'], entry['source_row'], entry['label'], entry['width_mm'], entry['height_mm'], entry['quantity'], entry['area_each'], entry['area_total'], entry['duplicate'], entry['occurrences']]
        rows.append('<tr'+(' class="duplicate"' if entry['duplicate'] else '')+'>'+''.join('<td>'+escape(str(value))+'</td>' for value in values)+'</tr>')
    html = '<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NaviMind · zestawienie okien</title><style>body{font:15px system-ui;margin:30px;color:#172033;background:#f4f7fa}h1{color:#18324d}.stats{background:white;padding:20px;border-radius:12px;display:flex;gap:30px;flex-wrap:wrap}.table{overflow:auto;margin-top:24px}table{border-collapse:collapse;background:white;width:100%}th{background:#18324d;color:white;position:sticky;top:0}td,th{padding:10px;text-align:left;border-bottom:1px solid #ddd;white-space:nowrap}.duplicate{background:#ffe8bb}p{max-width:1000px;line-height:1.5}</style><h1>NaviMind · zestawienie okien</h1><div class="stats">'+''.join('<strong>'+escape(label)+': '+escape(str(value))+'</strong>' for label,value in [('Pliki',summary['files']),('Pozycje',summary['positions']),('Sztuki',summary['quantity']),('Powierzchnia [m²]',summary['area_m2']),('Wiersze z powtórzeniem',summary['duplicate_rows'])])+'</div><p>Powtórzenia oznaczono kolorem. Nie usunięto żadnych pozycji; sumy obejmują wszystkie źródła. Wariant oznacza zgodny opis (bez różnic wielkości liter i odstępów), szerokość i wysokość. Ilości mogą się różnić. Oznaczenia dotyczą chwili generowania raportu.</p><div class="table"><table><thead><tr>'+''.join('<th>'+escape(h)+'</th>' for h in HEADERS)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div></html>'
    with path.open('x', encoding='utf-8') as stream:
        stream.write(html)


def open_report(path, preview):
    try:
        if os.name == 'nt':
            os.startfile(str(path))
            return {'open_status': 'requested', 'opened_with': 'default_spreadsheet_application'}
    except OSError:
        pass
    try:
        if webbrowser.open(preview.resolve().as_uri()):
            return {'open_status': 'requested', 'opened_with': 'browser_preview'}
    except Exception:
        pass
    return {'open_status': 'unavailable', 'opened_with': None}
