from app.wh.geometry_patch import (
    patch_geometry
)


result = patch_geometry(

    "research/payloads/"
    "fix_ru_fix/"
    "OFR-2044-TT.OFR",

    "research/payloads/"
    "fix_ru_fix/"
    "OFR-2053-.OFR",

    "research/payloads/"
    "fix_ru_fix/"
    "OFR-2055-.OFR"
)


with open(

    "outputs/ofr/"
    "synthetic_2500x1500.ofr",

    "wb"

) as f:

    f.write(result)


print(
    "\n[+] SYNTHETIC OFR SAVED"
)