from typing import List
from math import ceil, floor


arr1 = [100, 105, 110, 115, 120, 125, 130, 135]  # mean: 8, 9
arr2 = [104, 108, 112, 116, 118, 120, 124, 128]  # mean: 88

print(
    f"{arr1=}\n{arr2=}\n1+2={sorted(arr1+arr2)}\nmedian ({len(arr1+arr2)/2}) should be {sorted(arr1+arr2)[floor(len(arr1+arr2)/2)]}"
)


def split_on_median(arr: List[int]) -> List[int]:
    # [9, 11, 34, 67, 89, 99] -> 3
    l = int(len(arr) / 2)
    if len(arr) % 2 == 0:
        # print(f"{l=} is double")
        return (arr[l - 1] + arr[l]) / 2, arr[:l], arr[l:]

    # print(f"{l=} is simple")
    return arr[l], arr[: l + 1], arr[l:]


for i in range(10):
    print()
    m1, a1, b1 = split_on_median(arr1)
    print(f"{arr1=}")
    print(f"{m1=}")
    print(f"{a1=} {b1=}")

    m2, a2, b2 = split_on_median(arr2)
    print(f"{arr2=}")
    print(f"{m2=}")
    print(f"{a2=} {b2=}")

    if m1 < m2:
        arr1 = b1
        arr2 = a2

    if m1 > m2:
        arr1 = a1
        arr2 = b2

    if m1 == m2:
        print(f"m1 == m2 => {m1}")

    if len(arr1) == 1 and len(arr2) == 1:
        print("\nllego a la weaita")
        print(f"{arr1=} {arr2=}")
        if len(arr1) + len(arr2) % 2 == 0:
            print(f"la wea es {(arr1[0]+arr2[0])/2}")
        else:
            print(f"la wea es {arr1[0]}")
        break
