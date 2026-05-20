import sys


def load_file(path):

    with open(path, "rb") as f:

        return f.read()


def main():

    file_a = sys.argv[1]

    file_b = sys.argv[2]


    a = load_file(file_a)

    b = load_file(file_b)


    print()
    print("========== DIFF REGIONS ==========")
    print()


    in_diff = False

    start = 0


    for i in range(

        min(len(a), len(b))
    ):

        if a[i] != b[i]:

            if not in_diff:

                start = i

                in_diff = True

        else:

            if in_diff:

                end = i - 1

                print(
                    f"{start} - {end} "
                    f"(size={end-start+1})"
                )

                in_diff = False


    if in_diff:

        end = min(
            len(a),
            len(b)
        ) - 1

        print(
            f"{start} - {end} "
            f"(size={end-start+1})"
        )


if __name__ == "__main__":

    main()