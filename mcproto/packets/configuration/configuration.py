from __future__ import annotations

from enum import IntEnum
from typing import ClassVar, final

from typing_extensions import Self, override

from mcproto.buffer import Buffer
from mcproto.protocol.base_io import StructFormat
from mcproto.packets.packet import ClientBoundPacket, GameState, ServerBoundPacket
from attrs import define
from mcproto.types.identifier import Identifier
from mcproto.types.chat import TextComponent
from mcproto.types.uuid import UUID
from mcproto.types.nbt import CompoundNBT
from mcproto.types.tag import RegistryTag

__all__ = [
    "ClientboundPluginMessage",
    "Disconnect",
    "FinishConfiguration",
    "ClientboundKeepAlive",
    "Ping",
    "RegistryData",
    "RemoveResourcePack",
    "AddResourcePack",
    "FeatureFlags",
    "UpdateTags",
    "ClientInformation",
    "ServerboundPluginMessage",
    "AcknowledgeFinishConfiguration",
    "ServerboundKeepAlive",
    "Pong",
    "ResourcePackResult",
    "ResourcePackResponse",
]


@final
@define
class ClientboundPluginMessage(ClientBoundPacket):
    """Mods and plugins can use this to send their data. (Client -> Server).

    Minecraft itself uses several plugin channels. These internal channels are in the `minecraft` namespace.

    Initialize the ClientboundPluginMessage packet.

    :param channel: Name of the plugin channel used to send the data.
    :type channel: Identifier
    :param data: Any data.
    :type data: bytes
    """

    PACKET_ID: ClassVar[int] = 0x0
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    channel: Identifier
    data: bytes

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.channel.serialize_to(buf)
        buf.write(self.data)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        channel = Identifier.deserialize(buf)
        data = bytes(buf.read(buf.remaining))
        return cls(channel=channel, data=data)


@final
@define
class Disconnect(ClientBoundPacket):
    """Disconnect the player with a reason. (Client -> Server).

    Initialize the Disconnect packet.

    :param reason: The reason why the player was disconnected.
    :type reason: TextComponent
    """

    PACKET_ID: ClassVar[int] = 0x1
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    reason: TextComponent

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.reason.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        reason = TextComponent.deserialize(buf)
        return cls(reason=reason)


@final
@define
class FinishConfiguration(ClientBoundPacket):
    """Sent by the server to notify the client that the configuration process has finished. (Client -> Server).

    The client answers with Acknowledge Finish Configuration whenever it is ready to continue.

    Initialize the FinishConfiguration packet.


    """

    PACKET_ID: ClassVar[int] = 0x2
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    @override
    def serialize_to(self, buf: Buffer) -> None:
        pass

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        return cls()


@final
@define
class ClientboundKeepAlive(ClientBoundPacket):
    """The server will frequently send out a keep-alive, each containing a random ID. (Client -> Server).

    The client must respond with the same payload (see Serverbound Keep Alive). If the client does not
    respond to a Keep Alive packet within 15 seconds after it was sent, the server kicks the client.
    Vice versa, if the server does not send any keep-alives for 20 seconds, the client will disconnect and
    yields a 'Timed out' exception.

    The Notchian server uses a system-dependent time in milliseconds to
    generate the keep alive ID value.

    Initialize the ClientboundKeepAlive packet.

    :param keep_alive_id: The keep alive ID.
    :type keep_alive_id: int
    """

    PACKET_ID: ClassVar[int] = 0x3
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    keep_alive_id: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.LONGLONG, self.keep_alive_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        keep_alive_id = buf.read_value(StructFormat.LONGLONG)
        return cls(keep_alive_id=keep_alive_id)


@final
@define
class Ping(ClientBoundPacket):
    """Packet is not used by the Notchian server. (Client -> Server).

    When sent to the client, client responds with a Pong packet with the same id.

    Initialize the Ping packet.

    :param payload: The payload.
    :type payload: int
    """

    PACKET_ID: ClassVar[int] = 0x4
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    payload: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.INT, self.payload)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        payload = buf.read_value(StructFormat.INT)
        return cls(payload=payload)


@final
@define
class RegistryData(ClientBoundPacket):
    """Represents certain registries that are sent from the server and are applied on the client. (Client -> Server).

    Initialize the RegistryData packet.

    :param registry_codec: The registry data.
    :type registry_codec: CompoundNBT
    """

    PACKET_ID: ClassVar[int] = 0x5
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    registry_codec: CompoundNBT

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.registry_codec.serialize_to(buf, with_type=True, with_name=False)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        # Since 1.20.2 (Protocol 764) NBT sent over the network has been updated to exclude the name from
        # the root TAG_COMPOUND
        # TODO: Check if this is correct using Wireshark
        registry_codec = CompoundNBT.deserialize(buf, with_type=True, with_name=False)
        return cls(registry_codec=registry_codec)


@final
@define
class RemoveResourcePack(ClientBoundPacket):
    """Remove Resource Pack (configuration) (Client -> Server).

    Initialize the RemoveResourcePack packet.

    :param uuid: The UUID of the resource pack to be removed.
    :type uuid: :class:`UUID`, optional
    """

    PACKET_ID: ClassVar[int] = 0x6
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    uuid: UUID | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_optional(self.uuid, lambda x: x.serialize_to(buf))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        uuid = buf.read_optional(lambda: UUID.deserialize(buf))
        return cls(uuid=uuid)


@final
@define
class AddResourcePack(ClientBoundPacket):
    """Add Resource Pack (configuration) (Client -> Server).

    Initialize the AddResourcePack packet.

    :param uuid: The unique identifier of the resource pack.
    :type uuid: UUID
    :param url: The URL to the resource pack.
    :type url: str
    :param hash_sha1: A 40 character hexadecimal, case-insensitive SHA-1 hash of the resource pack file. If it's not
    a 40 character hexadecimal string, the client will not use it for hash verification and likely
    waste bandwidth.
    :type hash_sha1: str, optional
    :param forced: The Notchian client will be forced to use the resource pack from the server. If they decline
    they will be kicked from the server.
    :type forced: bool
    :param prompt_message: This is shown in the prompt making the client accept or decline the resource pack. Only
    present if 'Has Prompt Message' is true.
    :type prompt_message: TextComponent, optional
    """

    PACKET_ID: ClassVar[int] = 0x7
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    uuid: UUID
    url: str
    hash_sha1: str | None
    forced: bool
    prompt_message: TextComponent | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.uuid.serialize_to(buf)
        buf.write_utf(self.url)
        buf.write_utf(self.hash_sha1 if self.hash_sha1 else "")
        buf.write_value(StructFormat.BYTE, int(self.forced))
        buf.write_optional(self.prompt_message, lambda x: x.serialize_to(buf))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        uuid = UUID.deserialize(buf)
        url = buf.read_utf()
        hash_sha1 = buf.read_utf()
        if not hash_sha1:
            hash_sha1 = None
        forced = bool(buf.read_value(StructFormat.BYTE))
        prompt_message = buf.read_optional(lambda: TextComponent.deserialize(buf))
        return cls(
            uuid=uuid,
            url=url,
            hash_sha1=hash_sha1,
            forced=forced,
            prompt_message=prompt_message,
        )

    @override
    def validate(self) -> None:
        if (
            self.hash_sha1  # Ignore if not present
            and not all(c in "0123456789abcdefABCDEF" for c in self.hash_sha1)
            and len(self.hash_sha1) != 40
        ):
            raise ValueError("Hash SHA-1 must be a 40 character hexadecimal string.")


@final
@define
class FeatureFlags(ClientBoundPacket):
    """Used to enable and disable features, generally experimental ones, on the client. (Client -> Server).

    Initialize the FeatureFlags packet.

    :param flags: Array of Identifier.
    :type flags: Identifier
    """

    PACKET_ID: ClassVar[int] = 0x8
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    flags: list[Identifier]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(len(self.flags))
        for feature in self.flags:
            feature.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        total_features = buf.read_varint()
        flags = [Identifier.deserialize(buf) for _ in range(total_features)]
        return cls(flags=flags)


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

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(len(self.mapping))
        for registry, tags in self.mapping.items():
            registry.serialize_to(buf)
            buf.write_varint(len(tags))
            for tag in tags:
                tag.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        total_registries = buf.read_varint()
        mapping: dict[Identifier, list[RegistryTag]] = {}
        for _ in range(total_registries):
            registry = Identifier.deserialize(buf)
            total_tags = buf.read_varint()
            tags: list[RegistryTag] = []
            for _ in range(total_tags):
                tag = RegistryTag.deserialize(buf)
                tags.append(tag)
            mapping[registry] = tags
        return cls(mapping=mapping)


@final
@define
class ClientInformation(ClientBoundPacket):
    """Sent when the player connects, or when settings are changed. (Client -> Server).

    Initialize the ClientInformation packet.

    :param locale: Client's language (e.g. en_GB).
    :type locale: str
    :param view_distance: Client-side render distance in chunks.
    :type view_distance: int
    :param chat_mode: Chat mode (0: enabled, 1: commands only, 2: hidden).
    :type chat_mode: int
    :param chat_colors: Whether colored chat is enabled.
    :type chat_colors: bool
    :param displayed_skin_parts: Bit mask indicating displayed skin parts.
    :type displayed_skin_parts: int
    :param main_hand: Main hand (0: Left, 1: Right).
    :type main_hand: int
    :param enable_text_filtering: Enables text filtering (currently always false).
    :type enable_text_filtering: bool
    :param allow_server_listings: Whether the player appears in server listings.
    :type allow_server_listings: bool
    """

    PACKET_ID: ClassVar[int] = 0x0
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    locale: str
    view_distance: int
    chat_mode: int
    chat_colors: bool
    displayed_skin_parts: int
    main_hand: int
    enable_text_filtering: bool
    allow_server_listings: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_utf(self.locale)
        buf.write_value(StructFormat.BYTE, self.view_distance)
        buf.write_varint(self.chat_mode)
        buf.write_value(StructFormat.BYTE, int(self.chat_colors))
        buf.write_value(StructFormat.UBYTE, self.displayed_skin_parts)
        buf.write_varint(self.main_hand)
        buf.write_value(StructFormat.BYTE, int(self.enable_text_filtering))
        buf.write_value(StructFormat.BYTE, int(self.allow_server_listings))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        locale = buf.read_utf()
        view_distance = buf.read_value(StructFormat.BYTE)
        chat_mode = buf.read_varint()
        chat_colors = bool(buf.read_value(StructFormat.BYTE))
        displayed_skin_parts = buf.read_value(StructFormat.UBYTE)
        main_hand = buf.read_varint()
        enable_text_filtering = bool(buf.read_value(StructFormat.BYTE))
        allow_server_listings = bool(buf.read_value(StructFormat.BYTE))
        return cls(
            locale=locale,
            view_distance=view_distance,
            chat_mode=chat_mode,
            chat_colors=chat_colors,
            displayed_skin_parts=displayed_skin_parts,
            main_hand=main_hand,
            enable_text_filtering=enable_text_filtering,
            allow_server_listings=allow_server_listings,
        )

    @override
    def validate(self) -> None:
        if not (0 <= self.chat_mode <= 2):
            raise ValueError(f"Chat mode must be 0, 1, or 2, got {self.chat_mode}.")

        if not (0 <= self.main_hand <= 1):
            raise ValueError(f"Main hand must be 0 or 1, got {self.main_hand}.")

        if len(self.locale) > 16:
            raise ValueError(f"Locale is too long, must be at most 16 characters, got {len(self.locale)}.")


@final
@define
class ServerboundPluginMessage(ServerBoundPacket):
    """Mods and plugins can use this to send data. See wiki.vg for plugin channels documentation. (Server -> Client).

    Initialize the ServerboundPluginMessage packet.

    :param channel: Name of the plugin channel used to send the data.
    :type channel: Identifier
    :param data: Data sent by the plugin (length inferred from packet size). Maximum length: 32767 bytes.
    :type data: bytes
    """

    PACKET_ID: ClassVar[int] = 0x1
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    channel: Identifier
    data: bytes

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.channel.serialize_to(buf)
        buf.write(self.data)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        channel = Identifier.deserialize(buf)
        data = bytes(buf.read(buf.remaining))
        return cls(channel=channel, data=data)


@final
@define
class AcknowledgeFinishConfiguration(ClientBoundPacket):
    """Sent by the client to acknowledge the configuration process is finished. (Client -> Server).

    Initialize the AcknowledgeFinishConfiguration packet.
    """

    PACKET_ID: ClassVar[int] = 0x2
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    @override
    def serialize_to(self, buf: Buffer) -> None:
        pass

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        return cls()


@final
@define
class ServerboundKeepAlive(ServerBoundPacket):
    """Response to server's keep-alive packet with the same ID. (Server -> Client).

    Initialize the ServerboundKeepAlive packet.

    :param keep_alive_id: Keep-alive ID received from the server.
    :type keep_alive_id: int
    """

    PACKET_ID: ClassVar[int] = 0x3
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    keep_alive_id: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.LONGLONG, self.keep_alive_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        keep_alive_id = buf.read_value(StructFormat.LONGLONG)
        return cls(keep_alive_id=keep_alive_id)


@final
@define
class Pong(ClientBoundPacket):
    """Response to the server's ping packet with the same ID. (Client -> Server).

    Initialize the Pong packet.

    :param payload: ID from the ping packet (echoed back).
    :type payload: int
    """

    PACKET_ID: ClassVar[int] = 0x4
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    payload: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.INT, self.payload)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        payload = buf.read_value(StructFormat.INT)
        return cls(payload=payload)


class ResourcePackResult(IntEnum):
    """Result of the resource pack request."""

    SUCCESSFULLY_DOWNLOADED = 0
    DECLINED = 1
    FAILED_TO_DOWNLOAD = 2
    ACCEPTED = 3
    DOWNLOADED = 4
    INVALID_URL = 5
    FAILED_TO_RELOAD = 6
    DISCARDED = 7


@final
@define
class ResourcePackResponse(ClientBoundPacket):
    """Server's response to the client's resource pack request. (Client -> Server).

    Initialize the ResourcePackResponse packet.

    :param uuid: UUID of the received resource pack.
    :type uuid: :class:`UUID`, optional
    :param result: Result of the resource pack request.
    :type result: :class:`ResourcePackResult`
    """

    PACKET_ID: ClassVar[int] = 0x5
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    uuid: UUID | None
    result: ResourcePackResult

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_optional(self.uuid, lambda x: x.serialize_to(buf))
        buf.write_varint(self.result.value)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        uuid = buf.read_optional(lambda: UUID.deserialize(buf))
        result = ResourcePackResult(buf.read_varint())
        return cls(uuid=uuid, result=result)
