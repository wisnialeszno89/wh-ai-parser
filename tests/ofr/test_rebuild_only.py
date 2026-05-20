from pathlib import Path

from app.wh.runtime_engine import (
    load_ofr,
    save_ofr
)


source = (
    "app/wh/base_templates/"
    "double_sash_movable_mullion.ofr"
)

runtime = load_ofr(
    source
)

output = Path(
    "outputs/ofr/rebuild_only.ofr"
)

save_ofr(

    header=runtime["header"],

    payload=runtime["payload"],

    output_path=output
)

print()
print(output)