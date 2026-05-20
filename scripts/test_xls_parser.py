from app.parsers.xls_offer_parser import (
    parse_xls_offer
)


schema = parse_xls_offer(

    "research/xls/"
    "OFR-2044-.xls"
)


print(schema)