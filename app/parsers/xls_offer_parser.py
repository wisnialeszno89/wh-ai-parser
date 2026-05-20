import pandas as pd

from app.parsers.text_offer_parser import (
    parse_offer_text
)


def parse_xls_offer(path):

    xls = pd.ExcelFile(path)

    text = []


    for sheet in xls.sheet_names:

        df = pd.read_excel(

            path,

            sheet_name=sheet,

            header=None
        )

        values = df.astype(str).values


        for row in values:

            for cell in row:

                if cell != "nan":

                    text.append(str(cell))


    combined = "\n".join(text)

    return parse_offer_text(
        combined
    )