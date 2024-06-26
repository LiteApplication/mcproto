from __future__ import annotations

import struct

import pytest

from mcproto.buffer import Buffer
from mcproto.types.nbt import (
    ByteArrayNBT,
    ByteNBT,
    CompoundNBT,
    DoubleNBT,
    EndNBT,
    FloatNBT,
    IntArrayNBT,
    IntNBT,
    ListNBT,
    LongArrayNBT,
    LongNBT,
    NBTag,
    NBTagType,
    PayloadType,
    ShortNBT,
    StringNBT,
)

# region EndNBT


def test_serialize_deserialize_end():
    """Test serialization/deserialization of NBT END tag."""
    output_bytes = EndNBT().serialize()
    assert output_bytes == bytearray.fromhex("00")

    buffer = Buffer()
    EndNBT().write_to(buffer)
    assert buffer == bytearray.fromhex("00")

    buffer.clear()
    EndNBT().write_to(buffer, with_name=False)
    assert buffer == bytearray.fromhex("00")

    buffer = Buffer(bytearray.fromhex("00"))
    assert NBTag.deserialize(buffer).TYPE == NBTagType.END


# endregion
# region Numerical NBT tests


@pytest.mark.parametrize(
    ("nbt_class", "value", "expected_bytes"),
    [
        (ByteNBT, 0, bytearray.fromhex("01 00")),
        (ByteNBT, 1, bytearray.fromhex("01 01")),
        (ByteNBT, 127, bytearray.fromhex("01 7F")),
        (ByteNBT, -128, bytearray.fromhex("01 80")),
        (ByteNBT, -1, bytearray.fromhex("01 FF")),
        (ByteNBT, 12, bytearray.fromhex("01 0C")),
        (ShortNBT, 0, bytearray.fromhex("02 00 00")),
        (ShortNBT, 1, bytearray.fromhex("02 00 01")),
        (ShortNBT, 32767, bytearray.fromhex("02 7F FF")),
        (ShortNBT, -32768, bytearray.fromhex("02 80 00")),
        (ShortNBT, -1, bytearray.fromhex("02 FF FF")),
        (ShortNBT, 12, bytearray.fromhex("02 00 0C")),
        (IntNBT, 0, bytearray.fromhex("03 00 00 00 00")),
        (IntNBT, 1, bytearray.fromhex("03 00 00 00 01")),
        (IntNBT, 2147483647, bytearray.fromhex("03 7F FF FF FF")),
        (IntNBT, -2147483648, bytearray.fromhex("03 80 00 00 00")),
        (IntNBT, -1, bytearray.fromhex("03 FF FF FF FF")),
        (IntNBT, 12, bytearray.fromhex("03 00 00 00 0C")),
        (LongNBT, 0, bytearray.fromhex("04 00 00 00 00 00 00 00 00")),
        (LongNBT, 1, bytearray.fromhex("04 00 00 00 00 00 00 00 01")),
        (LongNBT, (1 << 63) - 1, bytearray.fromhex("04 7F FF FF FF FF FF FF FF")),
        (LongNBT, -(1 << 63), bytearray.fromhex("04 80 00 00 00 00 00 00 00")),
        (LongNBT, -1, bytearray.fromhex("04 FF FF FF FF FF FF FF FF")),
        (LongNBT, 12, bytearray.fromhex("04 00 00 00 00 00 00 00 0C")),
        (FloatNBT, 1.0, bytearray.fromhex("05") + bytes(struct.pack(">f", 1.0))),
        (FloatNBT, 3.14, bytearray.fromhex("05") + bytes(struct.pack(">f", 3.14))),
        (FloatNBT, -1.0, bytearray.fromhex("05") + bytes(struct.pack(">f", -1.0))),
        (FloatNBT, 12.0, bytearray.fromhex("05") + bytes(struct.pack(">f", 12.0))),
        (DoubleNBT, 1.0, bytearray.fromhex("06") + bytes(struct.pack(">d", 1.0))),
        (DoubleNBT, 3.14, bytearray.fromhex("06") + bytes(struct.pack(">d", 3.14))),
        (DoubleNBT, -1.0, bytearray.fromhex("06") + bytes(struct.pack(">d", -1.0))),
        (DoubleNBT, 12.0, bytearray.fromhex("06") + bytes(struct.pack(">d", 12.0))),
        (ByteArrayNBT, b"", bytearray.fromhex("07 00 00 00 00")),
        (ByteArrayNBT, b"\x00", bytearray.fromhex("07 00 00 00 01") + b"\x00"),
        (ByteArrayNBT, b"\x00\x01", bytearray.fromhex("07 00 00 00 02") + b"\x00\x01"),
        (ByteArrayNBT, b"\x00\x01\x02", bytearray.fromhex("07 00 00 00 03") + b"\x00\x01\x02"),
        (ByteArrayNBT, b"\x00\x01\x02\x03", bytearray.fromhex("07 00 00 00 04") + b"\x00\x01\x02\x03"),
        (ByteArrayNBT, b"\xFF" * 1024, bytearray.fromhex("07 00 00 04 00") + b"\xFF" * 1024),
        (
            ByteArrayNBT,
            bytes((n - 1) * n * 2 % 256 for n in range(256)),
            bytearray.fromhex("07 00 00 01 00") + bytes((n - 1) * n * 2 % 256 for n in range(256)),
        ),
        (StringNBT, "", bytearray.fromhex("08 00 00")),
        (StringNBT, "test", bytearray.fromhex("08 00 04") + b"test"),
        (StringNBT, "a" * 100, bytearray.fromhex("08 00 64") + b"a" * (100)),
        (StringNBT, "&à@é", bytearray.fromhex("08 00 06") + bytes("&à@é", "utf-8")),
        (ListNBT, [], bytearray.fromhex("09 00 00 00 00 00")),
        (ListNBT, [ByteNBT(0)], bytearray.fromhex("09 01 00 00 00 01 00")),
        (ListNBT, [ShortNBT(127), ShortNBT(256)], bytearray.fromhex("09 02 00 00 00 02 00 7F 01 00")),
        (
            ListNBT,
            [ListNBT([ByteNBT(0)]), ListNBT([IntNBT(256)])],
            bytearray.fromhex("09 09 00 00 00 02 01 00 00 00 01 00 03 00 00 00 01 00 00 01 00"),
        ),
        (CompoundNBT, [], bytearray.fromhex("0A 00")),
        (
            CompoundNBT,
            [ByteNBT(0, name="test")],
            bytearray.fromhex("0A") + ByteNBT(0, name="test").serialize() + b"\x00",
        ),
        (
            CompoundNBT,
            [ShortNBT(128, "Short"), ByteNBT(-1, "Byte")],
            bytearray.fromhex("0A") + ShortNBT(128, "Short").serialize() + ByteNBT(-1, "Byte").serialize() + b"\x00",
        ),
        (
            CompoundNBT,
            [CompoundNBT([ByteNBT(0, name="Byte")], name="test")],
            bytearray.fromhex("0A") + CompoundNBT([ByteNBT(0, name="Byte")], name="test").serialize() + b"\x00",
        ),
        (
            CompoundNBT,
            [CompoundNBT([ByteNBT(0, name="Byte"), IntNBT(0, name="Int")], "test"), IntNBT(-1, "Int 2")],
            bytearray.fromhex("0A")
            + CompoundNBT([ByteNBT(0, name="Byte"), IntNBT(0, name="Int")], "test").serialize()
            + IntNBT(-1, "Int 2").serialize()
            + b"\x00",
        ),
        (IntArrayNBT, [], bytearray.fromhex("0B 00 00 00 00")),
        (IntArrayNBT, [0], bytearray.fromhex("0B 00 00 00 01 00 00 00 00")),
        (IntArrayNBT, [0, 1], bytearray.fromhex("0B 00 00 00 02 00 00 00 00 00 00 00 01")),
        (IntArrayNBT, [1, 2, 3], bytearray.fromhex("0B 00 00 00 03 00 00 00 01 00 00 00 02 00 00 00 03")),
        (IntArrayNBT, [(1 << 31) - 1], bytearray.fromhex("0B 00 00 00 01 7F FF FF FF")),
        (IntArrayNBT, [(1 << 31) - 1, (1 << 31) - 2], bytearray.fromhex("0B 00 00 00 02 7F FF FF FF 7F FF FF FE")),
        (IntArrayNBT, [-1, -2, -3], bytearray.fromhex("0B 00 00 00 03 FF FF FF FF FF FF FF FE FF FF FF FD")),
        (IntArrayNBT, [12] * 1024, bytearray.fromhex("0B 00 00 04 00") + b"\x00\x00\x00\x0C" * 1024),
        (LongArrayNBT, [], bytearray.fromhex("0C 00 00 00 00")),
        (LongArrayNBT, [0], bytearray.fromhex("0C 00 00 00 01 00 00 00 00 00 00 00 00")),
        (LongArrayNBT, [0, 1], bytearray.fromhex("0C 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01")),
        (
            LongArrayNBT,
            [1, 2, 3],
            bytearray.fromhex(
                "0C 00 00 00 03 00 00 00 00 00 00 00 01 00 00 00 00 00 00 00 02 00 00 00 00 00 00 00 03"
            ),
        ),
        (LongArrayNBT, [(1 << 63) - 1], bytearray.fromhex("0C 00 00 00 01 7F FF FF FF FF FF FF FF")),
        (
            LongArrayNBT,
            [(1 << 63) - 1, (1 << 63) - 2],
            bytearray.fromhex("0C 00 00 00 02 7F FF FF FF FF FF FF FF 7F FF FF FF FF FF FF FE"),
        ),
        (
            LongArrayNBT,
            [-1, -2, -3],
            bytearray.fromhex(
                "0C 00 00 00 03 FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FE FF FF FF FF FF FF FF FD"
            ),
        ),
        (LongArrayNBT, [12] * 1024, bytearray.fromhex("0C 00 00 04 00") + b"\x00\x00\x00\x00\x00\x00\x00\x0C" * 1024),
    ],
)
def test_serialize_deserialize_noname(nbt_class: type[NBTag], value: PayloadType, expected_bytes: bytes):
    """Test serialization/deserialization of NBT tag without name."""
    # Test serialization
    output_bytes = nbt_class(value).serialize(with_name=False)
    output_bytes_no_type = nbt_class(value).serialize(with_type=False, with_name=False)
    assert output_bytes == expected_bytes
    assert output_bytes_no_type == expected_bytes[1:]

    buffer = Buffer()
    nbt_class(value).write_to(buffer, with_name=False)
    assert buffer == expected_bytes

    # Test deserialization
    buffer = Buffer(expected_bytes)
    assert NBTag.deserialize(buffer, with_name=False) == nbt_class(value)

    buffer = Buffer(expected_bytes[1:])
    assert nbt_class.deserialize(buffer, with_type=False, with_name=False) == nbt_class(value)

    buffer = Buffer(expected_bytes)
    assert nbt_class.read_from(buffer, with_name=False) == nbt_class(value)

    buffer = Buffer(expected_bytes[1:])
    assert nbt_class.read_from(buffer, with_type=False, with_name=False) == nbt_class(value)


@pytest.mark.parametrize(
    ("nbt_class", "value", "name", "expected_bytes"),
    [
        (ByteNBT, 0, "test", bytearray.fromhex("01") + b"\x00\x04test" + bytearray.fromhex("00")),
        (ByteNBT, 1, "a", bytearray.fromhex("01") + b"\x00\x01a" + bytearray.fromhex("01")),
        (ByteNBT, 127, "&à@é", bytearray.fromhex("01 00 06") + bytes("&à@é", "utf-8") + bytearray.fromhex("7F")),
        (ByteNBT, -128, "test", bytearray.fromhex("01") + b"\x00\x04test" + bytearray.fromhex("80")),
        (ByteNBT, 12, "a" * 100, bytearray.fromhex("01") + b"\x00\x64" + b"a" * 100 + bytearray.fromhex("0C")),
        (ShortNBT, 0, "test", bytearray.fromhex("02") + b"\x00\x04test" + bytearray.fromhex("00 00")),
        (ShortNBT, 1, "a", bytearray.fromhex("02") + b"\x00\x01a" + bytearray.fromhex("00 01")),
        (ShortNBT, 32767, "&à@é", bytearray.fromhex("02 00 06") + bytes("&à@é", "utf-8") + bytearray.fromhex("7F FF")),
        (ShortNBT, -32768, "test", bytearray.fromhex("02") + b"\x00\x04test" + bytearray.fromhex("80 00")),
        (ShortNBT, 12, "a" * 100, bytearray.fromhex("02") + b"\x00\x64" + b"a" * 100 + bytearray.fromhex("00 0C")),
        (IntNBT, 0, "test", bytearray.fromhex("03") + b"\x00\x04test" + bytearray.fromhex("00 00 00 00")),
        (IntNBT, 1, "a", bytearray.fromhex("03") + b"\x00\x01a" + bytearray.fromhex("00 00 00 01")),
        (
            IntNBT,
            2147483647,
            "&à@é",
            bytearray.fromhex("03 00 06") + bytes("&à@é", "utf-8") + bytearray.fromhex("7F FF FF FF"),
        ),
        (IntNBT, -2147483648, "test", bytearray.fromhex("03") + b"\x00\x04test" + bytearray.fromhex("80 00 00 00")),
        (
            IntNBT,
            12,
            "a" * 100,
            bytearray.fromhex("03") + b"\x00\x64" + b"a" * 100 + bytearray.fromhex("00 00 00 0C"),
        ),
        (LongNBT, 0, "test", bytearray.fromhex("04") + b"\x00\x04test" + bytearray.fromhex("00 00 00 00 00 00 00 00")),
        (LongNBT, 1, "a", bytearray.fromhex("04") + b"\x00\x01a" + bytearray.fromhex("00 00 00 00 00 00 00 01")),
        (
            LongNBT,
            (1 << 63) - 1,
            "&à@é",
            bytearray.fromhex("04 00 06") + bytes("&à@é", "utf-8") + bytearray.fromhex("7F FF FF FF FF FF FF FF"),
        ),
        (
            LongNBT,
            -1 << 63,
            "test",
            bytearray.fromhex("04") + b"\x00\x04test" + bytearray.fromhex("80 00 00 00 00 00 00 00"),
        ),
        (
            LongNBT,
            12,
            "a" * 100,
            bytearray.fromhex("04") + b"\x00\x64" + b"a" * 100 + bytearray.fromhex("00 00 00 00 00 00 00 0C"),
        ),
        (FloatNBT, 1.0, "test", bytearray.fromhex("05") + b"\x00\x04test" + bytes(struct.pack(">f", 1.0))),
        (FloatNBT, 3.14, "a", bytearray.fromhex("05") + b"\x00\x01a" + bytes(struct.pack(">f", 3.14))),
        (
            FloatNBT,
            -1.0,
            "&à@é",
            bytearray.fromhex("05 00 06") + bytes("&à@é", "utf-8") + bytes(struct.pack(">f", -1.0)),
        ),
        (FloatNBT, 12.0, "test", bytearray.fromhex("05") + b"\x00\x04test" + bytes(struct.pack(">f", 12.0))),
        (DoubleNBT, 1.0, "test", bytearray.fromhex("06") + b"\x00\x04test" + bytes(struct.pack(">d", 1.0))),
        (DoubleNBT, 3.14, "a", bytearray.fromhex("06") + b"\x00\x01a" + bytes(struct.pack(">d", 3.14))),
        (
            DoubleNBT,
            -1.0,
            "&à@é",
            bytearray.fromhex("06 00 06") + bytes("&à@é", "utf-8") + bytes(struct.pack(">d", -1.0)),
        ),
        (DoubleNBT, 12.0, "test", bytearray.fromhex("06") + b"\x00\x04test" + bytes(struct.pack(">d", 12.0))),
        (ByteArrayNBT, b"", "test", bytearray.fromhex("07") + b"\x00\x04test" + bytearray.fromhex("00 00 00 00")),
        (
            ByteArrayNBT,
            b"\x00",
            "a",
            bytearray.fromhex("07") + b"\x00\x01a" + bytearray.fromhex("00 00 00 01") + b"\x00",
        ),
        (
            ByteArrayNBT,
            b"\x00\x01",
            "&à@é",
            bytearray.fromhex("07 00 06") + bytes("&à@é", "utf-8") + bytearray.fromhex("00 00 00 02") + b"\x00\x01",
        ),
        (
            ByteArrayNBT,
            b"\x00\x01\x02",
            "test",
            bytearray.fromhex("07") + b"\x00\x04test" + bytearray.fromhex("00 00 00 03") + b"\x00\x01\x02",
        ),
        (
            ByteArrayNBT,
            b"\xFF" * 1024,
            "a" * 100,
            bytearray.fromhex("07") + b"\x00\x64" + b"a" * 100 + bytearray.fromhex("00 00 04 00") + b"\xFF" * 1024,
        ),
        (StringNBT, "", "test", bytearray.fromhex("08") + b"\x00\x04test" + bytearray.fromhex("00 00")),
        (StringNBT, "test", "a", bytearray.fromhex("08") + b"\x00\x01a" + bytearray.fromhex("00 04") + b"test"),
        (
            StringNBT,
            "a" * 100,
            "&à@é",
            bytearray.fromhex("08 00 06") + bytes("&à@é", "utf-8") + bytearray.fromhex("00 64") + b"a" * 100,
        ),
        (
            StringNBT,
            "&à@é",
            "test",
            bytearray.fromhex("08") + b"\x00\x04test" + bytearray.fromhex("00 06") + bytes("&à@é", "utf-8"),
        ),
        (ListNBT, [], "test", bytearray.fromhex("09") + b"\x00\x04test" + bytearray.fromhex("00 00 00 00 00")),
        (
            ListNBT,
            [ByteNBT(-1)],
            "a",
            bytearray.fromhex("09") + b"\x00\x01a" + bytearray.fromhex("01 00 00 00 01 FF"),
        ),
        (
            ListNBT,
            [ShortNBT(127), ShortNBT(256)],
            "test",
            bytearray.fromhex("09") + b"\x00\x04test" + bytearray.fromhex("02 00 00 00 02 00 7F 01 00"),
        ),
        (
            ListNBT,
            [ListNBT([ByteNBT(-1)]), ListNBT([IntNBT(256)])],
            "a",
            bytearray.fromhex("09")
            + b"\x00\x01a"
            + bytearray.fromhex("09 00 00 00 02 01 00 00 00 01 FF 03 00 00 00 01 00 00 01 00"),
        ),
        (CompoundNBT, [], "test", bytearray.fromhex("0A") + b"\x00\x04test" + bytearray.fromhex("00")),
        (
            CompoundNBT,
            [ByteNBT(0, name="Byte")],
            "test",
            bytearray.fromhex("0A") + b"\x00\x04test" + ByteNBT(0, name="Byte").serialize() + b"\x00",
        ),
        (
            CompoundNBT,
            [ShortNBT(128, "Short"), ByteNBT(-1, "Byte")],
            "test",
            bytearray.fromhex("0A")
            + b"\x00\x04test"
            + ShortNBT(128, "Short").serialize()
            + ByteNBT(-1, "Byte").serialize()
            + b"\x00",
        ),
        (
            CompoundNBT,
            [CompoundNBT([ByteNBT(0, name="Byte")], name="test")],
            "test",
            bytearray.fromhex("0A")
            + b"\x00\x04test"
            + CompoundNBT([ByteNBT(0, name="Byte")], "test").serialize()
            + b"\x00",
        ),
        (
            CompoundNBT,
            [ListNBT([ByteNBT(0)], name="List")],
            "test",
            bytearray.fromhex("0A") + b"\x00\x04test" + ListNBT([ByteNBT(0)], name="List").serialize() + b"\x00",
        ),
        (IntArrayNBT, [], "test", bytearray.fromhex("0B") + b"\x00\x04test" + bytearray.fromhex("00 00 00 00")),
        (
            IntArrayNBT,
            [0],
            "a",
            bytearray.fromhex("0B") + b"\x00\x01a" + bytearray.fromhex("00 00 00 01") + b"\x00\x00\x00\x00",
        ),
        (
            IntArrayNBT,
            [0, 1],
            "&à@é",
            bytearray.fromhex("0B 00 06")
            + bytes("&à@é", "utf-8")
            + bytearray.fromhex("00 00 00 02")
            + b"\x00\x00\x00\x00\x00\x00\x00\x01",
        ),
        (
            IntArrayNBT,
            [1, 2, 3],
            "test",
            bytearray.fromhex("0B")
            + b"\x00\x04test"
            + bytearray.fromhex("00 00 00 03")
            + b"\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03",
        ),
        (
            IntArrayNBT,
            [(1 << 31) - 1],
            "a" * 100,
            bytearray.fromhex("0B")
            + b"\x00\x64"
            + b"a" * 100
            + bytearray.fromhex("00 00 00 01")
            + b"\x7F\xFF\xFF\xFF",
        ),
        (LongArrayNBT, [], "test", bytearray.fromhex("0C") + b"\x00\x04test" + bytearray.fromhex("00 00 00 00")),
        (
            LongArrayNBT,
            [0],
            "a",
            bytearray.fromhex("0C")
            + b"\x00\x01a"
            + bytearray.fromhex("00 00 00 01")
            + b"\x00\x00\x00\x00\x00\x00\x00\x00",
        ),
        (
            LongArrayNBT,
            [0, 1],
            "&à@é",
            bytearray.fromhex("0C 00 06")
            + bytes("&à@é", "utf-8")
            + bytearray.fromhex("00 00 00 02")
            + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01",
        ),
        (
            LongArrayNBT,
            [1, 2, 3],
            "test",
            bytearray.fromhex("0C")
            + b"\x00\x04test"
            + bytearray.fromhex("00 00 00 03")
            + bytearray.fromhex("00 00 00 00 00 00 00 01 00 00 00 00 00 00 00 02 00 00 00 00 00 00 00 03"),
        ),
        (
            LongArrayNBT,
            [(1 << 63) - 1] * 100,
            "a" * 100,
            bytearray.fromhex("0C")
            + b"\x00\x64"
            + b"a" * 100
            + bytearray.fromhex("00 00 00 64")
            + b"\x7F\xFF\xFF\xFF\xFF\xFF\xFF\xFF" * 100,
        ),
    ],
)
def test_serialize_deserialize(nbt_class: type[NBTag], value: PayloadType, name: str, expected_bytes: bytes):
    """Test serialization/deserialization of NBT tag with name."""
    # Test serialization
    output_bytes = nbt_class(value, name).serialize()
    output_bytes_no_type = nbt_class(value, name).serialize(with_type=False)
    assert output_bytes == expected_bytes
    assert output_bytes_no_type == expected_bytes[1:]

    buffer = Buffer()
    nbt_class(value, name).write_to(buffer)
    assert buffer == expected_bytes

    # Test deserialization
    buffer = Buffer(expected_bytes * 2)
    assert buffer.remaining == len(expected_bytes) * 2
    assert NBTag.deserialize(buffer) == nbt_class(value, name=name)
    assert buffer.remaining == len(expected_bytes)
    assert NBTag.deserialize(buffer) == nbt_class(value, name=name)
    assert buffer.remaining == 0

    buffer = Buffer(expected_bytes[1:])
    assert nbt_class.deserialize(buffer, with_type=False) == nbt_class(value, name=name)

    buffer = Buffer(expected_bytes)
    assert nbt_class.read_from(buffer) == nbt_class(value, name=name)

    buffer = Buffer(expected_bytes[1:])
    assert nbt_class.read_from(buffer, with_type=False) == nbt_class(value, name=name)


@pytest.mark.parametrize(
    ("nbt_class", "size", "tag"),
    [
        (ByteNBT, 8, NBTagType.BYTE),
        (ShortNBT, 16, NBTagType.SHORT),
        (IntNBT, 32, NBTagType.INT),
        (LongNBT, 64, NBTagType.LONG),
    ],
)
def test_serialize_deserialize_numerical_fail(nbt_class: type[NBTag], size: int, tag: NBTagType):
    """Test serialization/deserialization of NBT NUM tag with invalid value."""
    # Out of bounds
    with pytest.raises(OverflowError):
        nbt_class(1 << (size - 1)).serialize(with_name=False)

    with pytest.raises(OverflowError):
        nbt_class(-(1 << (size - 1)) - 1).serialize(with_name=False)

    with pytest.raises(ValueError):  # No name
        nbt_class(0, "").serialize()  # without with_name=False

    # Deserialization
    buffer = Buffer(bytearray([tag.value + 1] + [0] * (size // 8)))
    with pytest.raises(TypeError):  # Tries to read a nbt_class, but it's one higher
        nbt_class.deserialize(buffer, with_name=False)

    # Not enough data
    buffer = Buffer(bytearray([tag.value] + [0] * ((size // 8) - 1)))
    with pytest.raises(IOError):
        nbt_class.read_from(buffer, with_name=False)

    buffer = Buffer(bytearray([tag.value, 0, 0] + [0] * (size // 8)))
    assert nbt_class.read_from(buffer, with_name=True) == nbt_class(0)


# endregion

# region FloatNBT


def test_serialize_deserialize_float_fail():
    """Test serialization/deserialization of NBT FLOAT tag with invalid value."""
    with pytest.raises(ValueError):
        FloatNBT(0, 0).serialize()  # type:ignore

    with pytest.raises(struct.error):
        FloatNBT("test").serialize(with_name=False)

    with pytest.raises(OverflowError):
        FloatNBT(1e39, "test").serialize()

    with pytest.raises(OverflowError):
        FloatNBT(-1e39, "test").serialize()

    # Deserialization
    buffer = Buffer(bytearray([NBTagType.BYTE] + [0] * 4))
    with pytest.raises(TypeError):  # Tries to read a FloatNBT, but it's a ByteNBT
        FloatNBT.deserialize(buffer, with_name=False)

    # Not enough data
    buffer = Buffer(bytearray([NBTagType.FLOAT, 0, 0, 0]))
    with pytest.raises(IOError):
        FloatNBT.read_from(buffer, with_name=False)


# endregion
# region DoubleNBT


def test_serialize_deserialize_double_fail():
    """Test serialization/deserialization of NBT DOUBLE tag with invalid value."""
    with pytest.raises(ValueError):
        DoubleNBT(0, 0).serialize()  # type: ignore

    with pytest.raises(struct.error):
        DoubleNBT("test").serialize(with_name=False)

    # Deserialization
    buffer = Buffer(bytearray([0x01] + [0] * 8))
    with pytest.raises(TypeError):  # Tries to read a DoubleNBT, but it's a ByteNBT
        DoubleNBT.deserialize(buffer, with_name=False)

    # Not enough data
    buffer = Buffer(bytearray([NBTagType.DOUBLE, 0, 0, 0, 0, 0, 0, 0]))
    with pytest.raises(IOError):
        DoubleNBT.read_from(buffer, with_name=False)


# endregion
# region ByteArrayNBT


def test_serialize_deserialize_bytearray_fail():
    """Test serialization/deserialization of NBT BYTEARRAY tag with invalid value."""
    with pytest.raises(ValueError):
        ByteArrayNBT([], 0).serialize()  # type:ignore

    with pytest.raises(ValueError):
        ByteArrayNBT(b"test", "").serialize()

    # Deserialization
    buffer = Buffer(bytearray([0x01] + [0] * 4))
    with pytest.raises(TypeError):  # Tries to read a ByteArrayNBT, but it's a ByteNBT
        ByteArrayNBT.deserialize(buffer, with_name=False)

    # Not enough data
    buffer = Buffer(bytearray([NBTagType.BYTE_ARRAY, 0, 0, 0]))  # Missing length bytes
    with pytest.raises(IOError):
        ByteArrayNBT.read_from(buffer, with_name=False)

    # Not enough data
    buffer = Buffer(bytearray([NBTagType.BYTE_ARRAY, 0, 0, 0, 1]))  # Missing data bytes
    with pytest.raises(IOError):
        ByteArrayNBT.read_from(buffer, with_name=False)

    # Not enough data
    buffer = Buffer(bytearray([NBTagType.BYTE_ARRAY, 0, 0, 0, 2, 0]))  # Missing data bytes
    with pytest.raises(IOError):
        ByteArrayNBT.read_from(buffer, with_name=False)

    # Negative length
    buffer = Buffer(bytearray([NBTagType.BYTE_ARRAY, 0xFF, 0xFF, 0xFF, 0xFF]))  # length = -1
    with pytest.raises(ValueError):
        ByteArrayNBT.deserialize(buffer, with_name=False)


# endregion
# region StringNBT


def test_serialize_deserialize_string_fail():
    """Test serialization/deserialization of NBT STRING tag with invalid value."""
    with pytest.raises(ValueError):
        StringNBT("", 0).serialize()  # type:ignore

    with pytest.raises(ValueError):
        StringNBT("test", "").serialize()

    # Deserialization
    buffer = Buffer(bytearray([0x01, 0, 0]))
    with pytest.raises(TypeError):  # Tries to read a StringNBT, but it's a ByteNBT
        StringNBT.deserialize(buffer, with_name=False)

    # Not enough data for the length
    buffer = Buffer(bytearray([NBTagType.STRING, 0]))
    with pytest.raises(IOError):
        StringNBT.read_from(buffer, with_name=False)

    # Not enough data
    buffer = Buffer(bytearray([NBTagType.STRING, 0, 1]))
    with pytest.raises(IOError):
        StringNBT.read_from(buffer, with_name=False)

    # Not enough data
    buffer = Buffer(bytearray([NBTagType.STRING, 0, 2, 0]))
    with pytest.raises(IOError):
        StringNBT.read_from(buffer, with_name=False)

    # Negative length
    buffer = Buffer(bytearray([NBTagType.STRING, 0xFF, 0xFF]))  # length = -1
    with pytest.raises(ValueError):
        StringNBT.deserialize(buffer, with_name=False)

    # Invalid UTF-8
    buffer = Buffer(bytearray([NBTagType.STRING, 0, 1, 0xC0, 0x80]))
    with pytest.raises(UnicodeDecodeError):
        StringNBT.read_from(buffer, with_name=False)


# endregion
# region ListNBT


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ([ByteNBT(0), IntNBT(0)], ValueError),
        ([ByteNBT(0), "test"], ValueError),
        ([ByteNBT(0), None], ValueError),
        ([ByteNBT(0), ByteNBT(-1, "Hello World")], ValueError),  # All unnamed tags
        ([ByteNBT(128), ByteNBT(-1)], OverflowError),  # Check for error propagation
    ],
)
def test_serialize_list_fail(payload, error):
    """Test serialization of NBT LIST tag with invalid value."""
    with pytest.raises(error):
        ListNBT(payload, "test").serialize()


def test_deserialize_list_fail():
    """Test deserialization of NBT LIST tag with invalid value."""
    # Wrong tag type
    buffer = Buffer(bytearray([0x09, 255, 0, 0, 0, 1, 0]))
    with pytest.raises(TypeError):
        ListNBT.deserialize(buffer, with_name=False)

    # Not enough data
    buffer = Buffer(bytearray([0x09, 1, 0, 0, 0, 1]))
    with pytest.raises(IOError):
        ListNBT.read_from(buffer, with_name=False)

    # Not enough data
    buffer = Buffer(bytearray([0x09, 1, 0, 0, 0]))
    with pytest.raises(IOError):
        ListNBT.read_from(buffer, with_name=False)


# endregion
# region CompoundNBT


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ([ByteNBT(0, name="Hello"), IntNBT(0)], ValueError),
        ([ByteNBT(0, name="hi"), "test"], ValueError),
        ([ByteNBT(0, name="hi"), None], ValueError),
        ([ByteNBT(0), ByteNBT(-1, "Hello World")], ValueError),  # All unnamed tags
        ([ByteNBT(128, name="Jello"), ByteNBT(-1, name="Bonjour")], OverflowError),  # Check for error propagation
    ],
)
def test_serialize_compound_fail(payload, error):
    """Test serialization of NBT COMPOUND tag with invalid value."""
    with pytest.raises(error):
        CompoundNBT(payload, "test").serialize()

    # Double name
    with pytest.raises(ValueError):
        CompoundNBT([ByteNBT(0, name="test"), ByteNBT(0, name="test")], "comp").serialize()


def test_deseialize_compound_fail():
    """Test deserialization of NBT COMPOUND tag with invalid value."""
    # Not enough data
    buffer = Buffer(bytearray([NBTagType.COMPOUND, 0x01]))
    with pytest.raises(IOError):
        CompoundNBT.read_from(buffer, with_name=False)

    # Not enough data
    buffer = Buffer(bytearray([NBTagType.COMPOUND]))
    with pytest.raises(IOError):
        CompoundNBT.read_from(buffer, with_name=False)

    # Wrong tag type
    buffer = Buffer(bytearray([15]))
    with pytest.raises(TypeError):
        NBTag.deserialize(buffer)


def test_to_object_compound():
    """Try a few incorrect CompoundNBT.to_object() calls."""
    comp = CompoundNBT([ByteNBT(0, "test"), ByteNBT(1, "test")])
    with pytest.raises(ValueError):
        comp.to_object()  # Duplicate name

    comp = CompoundNBT([ByteNBT(0), ByteNBT(1)])
    with pytest.raises(ValueError):
        comp.to_object()


def test_equality_compound():
    """Test equality of CompoundNBT."""
    comp1 = CompoundNBT([ByteNBT(0, name="test"), ByteNBT(1, name="test2"), ByteNBT(2, name="test3")], "comp")
    comp2 = CompoundNBT([ByteNBT(0, name="test"), ByteNBT(1, name="test2"), ByteNBT(2, name="test3")], "comp")
    assert comp1 == comp2

    comp2 = CompoundNBT([ByteNBT(0, name="test"), ByteNBT(1, name="test2")], "comp")
    assert comp1 != comp2

    comp2 = CompoundNBT([ByteNBT(0, name="test"), ByteNBT(1, name="test2"), ByteNBT(2, name="test4")], "comp")
    assert comp1 != comp2

    comp2 = CompoundNBT([ByteNBT(0, name="test"), ByteNBT(1, name="test2"), ByteNBT(2, name="test3")], "comp2")
    assert comp1 != comp2

    assert comp1 != ByteNBT(0, name="comp")


# endregion
# region IntArrayNBT


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ([0, "test"], ValueError),
        ([0, None], ValueError),
        ([0, 1 << 31], OverflowError),
        ([0, -(1 << 31) - 1], OverflowError),
    ],
)
def test_serialize_intarray_fail(payload, error):
    """Test serialization of NBT INTARRAY tag with invalid value."""
    with pytest.raises(error):
        IntArrayNBT(payload, "test").serialize()


def test_deserialize_intarray_fail():
    """Test deserialization of NBT INTARRAY tag with invalid value."""
    # Not enough data for 1 element
    buffer = Buffer(bytearray([0x0B, 0, 0, 0, 1, 0, 0, 0]))
    with pytest.raises(IOError):
        IntArrayNBT.deserialize(buffer, with_name=False)

    # Not enough data for the size
    buffer = Buffer(bytearray([0x0B, 0, 0, 0]))
    with pytest.raises(IOError):
        IntArrayNBT.read_from(buffer, with_name=False)

    # Not enough data to start the 2nd element
    buffer = Buffer(bytearray([0x0B, 0, 0, 0, 2, 1, 0, 0, 0]))
    with pytest.raises(IOError):
        IntArrayNBT.read_from(buffer, with_name=False)


# endregion
# region LongArrayNBT


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ([0, "test"], ValueError),
        ([0, None], ValueError),
        ([0, 1 << 63], OverflowError),
        ([0, -(1 << 63) - 1], OverflowError),
    ],
)
def test_serialize_deserialize_longarray_fail(payload, error):
    """Test serialization/deserialization of NBT LONGARRAY tag with invalid value."""
    with pytest.raises(error):
        LongArrayNBT(payload, "test").serialize()


def test_deserialize_longarray_fail():
    """Test deserialization of NBT LONGARRAY tag with invalid value."""
    # Not enough data for 1 element
    buffer = Buffer(bytearray([0x0C, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]))
    with pytest.raises(IOError):
        LongArrayNBT.deserialize(buffer, with_name=False)

    # Not enough data for the size
    buffer = Buffer(bytearray([0x0C, 0, 0, 0]))
    with pytest.raises(IOError):
        LongArrayNBT.read_from(buffer, with_name=False)

    # Not enough data to start the 2nd element
    buffer = Buffer(bytearray([0x0C, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0]))
    with pytest.raises(IOError):
        LongArrayNBT.read_from(buffer, with_name=False)


# endregion

# region NBTag


def test_nbt_helloworld():
    """Test serialization/deserialization of a simple NBT tag.

    Source data: https://wiki.vg/NBT#Example.
    """
    data = bytearray.fromhex("0a000b68656c6c6f20776f726c640800046e616d65000942616e616e72616d6100")
    buffer = Buffer(data)

    expected_object = {
        "hello world": {
            "name": "Bananrama",
        }
    }

    data = CompoundNBT.deserialize(buffer)
    assert data == NBTag.from_object(expected_object)
    assert data.to_object() == expected_object


def test_nbt_bigfile():
    """Test serialization/deserialization of a big NBT tag.

    Slighly modified from the source data to also include a IntArrayNBT and a LongArrayNBT.
    Source data: https://wiki.vg/NBT#Example.
    """
    data = "0a00054c6576656c0400086c6f6e67546573747fffffffffffffff02000973686f7274546573747fff08000a737472696e6754657374002948454c4c4f20574f524c4420544849532049532041205445535420535452494e4720c385c384c39621050009666c6f6174546573743eff1832030007696e74546573747fffffff0a00146e657374656420636f6d706f756e6420746573740a000368616d0800046e616d65000648616d70757305000576616c75653f400000000a00036567670800046e616d6500074567676265727405000576616c75653f00000000000c000f6c6973745465737420286c6f6e672900000005000000000000000b000000000000000c000000000000000d000000000000000e7fffffffffffffff0b000e6c697374546573742028696e7429000000047fffffff7ffffffe7ffffffd7ffffffc0900136c697374546573742028636f6d706f756e64290a000000020800046e616d65000f436f6d706f756e642074616720233004000a637265617465642d6f6e000001265237d58d000800046e616d65000f436f6d706f756e642074616720233104000a637265617465642d6f6e000001265237d58d0001000862797465546573747f07006562797465417272617954657374202874686520666972737420313030302076616c756573206f6620286e2a6e2a3235352b6e2a3729253130302c207374617274696e672077697468206e3d302028302c2036322c2033342c2031362c20382c202e2e2e2929000003e8003e2210080a162c4c12462004564e505c0e2e5828024a3830323e54103a0a482c1a12142036561c502a0e60585a02183862320c54423a3c485e1a44145236241c1e2a4060265a34180662000c2242083c165e4c44465204244e1e5c402e2628344a0630003e2210080a162c4c12462004564e505c0e2e5828024a3830323e54103a0a482c1a12142036561c502a0e60585a02183862320c54423a3c485e1a44145236241c1e2a4060265a34180662000c2242083c165e4c44465204244e1e5c402e2628344a0630003e2210080a162c4c12462004564e505c0e2e5828024a3830323e54103a0a482c1a12142036561c502a0e60585a02183862320c54423a3c485e1a44145236241c1e2a4060265a34180662000c2242083c165e4c44465204244e1e5c402e2628344a0630003e2210080a162c4c12462004564e505c0e2e5828024a3830323e54103a0a482c1a12142036561c502a0e60585a02183862320c54423a3c485e1a44145236241c1e2a4060265a34180662000c2242083c165e4c44465204244e1e5c402e2628344a0630003e2210080a162c4c12462004564e505c0e2e5828024a3830323e54103a0a482c1a12142036561c502a0e60585a02183862320c54423a3c485e1a44145236241c1e2a4060265a34180662000c2242083c165e4c44465204244e1e5c402e2628344a0630003e2210080a162c4c12462004564e505c0e2e5828024a3830323e54103a0a482c1a12142036561c502a0e60585a02183862320c54423a3c485e1a44145236241c1e2a4060265a34180662000c2242083c165e4c44465204244e1e5c402e2628344a0630003e2210080a162c4c12462004564e505c0e2e5828024a3830323e54103a0a482c1a12142036561c502a0e60585a02183862320c54423a3c485e1a44145236241c1e2a4060265a34180662000c2242083c165e4c44465204244e1e5c402e2628344a0630003e2210080a162c4c12462004564e505c0e2e5828024a3830323e54103a0a482c1a12142036561c502a0e60585a02183862320c54423a3c485e1a44145236241c1e2a4060265a34180662000c2242083c165e4c44465204244e1e5c402e2628344a0630003e2210080a162c4c12462004564e505c0e2e5828024a3830323e54103a0a482c1a12142036561c502a0e60585a02183862320c54423a3c485e1a44145236241c1e2a4060265a34180662000c2242083c165e4c44465204244e1e5c402e2628344a0630003e2210080a162c4c12462004564e505c0e2e5828024a3830323e54103a0a482c1a12142036561c502a0e60585a02183862320c54423a3c485e1a44145236241c1e2a4060265a34180662000c2242083c165e4c44465204244e1e5c402e2628344a063005000a646f75626c65546573743efc7b5e00"  # noqa: E501
    data = bytearray.fromhex(data)
    buffer = Buffer(data)

    expected_object = {
        "Level": {
            "longTest": 9223372036854775807,
            "shortTest": 32767,
            "stringTest": "HELLO WORLD THIS IS A TEST STRING ÅÄÖ!",
            "floatTest": 0.4982314705848694,
            "intTest": 2147483647,
            "nested compound test": {
                "ham": {"name": "Hampus", "value": 0.75},
                "egg": {"name": "Eggbert", "value": 0.5},
            },
            "listTest (long)": [11, 12, 13, 14, 9223372036854775807],
            "listTest (int)": [2147483647, 2147483646, 2147483645, 2147483644],
            "listTest (compound)": [
                {"name": "Compound tag #0", "created-on": 1264099775885},
                {"name": "Compound tag #1", "created-on": 1264099775885},
            ],
            "byteTest": 127,
            "byteArrayTest (the first 1000 values of (n*n*255+n*7)%100"
            ", starting with n=0 (0, 62, 34, 16, 8, ...))": bytearray(
                (n * n * 255 + n * 7) % 100 for n in range(1000)
            ),
            "doubleTest": 0.4931287132182315,
        }
    }

    data = CompoundNBT.deserialize(buffer)
    # print(f"{data=}\n{expected_object=}\n{data.to_object()=}\n{NBTag.from_object(expected_object)=}")

    def check_equality(self, other):
        """Check if two objects are equal, with deep epsilon check for floats."""
        if type(self) != type(other):
            return False
        if isinstance(self, dict):
            if len(self) != len(other):
                return False
            for key in self:
                if key not in other:
                    return False
                if not check_equality(self[key], other[key]):
                    return False
            return True
        if isinstance(self, list):
            if len(self) != len(other):
                return False
            return all(check_equality(self[i], other[i]) for i in range(len(self)))
        if isinstance(self, float):
            return abs(self - other) < 1e-6
        if self != other:
            return False
        return self == other

    assert data == NBTag.from_object(expected_object)
    assert check_equality(data.to_object(), expected_object)


# endregion
# region Edge cases


def test_from_object_lst_not_same_type():
    """Test from_object with a list that does not have the same type."""
    with pytest.raises(TypeError):
        NBTag.from_object([ByteNBT(0), IntNBT(0)])


def test_from_object_out_of_bounds():
    """Test from_object with a value that is out of bounds."""
    with pytest.raises(ValueError):
        NBTag.from_object({"test": 1 << 63})

    with pytest.raises(ValueError):
        NBTag.from_object({"test": -(1 << 63) - 1})

    with pytest.raises(ValueError):
        NBTag.from_object({"test": [1 << 63]})

    with pytest.raises(ValueError):
        NBTag.from_object({"test": [-(1 << 63) - 1]})


def test_from_object_morecases():
    """Test from_object with more edge cases."""

    class CustomType:
        def __bytes__(self):
            return b"test"

    assert NBTag.from_object(
        {
            "nbtag": ByteNBT(0),  # ByteNBT
            "bytearray": b"test",  # Conversion from bytes
            "empty_list": [],  # Empty list with type EndNBT
            "empty_compound": {},  # Empty compound
            "end_NBTag": None,  # Should not be done in practice, would create a broken buffer if serialized
            "custom": CustomType(),  # Custom type with __bytes__ method
        }
    ) == CompoundNBT(
        [  # Order is shuffled because the spec does not require a specific order
            CompoundNBT([], "empty_compound"),
            ByteArrayNBT(b"test", "bytearray"),
            ByteArrayNBT(b"test", "custom"),
            ListNBT([], "empty_list"),
            ByteNBT(0, "nbtag"),
            EndNBT(),
        ]
    )

    # Not a valid object
    with pytest.raises(TypeError):
        NBTag.from_object({"test": object()})

    compound = CompoundNBT.from_object(
        {
            "test": ByteNBT(0),
            "test2": IntNBT(0),
        },
        name="compound",
    )
    assert compound["test"] == ByteNBT(0, "test")
    assert compound["test2"] == IntNBT(0, "test2")
    with pytest.raises(KeyError):
        compound["test3"]

    # Cannot index into a ByteNBT
    with pytest.raises(TypeError):
        compound["test"][0]  # type:ignore

    listnbt = ListNBT.from_object([0, 1, 2], use_int_array=False)
    assert listnbt[0] == ByteNBT(0)
    assert listnbt[1] == ByteNBT(1)
    assert listnbt[2] == ByteNBT(2)
    with pytest.raises(IndexError):
        listnbt[3]
    with pytest.raises(TypeError):
        listnbt["hello"]

    assert listnbt[-1] == ByteNBT(2)
    assert listnbt[-2] == ByteNBT(1)
    assert listnbt[-3] == ByteNBT(0)

    with pytest.raises(TypeError):
        listnbt[object()]  # type:ignore

    assert listnbt.value == [0, 1, 2]
    assert listnbt.to_object() == [0, 1, 2]
    assert ListNBT([]).value == []
    assert compound.to_object() == {"compound": {"test": 0, "test2": 0}}
    assert compound.value == {"test": 0, "test2": 0}
    assert ListNBT([IntNBT(0)]).value == [0]

    assert ByteNBT(12).value == 12
    assert ShortNBT(13).value == 13
    assert IntNBT(14).value == 14
    assert LongNBT(15).value == 15
    assert FloatNBT(0.5).value == 0.5
    assert DoubleNBT(0.6).value == 0.6
    assert ByteArrayNBT(b"test").value == b"test"
    assert StringNBT("test").value == "test"
    assert IntArrayNBT([0, 1, 2]).value == [0, 1, 2]
    assert LongArrayNBT([0, 1, 2, 3]).value == [0, 1, 2, 3]

    invalid = ListNBT("Hello", "name")
    with pytest.raises(AttributeError):
        invalid[0]

    invalid = CompoundNBT([ByteNBT(0, "Byte"), "Hi"], "name")
    with pytest.raises(AttributeError):
        invalid["Byte"]  # Attribute error is raised when the structure is incorrectly constructed


def test_to_object_morecases():
    """Test to_object with more edge cases."""

    class CustomType:
        def __bytes__(self):
            return b"test"

    assert NBTag.from_object(
        {
            "bytearray": b"test",
            "empty_list": [],
            "empty_compound": {},
            "custom": CustomType(),
        }
    ).to_object() == {
        "bytearray": b"test",
        "empty_list": [],
        "empty_compound": {},
        "custom": b"test",
    }

    assert NBTag.to_object(CompoundNBT([])) == {}

    assert EndNBT().to_object() == {}  # Does not add anything when doing dict.update
    assert FloatNBT(0.5).to_object() == 0.5
    assert FloatNBT(0.5, "Hello World").to_object() == {"Hello World": 0.5}
    assert ByteArrayNBT(b"test").to_object() == b"test"  # Do not add name when there is no name
    assert StringNBT("test").to_object() == "test"
    assert StringNBT("test", "name").to_object() == {"name": "test"}
    assert ListNBT([ByteNBT(0), ByteNBT(1)]).to_object() == [0, 1]
    assert ListNBT([ByteNBT(0), ByteNBT(1)], "name").to_object() == {"name": [0, 1]}
    assert IntArrayNBT([0, 1, 2]).to_object() == [0, 1, 2]
    assert LongArrayNBT([0, 1, 2]).to_object() == [0, 1, 2]


def test_data_conversions():
    """Test data conversions using the built-in functions."""
    assert int(IntNBT(-1)) == -1
    assert float(FloatNBT(0.5)) == 0.5
    assert str(StringNBT("test")) == "test"
    assert bytes(ByteArrayNBT(b"test")) == b"test"
    assert list(ListNBT([ByteNBT(0), ByteNBT(1)])) == [ByteNBT(0), ByteNBT(1)]
    assert dict(CompoundNBT([ByteNBT(0, "first"), ByteNBT(1, "second")])) == {
        "first": ByteNBT(0, "first"),
        "second": ByteNBT(1, "second"),
    }
    assert list(IntArrayNBT([0, 1, 2])) == [0, 1, 2]
    assert list(LongArrayNBT([0, 1, 2])) == [0, 1, 2]


def test_init_nbtag_directly():
    """Test initializing NBTag directly."""
    with pytest.raises(TypeError):
        NBTag(0)
    with pytest.raises(TypeError):
        NBTag(0, "test")
    with pytest.raises(TypeError):
        NBTag(0, name="test")


# endregion
