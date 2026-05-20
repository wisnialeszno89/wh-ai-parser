from app.catalog.load_constructions import load_constructions


items = load_constructions()

for item in items:

    print(item["id"])
    print(item["schema"])
    print("---")