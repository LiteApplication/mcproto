from __future__ import annotations

import re
from mcproto.packets.configuration import (
    AddResourcePack,
    ClientboundKeepAlive,
    ClientboundPluginMessage,
    ServerboundPluginMessage,
    AcknowledgeFinishConfiguration,
    Disconnect,
    FeatureFlags,
    FinishConfiguration,
    Ping,
    ClientInformation,
    Pong,
    RegistryData,
    RemoveResourcePack,
    ResourcePackResult,
    ResourcePackResponse,
    ServerboundKeepAlive,
    UpdateTags,
)
from mcproto.types.chat import TextComponent
from mcproto.types.identifier import Identifier
from mcproto.types.nbt import CompoundNBT, StringNBT
from mcproto.types.uuid import UUID
from mcproto.types.tag import RegistryTag
from tests.helpers import gen_serializable_test, TestExc

# ClientboundPluginMessage
gen_serializable_test(
    context=globals(),
    cls=ClientboundPluginMessage,
    fields=[("channel", Identifier), ("data", bytes)],
    serialize_deserialize=[
        (
            (Identifier("custom:channel"), b"Hello"),
            b"\x0ecustom:channelHello",
        ),
    ],
)


# Disconnect
gen_serializable_test(
    context=globals(),
    cls=Disconnect,
    fields=[("reason", TextComponent)],
    serialize_deserialize=[
        (
            (TextComponent("Server closed"),),
            bytes(TextComponent("Server closed").serialize()),
        ),
    ],
)

# FinishConfiguration
# This test is here to ensure no data is serialized
gen_serializable_test(
    context=globals(),
    cls=FinishConfiguration,
    fields=[],
    serialize_deserialize=[
        (
            (),  # No fields
            b"",
        ),
    ],
)

# ClientboundKeepAlive
gen_serializable_test(
    context=globals(),
    cls=ClientboundKeepAlive,
    fields=[("keep_alive_id", int)],
    serialize_deserialize=[
        (
            (123,),
            b"\x00\x00\x00\x00\x00\x00\x00\x7b",
        ),
    ],
)

# Ping
gen_serializable_test(
    context=globals(),
    cls=Ping,
    fields=[("payload", int)],
    serialize_deserialize=[
        (
            (123,),
            b"\x00\x00\x00\x7b",
        ),
    ],
)

# RegistryData
gen_serializable_test(
    context=globals(),
    cls=RegistryData,
    fields=[("registry_codec", CompoundNBT)],
    serialize_deserialize=[
        (
            (
                CompoundNBT.from_object(
                    {"type": Identifier("foo"), "value": StringNBT("bar")},
                    schema={"type": Identifier, "value": StringNBT},
                ),
            ),
            bytes(CompoundNBT([StringNBT("minecraft:foo", name="type"), StringNBT("bar", name="value")]).serialize()),
        ),
    ],
)

# RemoveResourcePack
gen_serializable_test(
    context=globals(),
    cls=RemoveResourcePack,
    fields=[("uuid", UUID)],
    serialize_deserialize=[
        (
            (UUID("12345678-90ab-cdef-1234-567890abcdef"),),
            b"\x01" + bytes(UUID("12345678-90ab-cdef-1234-567890abcdef").serialize()),
        ),
        ((None,), b"\x00"),
    ],
)

# AddResourcePack
gen_serializable_test(
    context=globals(),
    cls=AddResourcePack,
    fields=[
        ("uuid", UUID),
        ("url", str),
        ("hash_sha1", str),
        ("forced", bool),
        ("prompt_message", "TextComponent | None"),
    ],
    serialize_deserialize=[
        (
            (
                UUID("12345678-90ab-cdef-1234-567890abcdef"),
                "http://example.com/resource.zip",
                "1234567890abcdef1234567890abCDef12345678",
                True,
                TextComponent("This is a resource pack"),
            ),
            bytes(UUID("12345678-90ab-cdef-1234-567890abcdef").serialize())
            + b"\x1fhttp://example.com/resource.zip"
            + b"\x281234567890abcdef1234567890abCDef12345678"
            + b"\x01"
            + b"\x01"
            + bytes(TextComponent("This is a resource pack").serialize()),
        ),
        (
            (
                UUID("12345678-90ab-cdef-1234-567890abcdef"),
                "http://example.com/resource.zip",
                None,
                True,
                None,
            ),
            bytes(UUID("12345678-90ab-cdef-1234-567890abcdef").serialize())
            + b"\x1fhttp://example.com/resource.zip"
            + b"\x00"  # String of length 0
            + b"\x01"
            + b"\x00",
        ),
    ],
    validation_fail=[
        (
            (
                UUID("12345678-90ab-cdef-1234-567890abcdef"),
                "http://example.com/resource.zip",
                "1234567890abcdef1234567890abcdef123456789g",
                True,
                None,
            ),
            TestExc(ValueError, r"Hash SHA-1 must be a 40 character hexadecimal string\."),
        ),
    ],
)

# FeatureFlags
gen_serializable_test(
    context=globals(),
    cls=FeatureFlags,
    fields=[("flags", "list[Identifier]")],
    serialize_deserialize=[
        (
            ([Identifier("foo"), Identifier("bar")],),
            b"\x02" + bytes(Identifier("foo").serialize()) + bytes(Identifier("bar").serialize()),
        ),
    ],
)

# UpdateTags
'''
@final
@define
class UpdateTags(ClientBoundPacket):
    """Update Tags (configuration) (Client -> Server).

    Contains :
    - Lenght of the array
    - Array of tags
        - Identifier : Registry name they apply to(e.g. minecraft:blocks)
        - Length of the array
        - Array of tag
            - Tag name (e.g. #minecraft:wool)
            - Length of the array
            - Array of VarInt IDs

    Initialize the UpdateTags packet.

    :param tags: A dictionary mapping a registry name to a list of tags.
    :type tags: dict[:class:`Identifier`, list[:class:`RegistryTag`]]

    """

    PACKET_ID: ClassVar[int] = 0x9
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    mapping: dict[Identifier, list[RegistryTag]]

'''

gen_serializable_test(
    context=globals(),
    cls=UpdateTags,
    fields=[("mapping", "dict[Identifier, list[RegistryTag]]")],
    serialize_deserialize=[
        (
            (
                {
                    Identifier("minecraft:block"): [
                        RegistryTag(Identifier("wool"), [1, 2, 3]),
                        RegistryTag(Identifier("mineable/axe"), [4, 5, 6]),
                    ],
                    Identifier("minecraft:item"): [
                        RegistryTag(Identifier("chest_boats"), [7, 8, 9]),
                        RegistryTag(Identifier("enchantable/fishing"), [10]),
                    ],
                },
            ),
            b"\x02"
            + bytes(Identifier("minecraft:block").serialize())
            + b"\x02"
            + bytes(RegistryTag(Identifier("wool"), [1, 2, 3]).serialize())
            + bytes(RegistryTag(Identifier("mineable/axe"), [4, 5, 6]).serialize())
            + bytes(Identifier("minecraft:item").serialize())
            + b"\x02"
            + bytes(RegistryTag(Identifier("chest_boats"), [7, 8, 9]).serialize())
            + bytes(RegistryTag(Identifier("enchantable/fishing"), [10]).serialize()),
        ),
    ],
)

# ClientInformation
gen_serializable_test(
    context=globals(),
    cls=ClientInformation,
    fields=[
        ("locale", str),
        ("view_distance", int),
        ("chat_mode", int),
        ("chat_colors", bool),
        ("displayed_skin_parts", int),
        ("main_hand", int),
        ("enable_text_filtering", bool),
        ("allow_server_listings", bool),
    ],
    serialize_deserialize=[
        (
            ("en_GB", 10, 0, True, 0b00100000, 1, False, True),
            b"\x05en_GB\x0a\x00\x01\x20\x01\x00\x01",
        ),
    ],
    validation_fail=[
        (
            ("en_GB", 10, 3, True, 0b00100000, 1, False, True),
            TestExc(ValueError, re.escape("Chat mode must be 0, 1, or 2, got 3")),
        ),
        (
            ("en_GB", 10, 0, True, 0b00100000, 2, False, True),
            TestExc(ValueError, re.escape("Main hand must be 0 or 1, got 2")),
        ),
        (
            ("too long for a locale", 10, 0, True, 0b00100000, 1, False, True),
            TestExc(ValueError, re.escape("Locale is too long, must be at most 16 characters, got 21")),
        ),
    ],
)
# ServerboundPluginMessage
gen_serializable_test(
    context=globals(),
    cls=ServerboundPluginMessage,
    fields=[("channel", Identifier), ("data", bytes)],
    serialize_deserialize=[
        (
            (Identifier("minecraft:brand"), b"MCProto"),
            b"\x0fminecraft:brandMCProto",
        ),
    ],
)

# AcknowledgeFinishConfiguration
gen_serializable_test(
    context=globals(),
    cls=AcknowledgeFinishConfiguration,
    fields=[],
    serialize_deserialize=[
        (
            (),
            b"",
        ),
    ],
)


# ServerboundKeepAlive
gen_serializable_test(
    context=globals(),
    cls=ServerboundKeepAlive,
    fields=[("keep_alive_id", int)],
    serialize_deserialize=[
        (
            (123,),
            b"\x00\x00\x00\x00\x00\x00\x00\x7b",
        ),
    ],
)

# Pong
gen_serializable_test(
    context=globals(),
    cls=Pong,
    fields=[("payload", int)],
    serialize_deserialize=[
        (
            (123,),
            b"\x00\x00\x00\x7b",
        ),
    ],
)

# ResourcePackResponse
gen_serializable_test(
    context=globals(),
    cls=ResourcePackResponse,
    fields=[("uuid", UUID), ("result", ResourcePackResult)],
    serialize_deserialize=[
        (
            (UUID("12345678-90ab-cdef-1234-567890abcdef"), ResourcePackResult.DOWNLOADED),
            b"\x01" + bytes(UUID("12345678-90ab-cdef-1234-567890abcdef").serialize()) + b"\x04",
        ),
        ((None, ResourcePackResult.DISCARDED), b"\x00\x07"),
    ],
)
