# https://raw.githubusercontent.com/lincolnloop/python-qrcode/b80fea6ee7e75f3024b9ed7adf891a143e0b14e3/qrcode/main.py
# The code was copied in such weird way since the original project requires Pillow

import math
import re
import sys
from bisect import bisect_left
from typing import Dict, List, NamedTuple, Optional, cast

ERROR_CORRECT_L = 1
ERROR_CORRECT_M = 0
ERROR_CORRECT_Q = 3
ERROR_CORRECT_H = 2

EXP_TABLE = list(range(256))

LOG_TABLE = list(range(256))

for i in range(8):
    EXP_TABLE[i] = 1 << i

for i in range(8, 256):
    EXP_TABLE[i] = (
        EXP_TABLE[i - 4] ^ EXP_TABLE[i - 5] ^ EXP_TABLE[i - 6] ^ EXP_TABLE[i - 8]
    )

for i in range(255):
    LOG_TABLE[EXP_TABLE[i]] = i


def rs_blocks(version, error_correction):
    if error_correction not in RS_BLOCK_OFFSET:  # pragma: no cover
        raise Exception(
            f"bad rs block @ version: {version} / error_correction: {error_correction}"
        )
    offset = RS_BLOCK_OFFSET[error_correction]
    rs_block = RS_BLOCK_TABLE[(version - 1) * 4 + offset]

    blocks = []

    for i in range(0, len(rs_block), 3):
        count, total_count, data_count = rs_block[i : i + 3]
        blocks.extend(RSBlock(total_count, data_count) for _ in range(count))
    return blocks


RS_BLOCK_OFFSET = {
    ERROR_CORRECT_L: 0,
    ERROR_CORRECT_M: 1,
    ERROR_CORRECT_Q: 2,
    ERROR_CORRECT_H: 3,
}

RS_BLOCK_TABLE = (
    # L
    # M
    # Q
    # H
    # 1
    (1, 26, 19),
    (1, 26, 16),
    (1, 26, 13),
    (1, 26, 9),
    # 2
    (1, 44, 34),
    (1, 44, 28),
    (1, 44, 22),
    (1, 44, 16),
    # 3
    (1, 70, 55),
    (1, 70, 44),
    (2, 35, 17),
    (2, 35, 13),
    # 4
    (1, 100, 80),
    (2, 50, 32),
    (2, 50, 24),
    (4, 25, 9),
    # 5
    (1, 134, 108),
    (2, 67, 43),
    (2, 33, 15, 2, 34, 16),
    (2, 33, 11, 2, 34, 12),
    # 6
    (2, 86, 68),
    (4, 43, 27),
    (4, 43, 19),
    (4, 43, 15),
    # 7
    (2, 98, 78),
    (4, 49, 31),
    (2, 32, 14, 4, 33, 15),
    (4, 39, 13, 1, 40, 14),
    # 8
    (2, 121, 97),
    (2, 60, 38, 2, 61, 39),
    (4, 40, 18, 2, 41, 19),
    (4, 40, 14, 2, 41, 15),
    # 9
    (2, 146, 116),
    (3, 58, 36, 2, 59, 37),
    (4, 36, 16, 4, 37, 17),
    (4, 36, 12, 4, 37, 13),
    # 10
    (2, 86, 68, 2, 87, 69),
    (4, 69, 43, 1, 70, 44),
    (6, 43, 19, 2, 44, 20),
    (6, 43, 15, 2, 44, 16),
    # 11
    (4, 101, 81),
    (1, 80, 50, 4, 81, 51),
    (4, 50, 22, 4, 51, 23),
    (3, 36, 12, 8, 37, 13),
    # 12
    (2, 116, 92, 2, 117, 93),
    (6, 58, 36, 2, 59, 37),
    (4, 46, 20, 6, 47, 21),
    (7, 42, 14, 4, 43, 15),
    # 13
    (4, 133, 107),
    (8, 59, 37, 1, 60, 38),
    (8, 44, 20, 4, 45, 21),
    (12, 33, 11, 4, 34, 12),
    # 14
    (3, 145, 115, 1, 146, 116),
    (4, 64, 40, 5, 65, 41),
    (11, 36, 16, 5, 37, 17),
    (11, 36, 12, 5, 37, 13),
    # 15
    (5, 109, 87, 1, 110, 88),
    (5, 65, 41, 5, 66, 42),
    (5, 54, 24, 7, 55, 25),
    (11, 36, 12, 7, 37, 13),
    # 16
    (5, 122, 98, 1, 123, 99),
    (7, 73, 45, 3, 74, 46),
    (15, 43, 19, 2, 44, 20),
    (3, 45, 15, 13, 46, 16),
    # 17
    (1, 135, 107, 5, 136, 108),
    (10, 74, 46, 1, 75, 47),
    (1, 50, 22, 15, 51, 23),
    (2, 42, 14, 17, 43, 15),
    # 18
    (5, 150, 120, 1, 151, 121),
    (9, 69, 43, 4, 70, 44),
    (17, 50, 22, 1, 51, 23),
    (2, 42, 14, 19, 43, 15),
    # 19
    (3, 141, 113, 4, 142, 114),
    (3, 70, 44, 11, 71, 45),
    (17, 47, 21, 4, 48, 22),
    (9, 39, 13, 16, 40, 14),
    # 20
    (3, 135, 107, 5, 136, 108),
    (3, 67, 41, 13, 68, 42),
    (15, 54, 24, 5, 55, 25),
    (15, 43, 15, 10, 44, 16),
    # 21
    (4, 144, 116, 4, 145, 117),
    (17, 68, 42),
    (17, 50, 22, 6, 51, 23),
    (19, 46, 16, 6, 47, 17),
    # 22
    (2, 139, 111, 7, 140, 112),
    (17, 74, 46),
    (7, 54, 24, 16, 55, 25),
    (34, 37, 13),
    # 23
    (4, 151, 121, 5, 152, 122),
    (4, 75, 47, 14, 76, 48),
    (11, 54, 24, 14, 55, 25),
    (16, 45, 15, 14, 46, 16),
    # 24
    (6, 147, 117, 4, 148, 118),
    (6, 73, 45, 14, 74, 46),
    (11, 54, 24, 16, 55, 25),
    (30, 46, 16, 2, 47, 17),
    # 25
    (8, 132, 106, 4, 133, 107),
    (8, 75, 47, 13, 76, 48),
    (7, 54, 24, 22, 55, 25),
    (22, 45, 15, 13, 46, 16),
    # 26
    (10, 142, 114, 2, 143, 115),
    (19, 74, 46, 4, 75, 47),
    (28, 50, 22, 6, 51, 23),
    (33, 46, 16, 4, 47, 17),
    # 27
    (8, 152, 122, 4, 153, 123),
    (22, 73, 45, 3, 74, 46),
    (8, 53, 23, 26, 54, 24),
    (12, 45, 15, 28, 46, 16),
    # 28
    (3, 147, 117, 10, 148, 118),
    (3, 73, 45, 23, 74, 46),
    (4, 54, 24, 31, 55, 25),
    (11, 45, 15, 31, 46, 16),
    # 29
    (7, 146, 116, 7, 147, 117),
    (21, 73, 45, 7, 74, 46),
    (1, 53, 23, 37, 54, 24),
    (19, 45, 15, 26, 46, 16),
    # 30
    (5, 145, 115, 10, 146, 116),
    (19, 75, 47, 10, 76, 48),
    (15, 54, 24, 25, 55, 25),
    (23, 45, 15, 25, 46, 16),
    # 31
    (13, 145, 115, 3, 146, 116),
    (2, 74, 46, 29, 75, 47),
    (42, 54, 24, 1, 55, 25),
    (23, 45, 15, 28, 46, 16),
    # 32
    (17, 145, 115),
    (10, 74, 46, 23, 75, 47),
    (10, 54, 24, 35, 55, 25),
    (19, 45, 15, 35, 46, 16),
    # 33
    (17, 145, 115, 1, 146, 116),
    (14, 74, 46, 21, 75, 47),
    (29, 54, 24, 19, 55, 25),
    (11, 45, 15, 46, 46, 16),
    # 34
    (13, 145, 115, 6, 146, 116),
    (14, 74, 46, 23, 75, 47),
    (44, 54, 24, 7, 55, 25),
    (59, 46, 16, 1, 47, 17),
    # 35
    (12, 151, 121, 7, 152, 122),
    (12, 75, 47, 26, 76, 48),
    (39, 54, 24, 14, 55, 25),
    (22, 45, 15, 41, 46, 16),
    # 36
    (6, 151, 121, 14, 152, 122),
    (6, 75, 47, 34, 76, 48),
    (46, 54, 24, 10, 55, 25),
    (2, 45, 15, 64, 46, 16),
    # 37
    (17, 152, 122, 4, 153, 123),
    (29, 74, 46, 14, 75, 47),
    (49, 54, 24, 10, 55, 25),
    (24, 45, 15, 46, 46, 16),
    # 38
    (4, 152, 122, 18, 153, 123),
    (13, 74, 46, 32, 75, 47),
    (48, 54, 24, 14, 55, 25),
    (42, 45, 15, 32, 46, 16),
    # 39
    (20, 147, 117, 4, 148, 118),
    (40, 75, 47, 7, 76, 48),
    (43, 54, 24, 22, 55, 25),
    (10, 45, 15, 67, 46, 16),
    # 40
    (19, 148, 118, 6, 149, 119),
    (18, 75, 47, 31, 76, 48),
    (34, 54, 24, 34, 55, 25),
    (20, 45, 15, 61, 46, 16),
)


def glog(n):
    if n < 1:  # pragma: no cover
        raise ValueError(f"glog({n})")
    return LOG_TABLE[n]


def gexp(n):
    return EXP_TABLE[n % 255]


class Polynomial:
    def __init__(self, num, shift):
        if not num:  # pragma: no cover
            raise Exception(f"{len(num)}/{shift}")

        offset = 0
        for offset in range(len(num)):
            if num[offset] != 0:
                break

        self.num = num[offset:] + [0] * shift

    def __getitem__(self, index):
        return self.num[index]

    def __iter__(self):
        return iter(self.num)

    def __len__(self):
        return len(self.num)

    def __mul__(self, other):
        num = [0] * (len(self) + len(other) - 1)

        for i, item in enumerate(self):
            for j, other_item in enumerate(other):
                num[i + j] ^= gexp(glog(item) + glog(other_item))

        return Polynomial(num, 0)

    def __mod__(self, other):
        difference = len(self) - len(other)
        if difference < 0:
            return self

        ratio = glog(self[0]) - glog(other[0])

        num = [
            item ^ gexp(glog(other_item) + ratio)
            for item, other_item in zip(self, other)
        ]
        if difference:
            num.extend(self[-difference:])

        # recursive call
        return Polynomial(num, 0) % other


class RSBlock(NamedTuple):
    total_count: int
    data_count: int


rsPoly_LUT = {
    7: [1, 127, 122, 154, 164, 11, 68, 117],
    10: [1, 216, 194, 159, 111, 199, 94, 95, 113, 157, 193],
    13: [1, 137, 73, 227, 17, 177, 17, 52, 13, 46, 43, 83, 132, 120],
    15: [1, 29, 196, 111, 163, 112, 74, 10, 105, 105, 139, 132, 151, 32, 134, 26],
    16: [1, 59, 13, 104, 189, 68, 209, 30, 8, 163, 65, 41, 229, 98, 50, 36, 59],
    17: [1, 119, 66, 83, 120, 119, 22, 197, 83, 249, 41, 143, 134, 85, 53, 125, 99, 79],
    18: [
        1,
        239,
        251,
        183,
        113,
        149,
        175,
        199,
        215,
        240,
        220,
        73,
        82,
        173,
        75,
        32,
        67,
        217,
        146,
    ],
    20: [
        1,
        152,
        185,
        240,
        5,
        111,
        99,
        6,
        220,
        112,
        150,
        69,
        36,
        187,
        22,
        228,
        198,
        121,
        121,
        165,
        174,
    ],
    22: [
        1,
        89,
        179,
        131,
        176,
        182,
        244,
        19,
        189,
        69,
        40,
        28,
        137,
        29,
        123,
        67,
        253,
        86,
        218,
        230,
        26,
        145,
        245,
    ],
    24: [
        1,
        122,
        118,
        169,
        70,
        178,
        237,
        216,
        102,
        115,
        150,
        229,
        73,
        130,
        72,
        61,
        43,
        206,
        1,
        237,
        247,
        127,
        217,
        144,
        117,
    ],
    26: [
        1,
        246,
        51,
        183,
        4,
        136,
        98,
        199,
        152,
        77,
        56,
        206,
        24,
        145,
        40,
        209,
        117,
        233,
        42,
        135,
        68,
        70,
        144,
        146,
        77,
        43,
        94,
    ],
    28: [
        1,
        252,
        9,
        28,
        13,
        18,
        251,
        208,
        150,
        103,
        174,
        100,
        41,
        167,
        12,
        247,
        56,
        117,
        119,
        233,
        127,
        181,
        100,
        121,
        147,
        176,
        74,
        58,
        197,
    ],
    30: [
        1,
        212,
        246,
        77,
        73,
        195,
        192,
        75,
        98,
        5,
        70,
        103,
        177,
        22,
        217,
        138,
        51,
        181,
        246,
        72,
        25,
        18,
        46,
        228,
        74,
        216,
        195,
        11,
        106,
        130,
        150,
    ],
}


# QR encoding modes.
MODE_NUMBER = 1 << 0
MODE_ALPHA_NUM = 1 << 1
MODE_8BIT_BYTE = 1 << 2
MODE_KANJI = 1 << 3

# Encoding mode sizes.
MODE_SIZE_SMALL = {
    MODE_NUMBER: 10,
    MODE_ALPHA_NUM: 9,
    MODE_8BIT_BYTE: 8,
    MODE_KANJI: 8,
}
MODE_SIZE_MEDIUM = {
    MODE_NUMBER: 12,
    MODE_ALPHA_NUM: 11,
    MODE_8BIT_BYTE: 16,
    MODE_KANJI: 10,
}
MODE_SIZE_LARGE = {
    MODE_NUMBER: 14,
    MODE_ALPHA_NUM: 13,
    MODE_8BIT_BYTE: 16,
    MODE_KANJI: 12,
}

ALPHA_NUM = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"
RE_ALPHA_NUM = re.compile(b"^[" + re.escape(ALPHA_NUM) + rb"]*\Z")

# The number of bits for numeric delimited data lengths.
NUMBER_LENGTH = {3: 10, 2: 7, 1: 4}

PATTERN_POSITION_TABLE = [
    [],
    [6, 18],
    [6, 22],
    [6, 26],
    [6, 30],
    [6, 34],
    [6, 22, 38],
    [6, 24, 42],
    [6, 26, 46],
    [6, 28, 50],
    [6, 30, 54],
    [6, 32, 58],
    [6, 34, 62],
    [6, 26, 46, 66],
    [6, 26, 48, 70],
    [6, 26, 50, 74],
    [6, 30, 54, 78],
    [6, 30, 56, 82],
    [6, 30, 58, 86],
    [6, 34, 62, 90],
    [6, 28, 50, 72, 94],
    [6, 26, 50, 74, 98],
    [6, 30, 54, 78, 102],
    [6, 28, 54, 80, 106],
    [6, 32, 58, 84, 110],
    [6, 30, 58, 86, 114],
    [6, 34, 62, 90, 118],
    [6, 26, 50, 74, 98, 122],
    [6, 30, 54, 78, 102, 126],
    [6, 26, 52, 78, 104, 130],
    [6, 30, 56, 82, 108, 134],
    [6, 34, 60, 86, 112, 138],
    [6, 30, 58, 86, 114, 142],
    [6, 34, 62, 90, 118, 146],
    [6, 30, 54, 78, 102, 126, 150],
    [6, 24, 50, 76, 102, 128, 154],
    [6, 28, 54, 80, 106, 132, 158],
    [6, 32, 58, 84, 110, 136, 162],
    [6, 26, 54, 82, 110, 138, 166],
    [6, 30, 58, 86, 114, 142, 170],
]

G15 = (1 << 10) | (1 << 8) | (1 << 5) | (1 << 4) | (1 << 2) | (1 << 1) | (1 << 0)
G18 = (
    (1 << 12)
    | (1 << 11)
    | (1 << 10)
    | (1 << 9)
    | (1 << 8)
    | (1 << 5)
    | (1 << 2)
    | (1 << 0)
)
G15_MASK = (1 << 14) | (1 << 12) | (1 << 10) | (1 << 4) | (1 << 1)

PAD0 = 0xEC
PAD1 = 0x11


# Precompute bit count limits, indexed by error correction level and code size
def _data_count(block):
    return block.data_count


BIT_LIMIT_TABLE = [
    [0]
    + [
        8 * sum(map(_data_count, rs_blocks(version, error_correction)))
        for version in range(1, 41)
    ]
    for error_correction in range(4)
]


def BCH_type_info(data):
    d = data << 10
    while BCH_digit(d) - BCH_digit(G15) >= 0:
        d ^= G15 << (BCH_digit(d) - BCH_digit(G15))

    return ((data << 10) | d) ^ G15_MASK


def BCH_type_number(data):
    d = data << 12
    while BCH_digit(d) - BCH_digit(G18) >= 0:
        d ^= G18 << (BCH_digit(d) - BCH_digit(G18))
    return (data << 12) | d


def BCH_digit(data):
    digit = 0
    while data != 0:
        digit += 1
        data >>= 1
    return digit


def pattern_position(version):
    return PATTERN_POSITION_TABLE[version - 1]


def mask_func(pattern):
    """
    Return the mask function for the given mask pattern.
    """
    if pattern == 0:  # 000
        return lambda i, j: (i + j) % 2 == 0
    if pattern == 1:  # 001
        return lambda i, j: i % 2 == 0
    if pattern == 2:  # 010
        return lambda i, j: j % 3 == 0
    if pattern == 3:  # 011
        return lambda i, j: (i + j) % 3 == 0
    if pattern == 4:  # 100
        return lambda i, j: (math.floor(i / 2) + math.floor(j / 3)) % 2 == 0
    if pattern == 5:  # 101
        return lambda i, j: (i * j) % 2 + (i * j) % 3 == 0
    if pattern == 6:  # 110
        return lambda i, j: ((i * j) % 2 + (i * j) % 3) % 2 == 0
    if pattern == 7:  # 111
        return lambda i, j: ((i * j) % 3 + (i + j) % 2) % 2 == 0
    raise TypeError(f"Bad mask pattern: {pattern}")


def mode_sizes_for_version(version):
    if version < 10:
        return MODE_SIZE_SMALL
    elif version < 27:
        return MODE_SIZE_MEDIUM
    else:
        return MODE_SIZE_LARGE


def length_in_bits(mode, version):
    if mode not in (MODE_NUMBER, MODE_ALPHA_NUM, MODE_8BIT_BYTE, MODE_KANJI):
        raise TypeError(f"Invalid mode ({mode})")  # pragma: no cover

    check_version(version)

    return mode_sizes_for_version(version)[mode]


def check_version(version):
    if version < 1 or version > 40:
        raise ValueError(f"Invalid version (was {version}, expected 1 to 40)")


def lost_point(modules):
    modules_count = len(modules)

    lost_point_ = 0

    lost_point_ = _lost_point_level1(modules, modules_count)
    lost_point_ += _lost_point_level2(modules, modules_count)
    lost_point_ += _lost_point_level3(modules, modules_count)
    lost_point_ += _lost_point_level4(modules, modules_count)

    return lost_point_


def _lost_point_level1(modules, modules_count):
    lost_point = 0

    modules_range = range(modules_count)
    container = [0] * (modules_count + 1)

    for row in modules_range:
        this_row = modules[row]
        previous_color = this_row[0]
        length = 0
        for col in modules_range:
            if this_row[col] == previous_color:
                length += 1
            else:
                if length >= 5:
                    container[length] += 1
                length = 1
                previous_color = this_row[col]
        if length >= 5:
            container[length] += 1

    for col in modules_range:
        previous_color = modules[0][col]
        length = 0
        for row in modules_range:
            if modules[row][col] == previous_color:
                length += 1
            else:
                if length >= 5:
                    container[length] += 1
                length = 1
                previous_color = modules[row][col]
        if length >= 5:
            container[length] += 1

    lost_point += sum(
        container[each_length] * (each_length - 2)
        for each_length in range(5, modules_count + 1)
    )

    return lost_point


def _lost_point_level2(modules, modules_count):
    lost_point = 0

    modules_range = range(modules_count - 1)
    for row in modules_range:
        this_row = modules[row]
        next_row = modules[row + 1]
        # use iter() and next() to skip next four-block. e.g.
        # d a f   if top-right a != b bottom-right,
        # c b e   then both abcd and abef won't lost any point.
        modules_range_iter = iter(modules_range)
        for col in modules_range_iter:
            top_right = this_row[col + 1]
            if top_right != next_row[col + 1]:
                # reduce 33.3% of runtime via next().
                # None: raise nothing if there is no next item.
                next(modules_range_iter, None)
            elif top_right != this_row[col] or top_right != next_row[col]:
                continue
            else:
                lost_point += 3

    return lost_point


def _lost_point_level3(modules, modules_count):
    # 1 : 1 : 3 : 1 : 1 ratio (dark:light:dark:light:dark) pattern in
    # row/column, preceded or followed by light area 4 modules wide. From ISOIEC.
    # pattern1:     10111010000
    # pattern2: 00001011101
    modules_range = range(modules_count)
    modules_range_short = range(modules_count - 10)
    lost_point = 0

    for row in modules_range:
        this_row = modules[row]
        modules_range_short_iter = iter(modules_range_short)
        col = 0
        for col in modules_range_short_iter:
            if (
                not this_row[col + 1]
                and this_row[col + 4]
                and not this_row[col + 5]
                and this_row[col + 6]
                and not this_row[col + 9]
                and (
                    this_row[col + 0]
                    and this_row[col + 2]
                    and this_row[col + 3]
                    and not this_row[col + 7]
                    and not this_row[col + 8]
                    and not this_row[col + 10]
                    or not this_row[col + 0]
                    and not this_row[col + 2]
                    and not this_row[col + 3]
                    and this_row[col + 7]
                    and this_row[col + 8]
                    and this_row[col + 10]
                )
            ):
                lost_point += 40
            # horspool algorithm.
            # if this_row[col + 10]:
            #   pattern1 shift 4, pattern2 shift 2. So min=2.
            # else:
            #   pattern1 shift 1, pattern2 shift 1. So min=1.
            if this_row[col + 10]:
                next(modules_range_short_iter, None)

    for col in modules_range:
        modules_range_short_iter = iter(modules_range_short)
        row = 0
        for row in modules_range_short_iter:
            if (
                not modules[row + 1][col]
                and modules[row + 4][col]
                and not modules[row + 5][col]
                and modules[row + 6][col]
                and not modules[row + 9][col]
                and (
                    modules[row + 0][col]
                    and modules[row + 2][col]
                    and modules[row + 3][col]
                    and not modules[row + 7][col]
                    and not modules[row + 8][col]
                    and not modules[row + 10][col]
                    or not modules[row + 0][col]
                    and not modules[row + 2][col]
                    and not modules[row + 3][col]
                    and modules[row + 7][col]
                    and modules[row + 8][col]
                    and modules[row + 10][col]
                )
            ):
                lost_point += 40
            if modules[row + 10][col]:
                next(modules_range_short_iter, None)

    return lost_point


def _lost_point_level4(modules, modules_count):
    dark_count = sum(map(sum, modules))
    percent = float(dark_count) / (modules_count**2)
    # Every 5% departure from 50%, rating++
    rating = int(abs(percent * 100 - 50) / 5)
    return rating * 10


def optimal_data_chunks(data, minimum=4):
    """
    An iterator returning QRData chunks optimized to the data content.

    :param minimum: The minimum number of bytes in a row to split as a chunk.
    """
    data = to_bytestring(data)
    num_pattern = rb"\d"
    alpha_pattern = b"[" + re.escape(ALPHA_NUM) + b"]"
    if len(data) <= minimum:
        num_pattern = re.compile(b"^" + num_pattern + b"+$")
        alpha_pattern = re.compile(b"^" + alpha_pattern + b"+$")
    else:
        re_repeat = b"{" + str(minimum).encode("ascii") + b",}"
        num_pattern = re.compile(num_pattern + re_repeat)
        alpha_pattern = re.compile(alpha_pattern + re_repeat)
    num_bits = _optimal_split(data, num_pattern)
    for is_num, chunk in num_bits:
        if is_num:
            yield QRData(chunk, mode=MODE_NUMBER, check_data=False)
        else:
            for is_alpha, sub_chunk in _optimal_split(chunk, alpha_pattern):
                mode = MODE_ALPHA_NUM if is_alpha else MODE_8BIT_BYTE
                yield QRData(sub_chunk, mode=mode, check_data=False)


def _optimal_split(data, pattern):
    while data:
        match = re.search(pattern, data)
        if not match:
            break
        start, end = match.start(), match.end()
        if start:
            yield False, data[:start]
        yield True, data[start:end]
        data = data[end:]
    if data:
        yield False, data


def to_bytestring(data):
    """
    Convert data to a (utf-8 encoded) byte-string if it isn't a byte-string
    already.
    """
    if not isinstance(data, bytes):
        data = str(data).encode("utf-8")
    return data


def optimal_mode(data):
    """
    Calculate the optimal mode for this chunk of data.
    """
    if data.isdigit():
        return MODE_NUMBER
    return MODE_ALPHA_NUM if RE_ALPHA_NUM.match(data) else MODE_8BIT_BYTE


class QRData:
    """
    Data held in a QR compatible format.

    Doesn't currently handle KANJI.
    """

    def __init__(self, data, mode=None, check_data=True):
        """
        If ``mode`` isn't provided, the most compact QR data type possible is
        chosen.
        """
        if check_data:
            data = to_bytestring(data)

        if mode is None:
            self.mode = optimal_mode(data)
        else:
            self.mode = mode
            if mode not in (MODE_NUMBER, MODE_ALPHA_NUM, MODE_8BIT_BYTE):
                raise TypeError(f"Invalid mode ({mode})")  # pragma: no cover
            if check_data and mode < optimal_mode(data):  # pragma: no cover
                raise ValueError(f"Provided data can not be represented in mode {mode}")

        self.data = data

    def __len__(self):
        return len(self.data)

    def write(self, buffer):
        if self.mode == MODE_NUMBER:
            for i in range(0, len(self.data), 3):
                chars = self.data[i : i + 3]
                bit_length = NUMBER_LENGTH[len(chars)]
                buffer.put(int(chars), bit_length)
        elif self.mode == MODE_ALPHA_NUM:
            for i in range(0, len(self.data), 2):
                chars = self.data[i : i + 2]
                if len(chars) > 1:
                    buffer.put(
                        ALPHA_NUM.find(chars[0]) * 45 + ALPHA_NUM.find(chars[1]), 11
                    )
                else:
                    buffer.put(ALPHA_NUM.find(chars), 6)
        else:
            # Iterating a bytestring in Python 3 returns an integer,
            # no need to ord().
            data = self.data
            for c in data:
                buffer.put(c, 8)

    def __repr__(self):
        return repr(self.data)


class BitBuffer:
    def __init__(self):
        self.buffer: List[int] = []
        self.length = 0

    def __repr__(self):
        return ".".join([str(n) for n in self.buffer])

    def get(self, index):
        buf_index = math.floor(index / 8)
        return ((self.buffer[buf_index] >> (7 - index % 8)) & 1) == 1

    def put(self, num, length):
        for i in range(length):
            self.put_bit(((num >> (length - i - 1)) & 1) == 1)

    def __len__(self):
        return self.length

    def put_bit(self, bit):
        buf_index = self.length // 8
        if len(self.buffer) <= buf_index:
            self.buffer.append(0)
        if bit:
            self.buffer[buf_index] |= 0x80 >> (self.length % 8)
        self.length += 1


def create_bytes(buffer: BitBuffer, rs_blocks: List[RSBlock]):
    offset = 0

    maxDcCount = 0
    maxEcCount = 0

    dcdata: List[List[int]] = []
    ecdata: List[List[int]] = []

    for rs_block in rs_blocks:
        dcCount = rs_block.data_count
        ecCount = rs_block.total_count - dcCount

        maxDcCount = max(maxDcCount, dcCount)
        maxEcCount = max(maxEcCount, ecCount)

        current_dc = [0xFF & buffer.buffer[i + offset] for i in range(dcCount)]
        offset += dcCount

        # Get error correction polynomial.
        if ecCount in rsPoly_LUT:
            rsPoly = Polynomial(rsPoly_LUT[ecCount], 0)
        else:
            rsPoly = Polynomial([1], 0)
            for i in range(ecCount):
                rsPoly = rsPoly * Polynomial([1, gexp(i)], 0)

        rawPoly = Polynomial(current_dc, len(rsPoly) - 1)

        modPoly = rawPoly % rsPoly
        current_ec = []
        mod_offset = len(modPoly) - ecCount
        for i in range(ecCount):
            modIndex = i + mod_offset
            current_ec.append(modPoly[modIndex] if (modIndex >= 0) else 0)

        dcdata.append(current_dc)
        ecdata.append(current_ec)

    data = []
    for i in range(maxDcCount):
        data.extend(dc[i] for dc in dcdata if i < len(dc))
    for i in range(maxEcCount):
        data.extend(ec[i] for ec in ecdata if i < len(ec))
    return data


def create_data(version, error_correction, data_list):
    buffer = BitBuffer()
    for data in data_list:
        buffer.put(data.mode, 4)
        buffer.put(len(data), length_in_bits(data.mode, version))
        data.write(buffer)

    # Calculate the maximum number of bits for the given version.
    rs_blocks_ = rs_blocks(version, error_correction)
    bit_limit = sum(block.data_count * 8 for block in rs_blocks_)
    if len(buffer) > bit_limit:
        raise DataOverflowError(
            f"Code length overflow. Data size ({len(buffer)}) > size available ({bit_limit})"
        )

    # Terminate the bits (add up to four 0s).
    for _ in range(min(bit_limit - len(buffer), 4)):
        buffer.put_bit(False)

    if delimit := len(buffer) % 8:
        for _ in range(8 - delimit):
            buffer.put_bit(False)

    # Add special alternating padding bitstrings until buffer is full.
    bytes_to_fill = (bit_limit - len(buffer)) // 8
    for i in range(bytes_to_fill):
        if i % 2 == 0:
            buffer.put(PAD0, 8)
        else:
            buffer.put(PAD1, 8)

    return create_bytes(buffer, rs_blocks_)


class DataOverflowError(Exception):
    pass


ModulesType = List[List[Optional[bool]]]
# Cache modules generated just based on the QR Code version
precomputed_qr_blanks: Dict[int, ModulesType] = {}


def _check_box_size(size):
    if int(size) <= 0:
        raise ValueError(f"Invalid box size (was {size}, expected larger than 0)")


def _check_border(size):
    if int(size) < 0:
        raise ValueError(
            f"Invalid border value (was {size}, expected 0 or larger than that)"
        )


def _check_mask_pattern(mask_pattern):
    if mask_pattern is None:
        return
    if not isinstance(mask_pattern, int):
        raise TypeError(
            f"Invalid mask pattern (was {type(mask_pattern)}, expected int)"
        )
    if mask_pattern < 0 or mask_pattern > 7:
        raise ValueError(f"Mask pattern should be in range(8) (got {mask_pattern})")


def copy_2d_array(x):
    return [row[:] for row in x]


class ActiveWithNeighbors(NamedTuple):
    NW: bool
    N: bool
    NE: bool
    W: bool
    me: bool
    E: bool
    SW: bool
    S: bool
    SE: bool

    def __bool__(self) -> bool:
        return self.me


class QRCode:
    modules: ModulesType
    _version: Optional[int] = None

    def __init__(
        self,
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    ):
        _check_box_size(box_size)
        _check_border(border)
        self.version = version
        self.error_correction = int(error_correction)
        self.box_size = int(box_size)
        # Spec says border should be at least four boxes wide, but allow for
        # any (e.g. for producing printable QR codes).
        self.border = int(border)
        self.clear()
        self._mask_pattern = None

    @property
    def version(self) -> int:
        if self._version is None:
            self.best_fit()
        return cast(int, self._version)

    @version.setter
    def version(self, value) -> None:
        if value is not None:
            value = int(value)
            check_version(value)
        self._version = value

    @property
    def mask_pattern(self):
        return self._mask_pattern

    @mask_pattern.setter
    def mask_pattern(self, pattern):
        _check_mask_pattern(pattern)
        self._mask_pattern = pattern

    def clear(self):
        """
        Reset the internal data.
        """
        self.modules = [[]]
        self.modules_count = 0
        self.data_cache = None
        self.data_list = []

    def add_data(self, data, optimize=20):
        """
        Add data to this QR Code.

        :param optimize: Data will be split into multiple chunks to optimize
            the QR size by finding to more compressed modes of at least this
            length. Set to ``0`` to avoid optimizing at all.
        """
        if isinstance(data, QRData):
            self.data_list.append(data)
        elif optimize:
            self.data_list.extend(optimal_data_chunks(data, minimum=optimize))
        else:
            self.data_list.append(QRData(data))
        self.data_cache = None

    def make(self, fit=True):
        """
        Compile the data into a QR Code array.

        :param fit: If ``True`` (or if a size has not been provided), find the
            best fit for the data to avoid data overflow errors.
        """
        if fit or (self.version is None):
            self.best_fit(start=self.version)
        if self.mask_pattern is None:
            self.makeImpl(False, self.best_mask_pattern())
        else:
            self.makeImpl(False, self.mask_pattern)

    def makeImpl(self, test, mask_pattern):
        self.modules_count = self.version * 4 + 17

        if self.version in precomputed_qr_blanks:
            self.modules = copy_2d_array(precomputed_qr_blanks[self.version])
        else:
            self.modules = [[None] * self.modules_count for _ in range(self.modules_count)]
            self.setup_position_probe_pattern(0, 0)
            self.setup_position_probe_pattern(self.modules_count - 7, 0)
            self.setup_position_probe_pattern(0, self.modules_count - 7)
            self.setup_position_adjust_pattern()
            self.setup_timing_pattern()

            precomputed_qr_blanks[self.version] = copy_2d_array(self.modules)

        self.setup_type_info(test, mask_pattern)

        if self.version >= 7:
            self.setup_type_number(test)

        if self.data_cache is None:
            self.data_cache = create_data(
                self.version, self.error_correction, self.data_list
            )
        self.map_data(self.data_cache, mask_pattern)

    def setup_position_probe_pattern(self, row, col):
        for r in range(-1, 8):
            if row + r <= -1 or self.modules_count <= row + r:
                continue

            for c in range(-1, 8):
                if col + c <= -1 or self.modules_count <= col + c:
                    continue

                self.modules[row + r][col + c] = (
                    (0 <= r <= 6 and c in {0, 6})
                    or (0 <= c <= 6 and r in {0, 6})
                    or (2 <= r <= 4 and 2 <= c <= 4)
                )

    def best_fit(self, start=None):
        """
        Find the minimum size required to fit in the data.
        """
        if start is None:
            start = 1
        check_version(start)

        # Corresponds to the code in create_data, except we don't yet know
        # version, so optimistically assume start and check later
        mode_sizes = mode_sizes_for_version(start)
        buffer = BitBuffer()
        for data in self.data_list:
            buffer.put(data.mode, 4)
            buffer.put(len(data), mode_sizes[data.mode])
            data.write(buffer)

        needed_bits = len(buffer)
        self.version = bisect_left(
            BIT_LIMIT_TABLE[self.error_correction], needed_bits, start
        )
        if self.version == 41:
            raise DataOverflowError()

        # Now check whether we need more bits for the mode sizes, recursing if
        # our guess was too low
        if mode_sizes is not mode_sizes_for_version(self.version):
            self.best_fit(start=self.version)
        return self.version

    def best_mask_pattern(self):
        """
        Find the most efficient mask pattern.
        """
        min_lost_point = 0
        pattern = 0

        for i in range(8):
            self.makeImpl(True, i)

            lost_point_ = lost_point(self.modules)

            if i == 0 or min_lost_point > lost_point_:
                min_lost_point = lost_point_
                pattern = i

        return pattern

    def print_tty(self, out=None):
        """
        Output the QR Code only using TTY colors.
        If the data has not been compiled yet, make it first.
        """
        if out is None:
            import sys

            out = sys.stdout

        if not out.isatty():
            raise OSError("Not a tty")

        if self.data_cache is None:
            self.make()

        modcount = self.modules_count
        out.write("\x1b[1;47m" + (" " * (modcount * 2 + 4)) + "\x1b[0m\n")
        for r in range(modcount):
            out.write("\x1b[1;47m  \x1b[40m")
            for c in range(modcount):
                if self.modules[r][c]:
                    out.write("  ")
                else:
                    out.write("\x1b[1;47m  \x1b[40m")
            out.write("\x1b[1;47m  \x1b[0m\n")
        out.write("\x1b[1;47m" + (" " * (modcount * 2 + 4)) + "\x1b[0m\n")
        out.flush()

    def print_ascii(self, out=None, tty=False, invert=False):
        """
        Output the QR Code using ASCII characters.

        :param tty: use fixed TTY color codes (forces invert=True)
        :param invert: invert the ASCII characters (solid <-> transparent)
        """
        if out is None:
            out = sys.stdout

        if tty and not out.isatty():
            raise OSError("Not a tty")

        if self.data_cache is None:
            self.make()

        modcount = self.modules_count
        codes = [bytes((code,)).decode("cp437") for code in (255, 223, 220, 219)]
        if tty:
            invert = True
        if invert:
            codes.reverse()

        def get_module(x, y) -> int:
            if invert and self.border and max(x, y) >= modcount + self.border:
                return 1
            if min(x, y) < 0 or max(x, y) >= modcount:
                return 0
            return cast(int, self.modules[x][y])

        for r in range(-self.border, modcount + self.border, 2):
            if tty:
                if not invert or r < modcount + self.border - 1:
                    out.write("\x1b[48;5;232m")  # Background black
                out.write("\x1b[38;5;255m")  # Foreground white
            for c in range(-self.border, modcount + self.border):
                pos = get_module(r, c) + (get_module(r + 1, c) << 1)
                out.write(codes[pos])
            if tty:
                out.write("\x1b[0m")
            out.write("\n")
        out.flush()

    # return true if and only if (row, col) is in the module
    def is_constrained(self, row: int, col: int) -> bool:
        return (
            row >= 0
            and row < len(self.modules)
            and col >= 0
            and col < len(self.modules[row])
        )

    def setup_timing_pattern(self):
        for r in range(8, self.modules_count - 8):
            if self.modules[r][6] is not None:
                continue
            self.modules[r][6] = r % 2 == 0

        for c in range(8, self.modules_count - 8):
            if self.modules[6][c] is not None:
                continue
            self.modules[6][c] = c % 2 == 0

    def setup_position_adjust_pattern(self):
        pos = pattern_position(self.version)

        for i in range(len(pos)):
            row = pos[i]

            for j in range(len(pos)):
                col = pos[j]

                if self.modules[row][col] is not None:
                    continue

                for r in range(-2, 3):
                    for c in range(-2, 3):
                        self.modules[row + r][col + c] = (
                            r == -2
                            or r == 2
                            or c == -2
                            or c == 2
                            or (r == 0 and c == 0)
                        )

    def setup_type_number(self, test):
        bits = BCH_type_number(self.version)

        for i in range(18):
            mod = not test and ((bits >> i) & 1) == 1
            self.modules[i // 3][i % 3 + self.modules_count - 8 - 3] = mod

        for i in range(18):
            mod = not test and ((bits >> i) & 1) == 1
            self.modules[i % 3 + self.modules_count - 8 - 3][i // 3] = mod

    def setup_type_info(self, test, mask_pattern):
        data = (self.error_correction << 3) | mask_pattern
        bits = BCH_type_info(data)

        # vertical
        for i in range(15):
            mod = not test and ((bits >> i) & 1) == 1

            if i < 6:
                self.modules[i][8] = mod
            elif i < 8:
                self.modules[i + 1][8] = mod
            else:
                self.modules[self.modules_count - 15 + i][8] = mod

        # horizontal
        for i in range(15):
            mod = not test and ((bits >> i) & 1) == 1

            if i < 8:
                self.modules[8][self.modules_count - i - 1] = mod
            elif i < 9:
                self.modules[8][15 - i - 1 + 1] = mod
            else:
                self.modules[8][15 - i - 1] = mod

        # fixed module
        self.modules[self.modules_count - 8][8] = not test

    def map_data(self, data, mask_pattern):
        inc = -1
        row = self.modules_count - 1
        bitIndex = 7
        byteIndex = 0

        mask_func_ = mask_func(mask_pattern)

        data_len = len(data)

        for col in range(self.modules_count - 1, 0, -2):
            if col <= 6:
                col -= 1

            col_range = (col, col - 1)

            while True:
                for c in col_range:
                    if self.modules[row][c] is None:
                        dark = False

                        if byteIndex < data_len:
                            dark = ((data[byteIndex] >> bitIndex) & 1) == 1

                        if mask_func_(row, c):
                            dark = not dark

                        self.modules[row][c] = dark
                        bitIndex -= 1

                        if bitIndex == -1:
                            byteIndex += 1
                            bitIndex = 7

                row += inc

                if row < 0 or self.modules_count <= row:
                    row -= inc
                    inc = -inc
                    break

    def get_matrix(self):
        """
        Return the QR Code as a multidimensional array, including the border.

        To return the array without a border, set ``self.border`` to 0 first.
        """
        if self.data_cache is None:
            self.make()

        if not self.border:
            return self.modules

        width = len(self.modules) + self.border * 2
        code = [[False] * width] * self.border
        x_border = [False] * self.border
        for module in self.modules:
            code.append(x_border + cast(List[bool], module) + x_border)
        code += [[False] * width] * self.border

        return code

    def active_with_neighbors(self, row: int, col: int) -> ActiveWithNeighbors:
        context: List[bool] = []
        for r in range(row - 1, row + 2):
            context.extend(
                (self.is_constrained(r, c) and bool(self.modules[r][c]))
                for c in range(col - 1, col + 2)
            )
        return ActiveWithNeighbors(*context)
