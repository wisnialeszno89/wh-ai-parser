FILE = (
    "research/validation/"
    "validation.vrq"
)


with open(FILE, "rb") as f:

    data = f.read()


print(
    "\n========== RAW ==========\n"
)

print(
    data.decode(
        "utf-8",
        errors="ignore"
    )
)