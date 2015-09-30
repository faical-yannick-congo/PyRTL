""" AES-128 """

import pyrtl
import sys
from rtllib import libutils

# TODO:
# 1) Right now all ROMs are global -- need to be moved into function so each
#    instance of the AES block creates it's own memories
# 2) All ROMs should be syncronous.  This should be easy once (3) is completed
# 3) Right now aes_decryption generates one GIANT combinational block. Instead
#    it should generate one of 2 options -- Either an interative design or a
#    pipelined design.  Both will add registers between each round of AES
# 4) aes_encryption should be added to this file as well so that an
#    aes encrypter similar to (3) above is generated
# 5) a single "aes-unit" combining encryption and decryption (without making
#    full independent hardware units) would be a plus as well
# 6) The constants right now are a big ugly list -- it might be better to
#    store them as a multi-line string like: '0f bf 53 2c ...' and then
#    provide a small helper funciton to parse them out.  It might be a nice
#    utility for pyrtl itself to include.


def _g(word, key_expand_round):
    # One-byte left circular rotation, substitution of each byte
    a = libutils.partition_wire(word, 8)
    sub = pyrtl.concat(sbox[a[1]], sbox[a[2]], sbox[a[3]], sbox[a[0]])
    # xor substituted bytes with round constant.
    round_const = pyrtl.concat(rcon[key_expand_round + 1], pyrtl.Const(0, bitwidth=24))
    return round_const ^ sub


def key_expansion(key):
    w = list(reversed(libutils.partition_wire(key, 32)))
    for key_expand_round in range(10):
        last = key_expand_round * 4
        w.append(w[last] ^ _g(w[last + 3], key_expand_round))
        w.append(w[-1] ^ w[last + 1])
        w.append(w[-1] ^ w[last + 2])
        w.append(w[-1] ^ w[last + 3])
    return pyrtl.concat(*w)


def inv_sub_bytes(in_vector):
    subbed = [inv_sbox[byte] for byte in libutils.partition_wire(in_vector, 8)]
    return pyrtl.concat(*subbed)


def inv_shift_rows(in_vector):
    a = libutils.partition_wire(in_vector, 8)
    out_vector = pyrtl.concat(a[0], a[7], a[10], a[13],
                              a[1], a[4], a[11], a[14],
                              a[2], a[5], a[8],  a[15],
                              a[3], a[6], a[9],  a[12])
    return out_vector


def inv_galois_mult(c, d):
    # 09 = 9, 0B = 11, 0D = 13, 0E = 14
    assert d == 9 or d == 11 or d == 13 or d == 14
    if d == 9:
        return GM9[c]
    elif d == 11:
        return GM11[c]
    elif d == 13:
        return GM13[c]
    elif d == 14:
        return GM14[c]


def inv_mix_columns(in_vector):
    a = libutils.partition_wire(in_vector, 8)

    b0 = inv_galois_mult(a[0],  14) ^ inv_galois_mult(
        a[1], 11) ^ inv_galois_mult(a[2], 13) ^ inv_galois_mult(a[3], 9)
    b1 = inv_galois_mult(a[1],  14) ^ inv_galois_mult(
        a[2], 11) ^ inv_galois_mult(a[3], 13) ^ inv_galois_mult(a[0], 9)
    b2 = inv_galois_mult(a[2],  14) ^ inv_galois_mult(
        a[3], 11) ^ inv_galois_mult(a[0], 13) ^ inv_galois_mult(a[1], 9)
    b3 = inv_galois_mult(a[3],  14) ^ inv_galois_mult(
        a[0], 11) ^ inv_galois_mult(a[1], 13) ^ inv_galois_mult(a[2], 9)

    b4 = inv_galois_mult(a[4],  14) ^ inv_galois_mult(
        a[5], 11) ^ inv_galois_mult(a[6], 13) ^ inv_galois_mult(a[7], 9)
    b5 = inv_galois_mult(a[5],  14) ^ inv_galois_mult(
        a[6], 11) ^ inv_galois_mult(a[7], 13) ^ inv_galois_mult(a[4], 9)
    b6 = inv_galois_mult(a[6],  14) ^ inv_galois_mult(
        a[7], 11) ^ inv_galois_mult(a[4], 13) ^ inv_galois_mult(a[5], 9)
    b7 = inv_galois_mult(a[7],  14) ^ inv_galois_mult(
        a[4], 11) ^ inv_galois_mult(a[5], 13) ^ inv_galois_mult(a[6], 9)

    b8 = inv_galois_mult(a[8],  14) ^ inv_galois_mult(
        a[9], 11) ^ inv_galois_mult(a[10], 13) ^ inv_galois_mult(a[11], 9)
    b9 = inv_galois_mult(a[9],  14) ^ inv_galois_mult(
        a[10], 11) ^ inv_galois_mult(a[11], 13) ^ inv_galois_mult(a[8], 9)
    b10 = inv_galois_mult(a[10], 14) ^ inv_galois_mult(
        a[11], 11) ^ inv_galois_mult(a[8], 13) ^ inv_galois_mult(a[9], 9)
    b11 = inv_galois_mult(a[11], 14) ^ inv_galois_mult(
        a[8], 11) ^ inv_galois_mult(a[9], 13) ^ inv_galois_mult(a[10], 9)

    b12 = inv_galois_mult(a[12], 14) ^ inv_galois_mult(
        a[13], 11) ^ inv_galois_mult(a[14], 13) ^ inv_galois_mult(a[15], 9)
    b13 = inv_galois_mult(a[13], 14) ^ inv_galois_mult(
        a[14], 11) ^ inv_galois_mult(a[15], 13) ^ inv_galois_mult(a[12], 9)
    b14 = inv_galois_mult(a[14], 14) ^ inv_galois_mult(
        a[15], 11) ^ inv_galois_mult(a[12], 13) ^ inv_galois_mult(a[13], 9)
    b15 = inv_galois_mult(a[15], 14) ^ inv_galois_mult(
        a[12], 11) ^ inv_galois_mult(a[13], 13) ^ inv_galois_mult(a[14], 9)

    out_vector = pyrtl.concat(b0, b1, b2, b3,
                              b4, b5, b6, b7,
                              b8, b9, b10, b11,
                              b12, b13, b14, b15)
    return out_vector


def addroundkey(t, expanded_key, round):
    offset = round * 128
    return t ^ expanded_key[offset:offset + 128]


def aes_decryption(ciphertext, key):
    expanded_key = key_expansion(key)  # Expanding the key (key expansion).
    t = addroundkey(ciphertext, expanded_key, 0)  # Initial AddRoundKey.

    for round in range(1, 11):
        t = inv_shift_rows(t)
        t = inv_sub_bytes(t)
        t = addroundkey(t, expanded_key, round)
        if round != 10:
            t = inv_mix_columns(t)

    return t


# S-box ROM data.
sbox_data = [0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
             0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
             0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0,
             0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
             0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc,
             0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
             0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a,
             0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
             0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0,
             0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
             0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b,
             0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
             0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85,
             0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
             0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5,
             0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
             0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17,
             0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
             0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88,
             0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
             0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c,
             0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
             0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9,
             0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
             0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6,
             0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
             0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e,
             0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
             0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94,
             0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
             0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68,
             0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16]

sbox = pyrtl.RomBlock(bitwidth=8, addrwidth=8, romdata=sbox_data, asynchronous=True)

# Inverse S-box ROM data.
inv_sbox_data = [0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38,
                 0xbf, 0x40, 0xa3, 0x9e, 0x81, 0xf3, 0xd7, 0xfb,
                 0x7c, 0xe3, 0x39, 0x82, 0x9b, 0x2f, 0xff, 0x87,
                 0x34, 0x8e, 0x43, 0x44, 0xc4, 0xde, 0xe9, 0xcb,
                 0x54, 0x7b, 0x94, 0x32, 0xa6, 0xc2, 0x23, 0x3d,
                 0xee, 0x4c, 0x95, 0x0b, 0x42, 0xfa, 0xc3, 0x4e,
                 0x08, 0x2e, 0xa1, 0x66, 0x28, 0xd9, 0x24, 0xb2,
                 0x76, 0x5b, 0xa2, 0x49, 0x6d, 0x8b, 0xd1, 0x25,
                 0x72, 0xf8, 0xf6, 0x64, 0x86, 0x68, 0x98, 0x16,
                 0xd4, 0xa4, 0x5c, 0xcc, 0x5d, 0x65, 0xb6, 0x92,
                 0x6c, 0x70, 0x48, 0x50, 0xfd, 0xed, 0xb9, 0xda,
                 0x5e, 0x15, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84,
                 0x90, 0xd8, 0xab, 0x00, 0x8c, 0xbc, 0xd3, 0x0a,
                 0xf7, 0xe4, 0x58, 0x05, 0xb8, 0xb3, 0x45, 0x06,
                 0xd0, 0x2c, 0x1e, 0x8f, 0xca, 0x3f, 0x0f, 0x02,
                 0xc1, 0xaf, 0xbd, 0x03, 0x01, 0x13, 0x8a, 0x6b,
                 0x3a, 0x91, 0x11, 0x41, 0x4f, 0x67, 0xdc, 0xea,
                 0x97, 0xf2, 0xcf, 0xce, 0xf0, 0xb4, 0xe6, 0x73,
                 0x96, 0xac, 0x74, 0x22, 0xe7, 0xad, 0x35, 0x85,
                 0xe2, 0xf9, 0x37, 0xe8, 0x1c, 0x75, 0xdf, 0x6e,
                 0x47, 0xf1, 0x1a, 0x71, 0x1d, 0x29, 0xc5, 0x89,
                 0x6f, 0xb7, 0x62, 0x0e, 0xaa, 0x18, 0xbe, 0x1b,
                 0xfc, 0x56, 0x3e, 0x4b, 0xc6, 0xd2, 0x79, 0x20,
                 0x9a, 0xdb, 0xc0, 0xfe, 0x78, 0xcd, 0x5a, 0xf4,
                 0x1f, 0xdd, 0xa8, 0x33, 0x88, 0x07, 0xc7, 0x31,
                 0xb1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xec, 0x5f,
                 0x60, 0x51, 0x7f, 0xa9, 0x19, 0xb5, 0x4a, 0x0d,
                 0x2d, 0xe5, 0x7a, 0x9f, 0x93, 0xc9, 0x9c, 0xef,
                 0xa0, 0xe0, 0x3b, 0x4d, 0xae, 0x2a, 0xf5, 0xb0,
                 0xc8, 0xeb, 0xbb, 0x3c, 0x83, 0x53, 0x99, 0x61,
                 0x17, 0x2b, 0x04, 0x7e, 0xba, 0x77, 0xd6, 0x26,
                 0xe1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0c, 0x7d]

inv_sbox = pyrtl.RomBlock(bitwidth=8, addrwidth=8, romdata=inv_sbox_data, asynchronous=True)

# Rcon ROM data
rcon_data = [0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40,
             0x80, 0x1b, 0x36, 0x6c, 0xd8, 0xab, 0x4d, 0x9a,
             0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97, 0x35, 0x6a,
             0xd4, 0xb3, 0x7d, 0xfa, 0xef, 0xc5, 0x91, 0x39,
             0x72, 0xe4, 0xd3, 0xbd, 0x61, 0xc2, 0x9f, 0x25,
             0x4a, 0x94, 0x33, 0x66, 0xcc, 0x83, 0x1d, 0x3a,
             0x74, 0xe8, 0xcb, 0x8d, 0x01, 0x02, 0x04, 0x08,
             0x10, 0x20, 0x40, 0x80, 0x1b, 0x36, 0x6c, 0xd8,
             0xab, 0x4d, 0x9a, 0x2f, 0x5e, 0xbc, 0x63, 0xc6,
             0x97, 0x35, 0x6a, 0xd4, 0xb3, 0x7d, 0xfa, 0xef,
             0xc5, 0x91, 0x39, 0x72, 0xe4, 0xd3, 0xbd, 0x61,
             0xc2, 0x9f, 0x25, 0x4a, 0x94, 0x33, 0x66, 0xcc,
             0x83, 0x1d, 0x3a, 0x74, 0xe8, 0xcb, 0x8d, 0x01,
             0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b,
             0x36, 0x6c, 0xd8, 0xab, 0x4d, 0x9a, 0x2f, 0x5e,
             0xbc, 0x63, 0xc6, 0x97, 0x35, 0x6a, 0xd4, 0xb3,
             0x7d, 0xfa, 0xef, 0xc5, 0x91, 0x39, 0x72, 0xe4,
             0xd3, 0xbd, 0x61, 0xc2, 0x9f, 0x25, 0x4a, 0x94,
             0x33, 0x66, 0xcc, 0x83, 0x1d, 0x3a, 0x74, 0xe8,
             0xcb, 0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20,
             0x40, 0x80, 0x1b, 0x36, 0x6c, 0xd8, 0xab, 0x4d,
             0x9a, 0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97, 0x35,
             0x6a, 0xd4, 0xb3, 0x7d, 0xfa, 0xef, 0xc5, 0x91,
             0x39, 0x72, 0xe4, 0xd3, 0xbd, 0x61, 0xc2, 0x9f,
             0x25, 0x4a, 0x94, 0x33, 0x66, 0xcc, 0x83, 0x1d,
             0x3a, 0x74, 0xe8, 0xcb, 0x8d, 0x01, 0x02, 0x04,
             0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36, 0x6c,
             0xd8, 0xab, 0x4d, 0x9a, 0x2f, 0x5e, 0xbc, 0x63,
             0xc6, 0x97, 0x35, 0x6a, 0xd4, 0xb3, 0x7d, 0xfa,
             0xef, 0xc5, 0x91, 0x39, 0x72, 0xe4, 0xd3, 0xbd,
             0x61, 0xc2, 0x9f, 0x25, 0x4a, 0x94, 0x33, 0x66,
             0xcc, 0x83, 0x1d, 0x3a, 0x74, 0xe8, 0xcb, 0x8d]

rcon = pyrtl.RomBlock(bitwidth=8, addrwidth=8, romdata=rcon_data, asynchronous=True)

# Galois Multiplication tables for 9, 11, 13, and 14.

GM9_data = [0x00, 0x09, 0x12, 0x1b, 0x24, 0x2d, 0x36, 0x3f,
            0x48, 0x41, 0x5a, 0x53, 0x6c, 0x65, 0x7e, 0x77,
            0x90, 0x99, 0x82, 0x8b, 0xb4, 0xbd, 0xa6, 0xaf,
            0xd8, 0xd1, 0xca, 0xc3, 0xfc, 0xf5, 0xee, 0xe7,
            0x3b, 0x32, 0x29, 0x20, 0x1f, 0x16, 0x0d, 0x04,
            0x73, 0x7a, 0x61, 0x68, 0x57, 0x5e, 0x45, 0x4c,
            0xab, 0xa2, 0xb9, 0xb0, 0x8f, 0x86, 0x9d, 0x94,
            0xe3, 0xea, 0xf1, 0xf8, 0xc7, 0xce, 0xd5, 0xdc,
            0x76, 0x7f, 0x64, 0x6d, 0x52, 0x5b, 0x40, 0x49,
            0x3e, 0x37, 0x2c, 0x25, 0x1a, 0x13, 0x08, 0x01,
            0xe6, 0xef, 0xf4, 0xfd, 0xc2, 0xcb, 0xd0, 0xd9,
            0xae, 0xa7, 0xbc, 0xb5, 0x8a, 0x83, 0x98, 0x91,
            0x4d, 0x44, 0x5f, 0x56, 0x69, 0x60, 0x7b, 0x72,
            0x05, 0x0c, 0x17, 0x1e, 0x21, 0x28, 0x33, 0x3a,
            0xdd, 0xd4, 0xcf, 0xc6, 0xf9, 0xf0, 0xeb, 0xe2,
            0x95, 0x9c, 0x87, 0x8e, 0xb1, 0xb8, 0xa3, 0xaa,
            0xec, 0xe5, 0xfe, 0xf7, 0xc8, 0xc1, 0xda, 0xd3,
            0xa4, 0xad, 0xb6, 0xbf, 0x80, 0x89, 0x92, 0x9b,
            0x7c, 0x75, 0x6e, 0x67, 0x58, 0x51, 0x4a, 0x43,
            0x34, 0x3d, 0x26, 0x2f, 0x10, 0x19, 0x02, 0x0b,
            0xd7, 0xde, 0xc5, 0xcc, 0xf3, 0xfa, 0xe1, 0xe8,
            0x9f, 0x96, 0x8d, 0x84, 0xbb, 0xb2, 0xa9, 0xa0,
            0x47, 0x4e, 0x55, 0x5c, 0x63, 0x6a, 0x71, 0x78,
            0x0f, 0x06, 0x1d, 0x14, 0x2b, 0x22, 0x39, 0x30,
            0x9a, 0x93, 0x88, 0x81, 0xbe, 0xb7, 0xac, 0xa5,
            0xd2, 0xdb, 0xc0, 0xc9, 0xf6, 0xff, 0xe4, 0xed,
            0x0a, 0x03, 0x18, 0x11, 0x2e, 0x27, 0x3c, 0x35,
            0x42, 0x4b, 0x50, 0x59, 0x66, 0x6f, 0x74, 0x7d,
            0xa1, 0xa8, 0xb3, 0xba, 0x85, 0x8c, 0x97, 0x9e,
            0xe9, 0xe0, 0xfb, 0xf2, 0xcd, 0xc4, 0xdf, 0xd6,
            0x31, 0x38, 0x23, 0x2a, 0x15, 0x1c, 0x07, 0x0e,
            0x79, 0x70, 0x6b, 0x62, 0x5d, 0x54, 0x4f, 0x46]

GM11_data = [0x00, 0x0b, 0x16, 0x1d, 0x2c, 0x27, 0x3a, 0x31,
             0x58, 0x53, 0x4e, 0x45, 0x74, 0x7f, 0x62, 0x69,
             0xb0, 0xbb, 0xa6, 0xad, 0x9c, 0x97, 0x8a, 0x81,
             0xe8, 0xe3, 0xfe, 0xf5, 0xc4, 0xcf, 0xd2, 0xd9,
             0x7b, 0x70, 0x6d, 0x66, 0x57, 0x5c, 0x41, 0x4a,
             0x23, 0x28, 0x35, 0x3e, 0x0f, 0x04, 0x19, 0x12,
             0xcb, 0xc0, 0xdd, 0xd6, 0xe7, 0xec, 0xf1, 0xfa,
             0x93, 0x98, 0x85, 0x8e, 0xbf, 0xb4, 0xa9, 0xa2,
             0xf6, 0xfd, 0xe0, 0xeb, 0xda, 0xd1, 0xcc, 0xc7,
             0xae, 0xa5, 0xb8, 0xb3, 0x82, 0x89, 0x94, 0x9f,
             0x46, 0x4d, 0x50, 0x5b, 0x6a, 0x61, 0x7c, 0x77,
             0x1e, 0x15, 0x08, 0x03, 0x32, 0x39, 0x24, 0x2f,
             0x8d, 0x86, 0x9b, 0x90, 0xa1, 0xaa, 0xb7, 0xbc,
             0xd5, 0xde, 0xc3, 0xc8, 0xf9, 0xf2, 0xef, 0xe4,
             0x3d, 0x36, 0x2b, 0x20, 0x11, 0x1a, 0x07, 0x0c,
             0x65, 0x6e, 0x73, 0x78, 0x49, 0x42, 0x5f, 0x54,
             0xf7, 0xfc, 0xe1, 0xea, 0xdb, 0xd0, 0xcd, 0xc6,
             0xaf, 0xa4, 0xb9, 0xb2, 0x83, 0x88, 0x95, 0x9e,
             0x47, 0x4c, 0x51, 0x5a, 0x6b, 0x60, 0x7d, 0x76,
             0x1f, 0x14, 0x09, 0x02, 0x33, 0x38, 0x25, 0x2e,
             0x8c, 0x87, 0x9a, 0x91, 0xa0, 0xab, 0xb6, 0xbd,
             0xd4, 0xdf, 0xc2, 0xc9, 0xf8, 0xf3, 0xee, 0xe5,
             0x3c, 0x37, 0x2a, 0x21, 0x10, 0x1b, 0x06, 0x0d,
             0x64, 0x6f, 0x72, 0x79, 0x48, 0x43, 0x5e, 0x55,
             0x01, 0x0a, 0x17, 0x1c, 0x2d, 0x26, 0x3b, 0x30,
             0x59, 0x52, 0x4f, 0x44, 0x75, 0x7e, 0x63, 0x68,
             0xb1, 0xba, 0xa7, 0xac, 0x9d, 0x96, 0x8b, 0x80,
             0xe9, 0xe2, 0xff, 0xf4, 0xc5, 0xce, 0xd3, 0xd8,
             0x7a, 0x71, 0x6c, 0x67, 0x56, 0x5d, 0x40, 0x4b,
             0x22, 0x29, 0x34, 0x3f, 0x0e, 0x05, 0x18, 0x13,
             0xca, 0xc1, 0xdc, 0xd7, 0xe6, 0xed, 0xf0, 0xfb,
             0x92, 0x99, 0x84, 0x8f, 0xbe, 0xb5, 0xa8, 0xa3]

GM13_data = [0x00, 0x0d, 0x1a, 0x17, 0x34, 0x39, 0x2e, 0x23,
             0x68, 0x65, 0x72, 0x7f, 0x5c, 0x51, 0x46, 0x4b,
             0xd0, 0xdd, 0xca, 0xc7, 0xe4, 0xe9, 0xfe, 0xf3,
             0xb8, 0xb5, 0xa2, 0xaf, 0x8c, 0x81, 0x96, 0x9b,
             0xbb, 0xb6, 0xa1, 0xac, 0x8f, 0x82, 0x95, 0x98,
             0xd3, 0xde, 0xc9, 0xc4, 0xe7, 0xea, 0xfd, 0xf0,
             0x6b, 0x66, 0x71, 0x7c, 0x5f, 0x52, 0x45, 0x48,
             0x03, 0x0e, 0x19, 0x14, 0x37, 0x3a, 0x2d, 0x20,
             0x6d, 0x60, 0x77, 0x7a, 0x59, 0x54, 0x43, 0x4e,
             0x05, 0x08, 0x1f, 0x12, 0x31, 0x3c, 0x2b, 0x26,
             0xbd, 0xb0, 0xa7, 0xaa, 0x89, 0x84, 0x93, 0x9e,
             0xd5, 0xd8, 0xcf, 0xc2, 0xe1, 0xec, 0xfb, 0xf6,
             0xd6, 0xdb, 0xcc, 0xc1, 0xe2, 0xef, 0xf8, 0xf5,
             0xbe, 0xb3, 0xa4, 0xa9, 0x8a, 0x87, 0x90, 0x9d,
             0x06, 0x0b, 0x1c, 0x11, 0x32, 0x3f, 0x28, 0x25,
             0x6e, 0x63, 0x74, 0x79, 0x5a, 0x57, 0x40, 0x4d,
             0xda, 0xd7, 0xc0, 0xcd, 0xee, 0xe3, 0xf4, 0xf9,
             0xb2, 0xbf, 0xa8, 0xa5, 0x86, 0x8b, 0x9c, 0x91,
             0x0a, 0x07, 0x10, 0x1d, 0x3e, 0x33, 0x24, 0x29,
             0x62, 0x6f, 0x78, 0x75, 0x56, 0x5b, 0x4c, 0x41,
             0x61, 0x6c, 0x7b, 0x76, 0x55, 0x58, 0x4f, 0x42,
             0x09, 0x04, 0x13, 0x1e, 0x3d, 0x30, 0x27, 0x2a,
             0xb1, 0xbc, 0xab, 0xa6, 0x85, 0x88, 0x9f, 0x92,
             0xd9, 0xd4, 0xc3, 0xce, 0xed, 0xe0, 0xf7, 0xfa,
             0xb7, 0xba, 0xad, 0xa0, 0x83, 0x8e, 0x99, 0x94,
             0xdf, 0xd2, 0xc5, 0xc8, 0xeb, 0xe6, 0xf1, 0xfc,
             0x67, 0x6a, 0x7d, 0x70, 0x53, 0x5e, 0x49, 0x44,
             0x0f, 0x02, 0x15, 0x18, 0x3b, 0x36, 0x21, 0x2c,
             0x0c, 0x01, 0x16, 0x1b, 0x38, 0x35, 0x22, 0x2f,
             0x64, 0x69, 0x7e, 0x73, 0x50, 0x5d, 0x4a, 0x47,
             0xdc, 0xd1, 0xc6, 0xcb, 0xe8, 0xe5, 0xf2, 0xff,
             0xb4, 0xb9, 0xae, 0xa3, 0x80, 0x8d, 0x9a, 0x97]

GM14_data = [0x00, 0x0e, 0x1c, 0x12, 0x38, 0x36, 0x24, 0x2a,
             0x70, 0x7e, 0x6c, 0x62, 0x48, 0x46, 0x54, 0x5a,
             0xe0, 0xee, 0xfc, 0xf2, 0xd8, 0xd6, 0xc4, 0xca,
             0x90, 0x9e, 0x8c, 0x82, 0xa8, 0xa6, 0xb4, 0xba,
             0xdb, 0xd5, 0xc7, 0xc9, 0xe3, 0xed, 0xff, 0xf1,
             0xab, 0xa5, 0xb7, 0xb9, 0x93, 0x9d, 0x8f, 0x81,
             0x3b, 0x35, 0x27, 0x29, 0x03, 0x0d, 0x1f, 0x11,
             0x4b, 0x45, 0x57, 0x59, 0x73, 0x7d, 0x6f, 0x61,
             0xad, 0xa3, 0xb1, 0xbf, 0x95, 0x9b, 0x89, 0x87,
             0xdd, 0xd3, 0xc1, 0xcf, 0xe5, 0xeb, 0xf9, 0xf7,
             0x4d, 0x43, 0x51, 0x5f, 0x75, 0x7b, 0x69, 0x67,
             0x3d, 0x33, 0x21, 0x2f, 0x05, 0x0b, 0x19, 0x17,
             0x76, 0x78, 0x6a, 0x64, 0x4e, 0x40, 0x52, 0x5c,
             0x06, 0x08, 0x1a, 0x14, 0x3e, 0x30, 0x22, 0x2c,
             0x96, 0x98, 0x8a, 0x84, 0xae, 0xa0, 0xb2, 0xbc,
             0xe6, 0xe8, 0xfa, 0xf4, 0xde, 0xd0, 0xc2, 0xcc,
             0x41, 0x4f, 0x5d, 0x53, 0x79, 0x77, 0x65, 0x6b,
             0x31, 0x3f, 0x2d, 0x23, 0x09, 0x07, 0x15, 0x1b,
             0xa1, 0xaf, 0xbd, 0xb3, 0x99, 0x97, 0x85, 0x8b,
             0xd1, 0xdf, 0xcd, 0xc3, 0xe9, 0xe7, 0xf5, 0xfb,
             0x9a, 0x94, 0x86, 0x88, 0xa2, 0xac, 0xbe, 0xb0,
             0xea, 0xe4, 0xf6, 0xf8, 0xd2, 0xdc, 0xce, 0xc0,
             0x7a, 0x74, 0x66, 0x68, 0x42, 0x4c, 0x5e, 0x50,
             0x0a, 0x04, 0x16, 0x18, 0x32, 0x3c, 0x2e, 0x20,
             0xec, 0xe2, 0xf0, 0xfe, 0xd4, 0xda, 0xc8, 0xc6,
             0x9c, 0x92, 0x80, 0x8e, 0xa4, 0xaa, 0xb8, 0xb6,
             0x0c, 0x02, 0x10, 0x1e, 0x34, 0x3a, 0x28, 0x26,
             0x7c, 0x72, 0x60, 0x6e, 0x44, 0x4a, 0x58, 0x56,
             0x37, 0x39, 0x2b, 0x25, 0x0f, 0x01, 0x13, 0x1d,
             0x47, 0x49, 0x5b, 0x55, 0x7f, 0x71, 0x63, 0x6d,
             0xd7, 0xd9, 0xcb, 0xc5, 0xef, 0xe1, 0xf3, 0xfd,
             0xa7, 0xa9, 0xbb, 0xb5, 0x9f, 0x91, 0x83, 0x8d]

GM9 = pyrtl.RomBlock(bitwidth=8, addrwidth=8, romdata=GM9_data, asynchronous=True)
GM11 = pyrtl.RomBlock(bitwidth=8, addrwidth=8, romdata=GM11_data, asynchronous=True)
GM13 = pyrtl.RomBlock(bitwidth=8, addrwidth=8, romdata=GM13_data, asynchronous=True)
GM14 = pyrtl.RomBlock(bitwidth=8, addrwidth=8, romdata=GM14_data, asynchronous=True)


# Hardware build.
aes_ciphertext = pyrtl.Input(bitwidth=128, name='aes_ciphertext')
aes_key = pyrtl.Input(bitwidth=128, name='aes_key')
aes_plaintext = pyrtl.Output(bitwidth=128, name='aes_plaintext')
aes_plaintext <<= aes_decryption(aes_ciphertext, aes_key)

sim_trace = pyrtl.SimulationTrace(wirevector_subset=[aes_ciphertext, aes_key, aes_plaintext])
sim = pyrtl.Simulation(tracer=sim_trace)

for cycle in range(1):
    sim.step({
        aes_ciphertext: 0x66e94bd4ef8a2c3b884cfa59ca342b2e,
        aes_key: 0x0
    })

sim_trace.render_trace(symbol_len=40, segment_size=1)
