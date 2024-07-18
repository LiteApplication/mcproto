from __future__ import annotations

from enum import IntEnum
from typing import ClassVar, final

from attrs import define, field, validators
from typing_extensions import Self, override

from mcproto.buffer import Buffer
from mcproto.packets.packet import GameState, ServerBoundPacket
from mcproto.protocol.base_io import StructFormat
from mcproto.types.identifier import Identifier
from mcproto.types.uuid import UUID


@final
@define
class ClientInformation(ServerBoundPacket):
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

    locale: str = field(validator=validators.max_len(16))
    view_distance: int = field()
    chat_mode: int = field(validator=[validators.ge(0), validators.le(2)])
    chat_colors: bool = field()
    displayed_skin_parts: int = field()
    main_hand: int = field(validator=[validators.ge(0), validators.le(1)])
    enable_text_filtering: bool = field()
    allow_server_listings: bool = field()

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


@final
@define
class CookieResponse(ServerBoundPacket):
    """Response to a Cookie Request from the server. (Client -> Server).

    The Notchian server only accepts responses of up to 5 kiB in size.

    Initialize the CookieResponse packet.

    :param key: The identifier of the cookie.
    :type key: bytes
    :param payload: The data of the cookie, if any.
    :type payload: bytes | None
    """

    PACKET_ID: ClassVar[int] = 0x1
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    key: Identifier
    payload: bytes | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.key.serialize_to(buf)
        buf.write_optional(self.payload, buf.write_bytearray)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        key = Identifier.deserialize(buf)
        payload = buf.read_optional(lambda: bytes(buf.read_bytearray()))
        return cls(key=key, payload=payload)


@final
@define
class CustomPayload(ServerBoundPacket):
    """Mods and plugins can use this to send data. See wiki.vg for plugin channels documentation. (Client -> Server).

    Initialize the ServerboundCustomPayload packet.

    :param channel: Name of the plugin channel used to send the data.
    :type channel: :class:`~mcproto.types.Identifier`
    :param data: Data sent by the plugin (length inferred from packet size). Maximum length: 32767 bytes.
    :type data: bytes
    """

    PACKET_ID: ClassVar[int] = 0x2
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
class FinishConfiguration(ServerBoundPacket):
    """Sent by the client to acknowledge the configuration process is finished. (Client -> Server).

    Initialize the FinishConfiguration packet.
    """

    PACKET_ID: ClassVar[int] = 0x3
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
class KeepAlive(ServerBoundPacket):
    """Response to server's keep-alive packet with the same ID. (Client -> Server).

    Initialize the ServerboundKeepAlive packet.

    :param keep_alive_id: Keep-alive ID received from the server.
    :type keep_alive_id: int
    """

    PACKET_ID: ClassVar[int] = 0x4
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
class Pong(ServerBoundPacket):
    """Response to the server's ping packet with the same ID. (Client -> Server).

    Initialize the Pong packet.

    :param payload: ID from the ping packet (echoed back).
    :type payload: int
    """

    PACKET_ID: ClassVar[int] = 0x5
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
class ResourcePack(ServerBoundPacket):
    """Client's response to the server's :class:`ResourcePackPush` packet. (Client -> Server).

    Initialize the ResourcePack packet.

    :param uuid: UUID of the received resource pack.
    :type uuid: :class:`UUID`, optional
    :param result: Result of the resource pack request.
    :type result: :class:`ResourcePackResult`
    """

    PACKET_ID: ClassVar[int] = 0x6
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


@final
@define
class SelectKnownPacks(ServerBoundPacket):
    """Informs the server of which data packs are present on the client. (Client -> Server).

    The client sends this in response to :class:`~mcproto.packets.configuration.clientbound.SelectKnownPacks`.

    If the client specifies a pack in this packet, the server should omit its contained data from the
    :class:`RegistryData` packet.

    Initialize the ServerboundSelectKnownPacks packet.

    :param known_packs: A list of known packs.
    :type known_packs: list[tuple[str, str, str]]
    """

    PACKET_ID: ClassVar[int] = 0x07
    GAME_STATE: ClassVar[GameState] = GameState.CONFIGURATION

    known_packs: list[tuple[str, str, str]]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(len(self.known_packs))
        for namespace, pack_id, version in self.known_packs:
            buf.write_utf(namespace)
            buf.write_utf(pack_id)
            buf.write_utf(version)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        known_pack_count = buf.read_varint()
        known_packs: list[tuple[str, str, str]] = []
        for _ in range(known_pack_count):
            namespace = buf.read_utf()
            pack_id = buf.read_utf()
            version = buf.read_utf()
            known_packs.append((namespace, pack_id, version))
        return cls(known_packs=known_packs)
