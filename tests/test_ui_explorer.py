from pprint import pprint

from app.ui.runtime.ui_explorer import (
    ui_explorer
)

controls = ui_explorer(
    "samples/ui/wh_screen_06.png"
)

print()
pprint(
    controls[:30]
)
print()