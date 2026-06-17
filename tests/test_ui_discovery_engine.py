from pprint import pprint

from app.ui.runtime.ui_discovery_engine import (
    ui_discovery_engine
)


points = ui_discovery_engine(
    "samples/ui/wh_screen_06.png"
)

print()

pprint(
    points[:50]
)

print()