from app.ui.dataset.find_similar_regions import (
    find_similar_regions
)


IMAGE = "samples/wh_screen.png"


find_similar_regions(

    IMAGE,

    "templates/insert_vertical_tool.png",

    "insert_vertical"
)


find_similar_regions(

    IMAGE,

    "templates/insert_slash_left_tool.png",

    "insert_slash_left"
)


find_similar_regions(

    IMAGE,

    "templates/slope_tool.png",

    "slope"
)