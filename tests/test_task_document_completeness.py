"""A long enquiry must never turn into a seemingly complete partial order."""
from pathlib import Path

import pytest

from app.agent.intake.task_document import read_task_document


def test_trailing_position_cannot_be_silently_dropped(tmp_path):
    source = tmp_path / 'enquiry.txt'
    source.write_text('Fenster 1 Stk. 1200x1400 mm\n' * 500 +
                      'Haustür 2 Stk. 990x2120 mm', encoding='utf-8')
    with pytest.raises(ValueError, match='text_too_large_split_request'):
        read_task_document(source)


def test_exact_limit_preserves_every_character_and_bom_is_not_product_text(tmp_path):
    source = tmp_path / 'enquiry.md'
    text = 'Okno 1 szt. 1230×1478 mm'
    source.write_text(text, encoding='utf-8-sig')
    assert read_task_document(source, max_chars=len(text)) == text
    with pytest.raises(ValueError, match='text_too_large'):
        read_task_document(source, max_chars=len(text)-1)


@pytest.mark.parametrize('limit', [0, -1, True, 1.5])
def test_invalid_character_limits_are_rejected(limit):
    with pytest.raises(ValueError, match='invalid_char_limit'):
        read_task_document(Path('unused.txt'), max_chars=limit)


def test_pdf_text_limit_cannot_hide_the_last_position(tmp_path):
    fitz = pytest.importorskip('fitz')
    source = tmp_path / 'enquiry.pdf'
    with fitz.open() as document:
        document.new_page().insert_text((40, 50), 'Fenster 1 Stk. 1200x1400 mm')
        document.new_page().insert_text((40, 50), 'Haustuer 2 Stk. 990x2120 mm')
        document.save(source)
    with pytest.raises(ValueError, match='text_too_large'):
        read_task_document(source, max_chars=30)
