from __future__ import annotations

import json
from typing import TypedDict, Union, cast, final

from typing_extensions import Self, TypeAlias, override

from mcproto.buffer import Buffer
from mcproto.types.abc import MCType
from attrs import define

from mcproto.types.nbt import NBTag, StringNBT, ByteNBT, FromObjectSchema, FromObjectType

__all__ = [
    "TextComponent",
    "RawTextComponentDict",
    "RawTextComponent",
]


class RawTextComponentDict(TypedDict, total=False):
    """Dictionary structure of JSON chat messages when serialized."""

    text: str
    translation: str
    extra: list[RawTextComponentDict]

    color: str
    bold: bool
    strikethrough: bool
    italic: bool
    underlined: bool
    obfuscated: bool


RawTextComponent: TypeAlias = Union[RawTextComponentDict, "list[RawTextComponentDict]", str]


def _deep_copy_dict(data: RawTextComponentDict) -> RawTextComponentDict:
    """Deep copy a dictionary structure."""
    json_data = json.dumps(data)
    return json.loads(json_data)


@define
class JSONTextComponent(MCType):
    """Minecraft chat message representation."""

    raw: RawTextComponent

    def as_dict(self) -> RawTextComponentDict:
        """Convert received ``raw`` into a stadard :class:`dict` form."""
        if isinstance(self.raw, list):
            return RawTextComponentDict(extra=self.raw)
        if isinstance(self.raw, str):
            return RawTextComponentDict(text=self.raw)
        if isinstance(self.raw, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
            return self.raw

        raise TypeError(  # pragma: no cover
            f"Found unexpected type ({self.raw.__class__!r}) ({self.raw!r}) in `raw` attribute"
        )

    @override
    def __eq__(self, other: object) -> bool:
        """Check equality between two chat messages.

        ..warning: This is purely using the `raw` field, which means it's possible that
        a chat message that appears the same, but was representing in a different way
        will fail this equality check.
        """
        if not isinstance(other, JSONTextComponent):
            return NotImplemented

        return self.raw == other.raw

    @override
    def serialize_to(self, buf: Buffer) -> None:
        txt = json.dumps(self.raw)
        buf.write_utf(txt)

    @override
    @classmethod
    def deserialize(cls, buf: Buffer, /) -> Self:
        txt = buf.read_utf()
        dct = json.loads(txt)
        return cls(dct)

    @override
    def validate(self) -> None:
        if not isinstance(self.raw, (dict, list, str)):  # type: ignore[unreachable]
            raise TypeError(f"Expected `raw` to be a dict, list or str, got {self.raw!r} instead")
        if isinstance(self.raw, dict):  # We want to keep it this way for readability
            if "text" not in self.raw and "extra" not in self.raw:
                raise AttributeError("Expected `raw` to have either 'text' or 'extra' key, got neither")
        if isinstance(self.raw, list):
            for elem in self.raw:
                if not isinstance(elem, dict):  # type: ignore[unreachable]
                    raise TypeError(f"Expected `raw` to be a list of dicts, got {elem!r} instead")
                if "text" not in elem and "extra" not in elem:
                    raise AttributeError(
                        "Expected each element in `raw` to have either 'text' or 'extra' key, got neither"
                    )


@final
class TextComponent(JSONTextComponent):
    """Minecraft chat message representation.

    This class provides the new chat message format using NBT data instead of JSON.
    """

    __slots__ = ()

    @override
    def serialize_to(self, buf: Buffer) -> None:
        payload = self._convert_to_dict(self.raw)
        payload = cast(FromObjectType, payload)  # We just ensured that the data is converted to the correct format
        nbt = NBTag.from_object(data=payload, schema=self._build_schema())  # This will validate the data
        nbt.serialize_to(buf)

    @override
    @classmethod
    def deserialize(cls, buf: Buffer, /) -> Self:
        nbt = NBTag.deserialize(buf, with_name=False)
        # Ensure the schema is compatible with the one defined in the class
        data, schema = cast("tuple[FromObjectType, FromObjectSchema]", nbt.to_object(include_schema=True))

        def recursive_validate(recieved: FromObjectSchema, expected: FromObjectSchema) -> None:
            if isinstance(recieved, dict):
                if not isinstance(expected, dict):
                    raise TypeError(f"Expected {expected!r}, got dict")
                for key, value in recieved.items():
                    if key not in expected:
                        raise KeyError(f"Unexpected key {key!r}")
                    recursive_validate(value, expected[key])
            elif isinstance(recieved, list):
                if not isinstance(expected, list):
                    raise TypeError(f"Expected {expected!r}, got list")
                for rec in recieved:
                    recursive_validate(rec, expected[0])
            elif recieved != expected:
                raise TypeError(f"Expected {expected!r}, got {recieved!r}")

        recursive_validate(schema, cls._build_schema())
        data = cast(RawTextComponentDict, data)  # We just ensured that the data is compatible with the schema
        return cls(data)

    @staticmethod
    def _build_schema() -> FromObjectSchema:
        """Build the schema for the NBT data representing the chat message."""
        schema: FromObjectSchema = {
            "text": StringNBT,
            "color": StringNBT,
            "bold": ByteNBT,
            "italic": ByteNBT,
            "underlined": ByteNBT,
            "strikethrough": ByteNBT,
            "obfuscated": ByteNBT,
        }
        # Allow the schema to be recursive
        schema["extra"] = [schema]  # type: ignore
        return schema

    @staticmethod
    def _convert_to_dict(msg: RawTextComponent) -> RawTextComponentDict:
        """Convert a chat message into a dictionary representation."""
        if isinstance(msg, str):
            return {"text": msg}

        if isinstance(msg, list):
            main = TextComponent._convert_to_dict(msg[0])
            if "extra" not in main:
                main["extra"] = []
            for elem in msg[1:]:
                main["extra"].append(TextComponent._convert_to_dict(elem))
            return main

        if isinstance(msg, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
            return _deep_copy_dict(msg)  # We don't want to modify self.raw for example

        raise TypeError(f"Unexpected type {msg!r} ({msg.__class__.__name__})")  # pragma: no cover

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TextComponent):
            return NotImplemented
        self_dict = self._convert_to_dict(self.raw)
        other_dict = self._convert_to_dict(other.raw)
        return self_dict == other_dict
