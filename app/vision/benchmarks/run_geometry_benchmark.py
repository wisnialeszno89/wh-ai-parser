from pathlib import Path

from app.vision.builders.build_construction import (
    build_construction
)


BASE_DIR = Path(
    "training_data/geometry"
)

total = 0
correct = 0

print("\nGEOMETRY BENCHMARK\n")

for category_dir in BASE_DIR.iterdir():

    if not category_dir.is_dir():
        continue

    expected = (
        category_dir.name
        .split("_")
    )

    print(f"\n[{category_dir.name}]")

    for image_path in category_dir.iterdir():

        if not image_path.is_file():
            continue

        total += 1

        try:

            result = build_construction(
                str(image_path)
            )

            ok = result == expected

            if ok:
                correct += 1

            status = (
                "OK"
                if ok
                else "FAIL"
            )

            print(
                f"{status} | "
                f"{image_path.name}"
            )

            print(
                f"expected={expected}"
            )

            print(
                f"result={result}"
            )

            print("")

        except Exception as e:

            print(
                f"ERROR | "
                f"{image_path.name}"
            )

            print(str(e))
            print("")

accuracy = (
    correct / total * 100
    if total > 0
    else 0
)

print("\n====================")
print(f"TOTAL: {total}")
print(f"CORRECT: {correct}")
print(
    f"ACCURACY: "
    f"{accuracy:.2f}%"
)
print("====================")