from __future__ import annotations

import math

from typing import ClassVar
from typing_extensions import override

from mcproto.buffer import Buffer
from mcproto.protocol import StructFormat
from mcproto.types.abc import MCType
from attrs import define


@define
class FixedBitset(MCType):
    """Represents a fixed-size bitset."""

    __n: ClassVar[int] = -1

    data: bytearray

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write(bytes(self.data))

    @override
    @classmethod
    def deserialize(cls, buf: Buffer) -> FixedBitset:
        data = buf.read(math.ceil(cls.__n / 8))
        return cls(data=data)

    @override
    def validate(self) -> None:
        """Validate the bitset."""
        if self.__n == -1:
            raise ValueError("Bitset size is not defined.")
        if len(self.data) != math.ceil(self.__n / 8):
            raise ValueError(f"Bitset size is {len(self.data) * 8}, expected {self.__n}.")

    @staticmethod
    def of_size(n: int) -> type[FixedBitset]:
        """Return a new FixedBitset class with the given size.

        :param n: The size of the bitset.
        """
        new_class = type(f"FixedBitset{n}", (FixedBitset,), {})
        new_class.__n = n
        return new_class

    @classmethod
    def from_int(cls, n: int) -> FixedBitset:
        """Return a new FixedBitset with the given integer value.

        :param n: The integer value.
        """
        if cls.__n == -1:
            raise ValueError("Bitset size is not defined.")
        if n < 0:
            # Manually compute two's complement
            n = -n
            data = bytearray(n.to_bytes(math.ceil(cls.__n / 8), "big"))
            for i in range(len(data)):
                data[i] ^= 0xFF
            data[-1] += 1
        else:
            data = bytearray(n.to_bytes(math.ceil(cls.__n / 8), "big"))
        return cls(data=data)

    def __setitem__(self, index: int, value: bool) -> None:
        byte_index = index // 8
        bit_index = index % 8
        if value:
            self.data[byte_index] |= 1 << bit_index
        else:
            self.data[byte_index] &= ~(1 << bit_index)

    def __getitem__(self, index: int) -> bool:
        byte_index = index // 8
        bit_index = index % 8
        return bool(self.data[byte_index] & (1 << bit_index))

    def __len__(self) -> int:
        return self.__n

    def __and__(self, other: FixedBitset) -> FixedBitset:
        if self.__n != other.__n:
            raise ValueError("Bitsets must have the same size.")
        return type(self)(data=bytearray(a & b for a, b in zip(self.data, other.data)))

    def __or__(self, other: FixedBitset) -> FixedBitset:
        if self.__n != other.__n:
            raise ValueError("Bitsets must have the same size.")
        return type(self)(data=bytearray(a | b for a, b in zip(self.data, other.data)))

    def __xor__(self, other: FixedBitset) -> FixedBitset:
        if self.__n != other.__n:
            raise ValueError("Bitsets must have the same size.")
        return type(self)(data=bytearray(a ^ b for a, b in zip(self.data, other.data)))

    def __invert__(self) -> FixedBitset:
        return type(self)(data=bytearray(~a & 0xFF for a in self.data))

    def __bytes__(self) -> bytes:
        return bytes(self.data)

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, FixedBitset):
            return NotImplemented
        return self.data == value.data and self.__n == value.__n


@define
class Bitset(MCType):
    """Represents a lenght-prefixed bitset with a variable size.

    :param size: The number of longs in the array representing the bitset.
    :param data: The bits of the bitset.
    """

    size: int
    data: list[int]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.size)
        for i in range(self.size):
            buf.write_value(StructFormat.LONGLONG, self.data[i])

    @override
    @classmethod
    def deserialize(cls, buf: Buffer) -> Bitset:
        size = buf.read_varint()
        if buf.remaining < size * 8:
            raise IOError("Not enough data to read bitset.")
        data = [buf.read_value(StructFormat.LONGLONG) for _ in range(size)]
        return cls(size=size, data=data)

    @override
    def validate(self) -> None:
        """Validate the bitset."""
        if self.size != len(self.data):
            raise ValueError(f"Bitset size is {self.size}, expected {len(self.data)}.")

    @classmethod
    def from_int(cls, n: int, size: int | None = None) -> Bitset:
        """Return a new Bitset with the given integer value.

        :param n: The integer value.
        :param size: The number of longs in the array representing the bitset.
        """
        if size is None:
            size = math.ceil(float(n.bit_length()) / 64.0)
        data = [n >> (i * 64) & 0xFFFFFFFFFFFFFFFF for i in range(size)]
        return cls(size=size, data=data)

    def __getitem__(self, index: int) -> bool:
        byte_index = index // 64
        bit_index = index % 64

        return bool(self.data[byte_index] & (1 << bit_index))

    def __setitem__(self, index: int, value: bool) -> None:
        byte_index = index // 64
        bit_index = index % 64

        if value:
            self.data[byte_index] |= 1 << bit_index
        else:
            self.data[byte_index] &= ~(1 << bit_index)

    def __len__(self) -> int:
        return self.size * 64

    def __and__(self, other: Bitset) -> Bitset:
        if self.size != other.size:
            raise ValueError("Bitsets must have the same size.")
        return Bitset(size=self.size, data=[a & b for a, b in zip(self.data, other.data)])

    def __or__(self, other: Bitset) -> Bitset:
        if self.size != other.size:
            raise ValueError("Bitsets must have the same size.")
        return Bitset(size=self.size, data=[a | b for a, b in zip(self.data, other.data)])

    def __xor__(self, other: Bitset) -> Bitset:
        if self.size != other.size:
            raise ValueError("Bitsets must have the same size.")
        return Bitset(size=self.size, data=[a ^ b for a, b in zip(self.data, other.data)])

    def __invert__(self) -> Bitset:
        return Bitset(size=self.size, data=[~a for a in self.data])

    def __bytes__(self) -> bytes:
        return b"".join(a.to_bytes(8, "big") for a in self.data)
