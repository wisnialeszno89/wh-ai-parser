import pandas as pd


PATH = (
    "research/xls/"
    "OFR-2044-.xls"
)


xls = pd.ExcelFile(PATH)


print(
    "\n========== SHEETS ==========\n"
)

print(
    xls.sheet_names
)


for sheet in xls.sheet_names:

    print(
        f"\n========== {sheet} ==========\n"
    )

    df = pd.read_excel(

        PATH,

        sheet_name=sheet,

        header=None
    )

    values = (
        df.astype(str)
        .values
    )

    for row in values:

        line = " | ".join(
            map(str, row)
        )

        if (
            "nan" not in line
            and line.strip()
        ):

            print(line)