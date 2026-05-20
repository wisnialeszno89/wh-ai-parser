import hashlib


A = (
    "research/payloads/fix_ru_fix/"
    "OFR-2044-TT.OFR"
)

B = (
    "outputs/ofr/"
    "rebuilt.ofr"
)


def sha256(path):

    with open(path, "rb") as f:

        return hashlib.sha256(
            f.read()
        ).hexdigest()


print(
    "\nORIGINAL:\n"
)

print(
    sha256(A)
)


print(
    "\nREBUILT:\n"
)

print(
    sha256(B)
)