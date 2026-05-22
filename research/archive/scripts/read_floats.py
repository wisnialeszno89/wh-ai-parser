import struct


path = (
    "research/dumps/"
    "region_3113_4079.bin"
)


with open(path, "rb") as f:

    data = f.read()


print()
print("========== FLOATS ==========")
print()


for i in range(

    0,

    len(data) - 4,

    4
):

    chunk = data[i:i+4]

    try:

        value = struct.unpack(
            "<f",
            chunk
        )[0]

        if (
            abs(value) > 0.01
            and abs(value) < 100000
        ):

            print(
                f"{i:04d} | {value}"
            )

    except:

        pass