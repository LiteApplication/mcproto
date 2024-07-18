from __future__ import annotations

import math
from enum import IntEnum
from typing import ClassVar, NamedTuple, cast, final

from attrs import define, field, validators
from typing_extensions import Self, override

from mcproto.buffer import Buffer
from mcproto.packets import GameState, ServerBoundPacket
from mcproto.packets.play.clientbound import DebugSampleType
from mcproto.protocol.base_io import StructFormat
from mcproto.types import FixedBitset, Identifier, Position, Slot, UUID, Vec3


@final
@define
class AcceptTeleportation(ServerBoundPacket):
    """Sent by client as confirmation of Synchronize Player Position. (Client -> Server).

    Initialize the AcceptTeleportation packet.

    :param teleport_id: The ID given by the Synchronize Player Position packet.
    :type teleport_id: int
    """

    PACKET_ID: ClassVar[int] = 0x00
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    teleport_id: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.teleport_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        teleport_id = buf.read_varint()
        return cls(teleport_id=teleport_id)


@final
@define
class BlockEntityTagQuery(ServerBoundPacket):
    """Used when F3+I is pressed while looking at a block. (Client -> Server).

    Initialize the BlockEntityTagQuery packet.

    :param transaction_id: An incremental ID so that the client can verify that the response matches.
    :type transaction_id: int
    :param location: The location of the block to check.
    :type location: :class:`~mcproto.types.Position`
    """

    PACKET_ID: ClassVar[int] = 0x01
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    transaction_id: int
    location: Position

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.transaction_id)
        self.location.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        transaction_id = buf.read_varint()
        location = Position.deserialize(buf)
        return cls(transaction_id=transaction_id, location=location)


@final
@define
class ChangeDifficulty(ServerBoundPacket):
    """Change the difficulty of the world. (Client -> Server).

    Must have at least op level 2 to use. Appears to only be used on singleplayer; the difficulty buttons are still
    disabled in multiplayer.

    Initialize the ChangeDifficulty packet.

    :param new_difficulty: The new difficulty level. 0: peaceful, 1: easy, 2: normal, 3: hard.
    :type new_difficulty: int
    """

    PACKET_ID: ClassVar[int] = 0x02
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    new_difficulty: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.BYTE, self.new_difficulty)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        new_difficulty = buf.read_value(StructFormat.BYTE)
        return cls(new_difficulty=new_difficulty)


@final
@define
class ChatAck(ServerBoundPacket):
    """Acknowledges receipt of a message from the server. (Client -> Server).

    Initialize the ChatAck packet.

    :param message_count: The message count sent by the server.
    :type message_count: int
    """

    PACKET_ID: ClassVar[int] = 0x03
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    message_count: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.message_count)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        message_count = buf.read_varint()
        return cls(message_count=message_count)


@final
@define
class ChatCommand(ServerBoundPacket):
    """Sends a chat command from the client to the server. (Client -> Server).

    Initialize the ChatCommand packet.

    :param command: The command typed by the client.
    :type command: str
    """

    PACKET_ID: ClassVar[int] = 0x04
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    command: str

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_utf(self.command)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        command = buf.read_utf()
        return cls(command=command)


@final
@define
class ChatCommandSigned(ServerBoundPacket):
    """Used to send a signed chat command to the server. (Client -> Server).

    Initialize the ChatCommandSigned packet.

    :param command: The command typed by the client.
    :type command: str
    :param timestamp: The timestamp that the command was executed.
    :type timestamp: int
    :param salt: The salt for the following argument signatures.
    :type salt: int
    :param arguments: A list of tuples containing the argument name and signature.
    :type arguments: list[tuple[str, bytes]]
    :param message_count: The message count.
    :type message_count: int
    :param acknowledged: The acknowledged bitset.
    :type acknowledged: :class:`~mcproto.types.FixedBitset[20]`
    """

    PACKET_ID: ClassVar[int] = 0x05
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    command: str
    timestamp: int
    salt: int
    arguments: list[tuple[str, bytes]]
    message_count: int
    acknowledged: FixedBitset[20]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_utf(self.command)
        buf.write_value(StructFormat.LONGLONG, self.timestamp)
        buf.write_value(StructFormat.LONGLONG, self.salt)
        buf.write_varint(len(self.arguments))
        for name, signature in self.arguments:
            buf.write_utf(name)
            buf.write(signature)
        buf.write_varint(self.message_count)
        self.acknowledged.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        command = buf.read_utf()
        timestamp = buf.read_value(StructFormat.LONGLONG)
        salt = buf.read_value(StructFormat.LONGLONG)
        count = buf.read_varint()
        arguments: list[tuple[str, bytes]] = []
        for _ in range(count):
            name = buf.read_utf()
            signature = bytes(buf.read(256))
            arguments.append((name, signature))
        message_count = buf.read_varint()
        acknowledged = FixedBitset.of_size(20).deserialize(buf)
        return cls(
            command=command,
            timestamp=timestamp,
            salt=salt,
            arguments=arguments,
            message_count=message_count,
            acknowledged=acknowledged,
        )


@final
@define
class Chat(ServerBoundPacket):
    """Used to send a chat message to the server. (Client -> Server).

    The server will broadcast a Player Chat Message packet with Chat Type minecraft:chat to all players that
    haven't disabled chat (including the player that sent the message).

    Initialize the Chat packet.

    :param message: The chat message.
    :type message: str
    :param timestamp: The timestamp of the message.
    :type timestamp: int
    :param salt: The salt used to verify the signature.
    :type salt: int
    :param has_signature: Whether the next field is present.
    :type has_signature: bool
    :param signature: The signature used to verify the chat message's authentication. When present, always 256 bytes
    and not length-prefixed.
    :type signature: bytes | None
    :param message_count: The message count.
    :type message_count: int
    :param acknowledged: The acknowledged bitset.
    :type acknowledged: bytes
    """

    PACKET_ID: ClassVar[int] = 0x06
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    message: str = field()
    timestamp: int = field()
    salt: int = field()
    signature: bytes | None = field(validator=validators.optional([validators.max_len(256), validators.min_len(256)]))
    message_count: int = field()
    acknowledged: FixedBitset[20] = field()

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_utf(self.message)
        buf.write_value(StructFormat.LONGLONG, self.timestamp)
        buf.write_value(StructFormat.LONGLONG, self.salt)
        buf.write_optional(self.signature, buf.write)
        buf.write_varint(self.message_count)
        self.acknowledged.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        message = buf.read_utf()
        timestamp = buf.read_value(StructFormat.LONGLONG)
        salt = buf.read_value(StructFormat.LONGLONG)
        signature = buf.read_optional(lambda: bytes(buf.read(256)))
        message_count = buf.read_varint()
        acknowledged = FixedBitset.of_size(20).deserialize(buf)
        return cls(
            message=message,
            timestamp=timestamp,
            salt=salt,
            signature=signature,
            message_count=message_count,
            acknowledged=acknowledged,
        )


@final
@define
class ChatSessionUpdate(ServerBoundPacket):
    """Sets the cryptographic ID of the player to create a session. (Client -> Server).

    Initialize the ChatSessionUpdate packet.

    :param session_id: The session ID.
    :type session_id: :class:`mcproto.types.UUID`
    :param expires: The time the play session key expires in epoch milliseconds.
    :type expires: int
    :param public_key: The public key (A byte array of an X.509-encoded public key).
    :type public_key: bytes
    :param signature: The player UUID, the key expiration timestamp, and the public key data. These values are hashed
    using SHA-1 and signed using Mojang's private RSA key.
    :type signature: bytes
    """

    GAME_STATE: ClassVar[GameState] = GameState.PLAY
    PACKET_ID: ClassVar[int] = 0x07

    session_id: UUID
    expires: int
    public_key: bytes
    signature: bytes

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.session_id.serialize_to(buf)
        buf.write_value(StructFormat.LONGLONG, self.expires)
        buf.write_bytearray(self.public_key)
        buf.write_bytearray(self.signature)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        session_id = UUID.deserialize(buf)
        expires = buf.read_value(StructFormat.LONGLONG)
        public_key = bytes(buf.read_bytearray())
        signature = bytes(buf.read_bytearray())
        return cls(session_id=session_id, expires=expires, public_key=public_key, signature=signature)


@final
@define
class ChunkBatchReceived(ServerBoundPacket):
    """Notifies the server that the chunk batch has been received by the client. (Client -> Server).

    The server uses the value sent in this packet to adjust the number of chunks to be sent in a batch.

    Initialize the ChunkBatchReceived packet.

    :param chunks_per_tick: Desired chunks per tick.
    :type chunks_per_tick: float
    """

    PACKET_ID: ClassVar[int] = 0x08
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    chunks_per_tick: float

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.FLOAT, self.chunks_per_tick)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        chunks_per_tick = buf.read_value(StructFormat.FLOAT)
        return cls(chunks_per_tick=chunks_per_tick)


class ClientCommandAction(IntEnum):
    """An action for the Client Status Packet."""

    PERFORM_RESPAWN = 0
    REQUEST_STATS = 1


@final
@define
class ClientCommand(ServerBoundPacket):
    """Used to send client status to the server. (Client -> Server).

    Initialize the ClientCommand packet.

    :param action_id: The action ID.
    :type action_id: :class:`ClientCommandAction`
    """

    PACKET_ID: ClassVar[int] = 0x09
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    action_id: ClientCommandAction

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.action_id.value)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        action_id = ClientCommandAction(buf.read_varint())
        return cls(action_id=action_id)


class ChatMode(IntEnum):
    """The chat mode for the Client Information Packet."""

    ENABLED = 0
    COMMANDS_ONLY = 1
    HIDDEN = 2


class MainHand(IntEnum):
    """The main hand for the Client Information Packet."""

    LEFT = 0
    RIGHT = 1


class DisplayedSkinParts(NamedTuple):
    """The displayed skin parts for the Client Information Packet."""

    cape: bool
    jacket: bool
    left_sleeve: bool
    right_sleeve: bool
    left_pants: bool
    right_pants: bool
    hat: bool


@final
@define
class ClientInformation(ServerBoundPacket):
    """Sent when the player connects, or when settings are changed. (Client -> Server).

    Initialize the ClientInformation packet.

    :param locale: The locale of the client.
    :type locale: str
    :param view_distance: The client-side render distance, in chunks.
    :type view_distance: int
    :param chat_mode: The chat mode.
    :type chat_mode: :class:`ChatMode`
    :param chat_colors: Whether the chat can be colored.
    :type chat_colors: bool
    :param displayed_skin_parts: Which skin parts are displayed.
    :type displayed_skin_parts: :class:`DisplayedSkinParts`
    :param main_hand: The main hand.
    :type main_hand: :class:`MainHand`
    :param enable_text_filtering: Whether to enable filtering of text on signs and written book titles.
    :type enable_text_filtering: bool
    :param allow_server_listings: Whether to allow server listings.
    :type allow_server_listings: bool
    """

    PACKET_ID: ClassVar[int] = 0x0A
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    locale: str
    view_distance: int
    chat_mode: ChatMode
    chat_colors: bool
    displayed_skin_parts: DisplayedSkinParts
    main_hand: MainHand
    enable_text_filtering: bool
    allow_server_listings: bool

    @staticmethod
    def from_displayed_skin_parts(parts: DisplayedSkinParts) -> int:
        """Convert a :class:`DisplayedSkinParts` instance to an integer."""
        return sum(int(part) << i for i, part in enumerate(parts))

    @staticmethod
    def to_displayed_skin_parts(parts: int) -> DisplayedSkinParts:
        """Convert an integer to a :class:`DisplayedSkinParts` instance."""
        return DisplayedSkinParts(*(bool(parts & (1 << i)) for i in range(7)))

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_utf(self.locale)
        buf.write_value(StructFormat.BYTE, self.view_distance)
        buf.write_varint(self.chat_mode.value)
        buf.write_value(StructFormat.BOOL, self.chat_colors)
        buf.write_value(StructFormat.UBYTE, self.from_displayed_skin_parts(self.displayed_skin_parts))
        buf.write_varint(self.main_hand.value)
        buf.write_value(StructFormat.BOOL, self.enable_text_filtering)
        buf.write_value(StructFormat.BOOL, self.allow_server_listings)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        locale = buf.read_utf()
        view_distance = buf.read_value(StructFormat.BYTE)
        chat_mode = ChatMode(buf.read_varint())
        chat_colors = buf.read_value(StructFormat.BOOL)
        displayed_skin_parts = cls.to_displayed_skin_parts(buf.read_value(StructFormat.UBYTE))
        main_hand = MainHand(buf.read_varint())
        enable_text_filtering = buf.read_value(StructFormat.BOOL)
        allow_server_listings = buf.read_value(StructFormat.BOOL)
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
class CommandSuggestion(ServerBoundPacket):
    """Sent when the client needs to tab-complete a minecraft:ask_server suggestion type. (Client -> Server).

    Initialize the CommandSuggestion packet.

    :param transaction_id: The id of the transaction that the server will send back to the client in the response of
    this packet.
    :type transaction_id: int
    :param text: All text behind the cursor without the / (e.g. to the left of the cursor in left-to-right languages
    like English).
    :type text: str
    """

    PACKET_ID: ClassVar[int] = 0x0B
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    transaction_id: int = field()
    text: str = field(validator=validators.max_len(32500))

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.transaction_id)
        buf.write_utf(self.text)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        transaction_id = buf.read_varint()
        text = buf.read_utf()
        return cls(transaction_id=transaction_id, text=text)


@final
@define
class ConfigurationAcknowledged(ServerBoundPacket):
    """Sent by the client upon receiving a Start Configuration packet from the server. (Client -> Server).

    This packet switches the connection state to configuration.

    Initialize the ConfigurationAcknowledged packet.
    """

    PACKET_ID: ClassVar[int] = 0x0C
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    @override
    def serialize_to(self, buf: Buffer) -> None:
        pass

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        return cls()


@final
@define
class ContainerButtonClick(ServerBoundPacket):
    """Used when clicking on window buttons. (Client -> Server).

    Until 1.14, this was only used by enchantment tables.

    Initialize the ContainerButtonClick packet.

    :param window_id: The ID of the window sent by Open Screen.
    :type window_id: int
    :param button_id: The ID of the button clicked. The meaning depends on the window type.
    :type button_id: int

    .. seealso:: <https://wiki.vg/Protocol#Click_Container Button> for which button IDs are used for which windows.
    """

    PACKET_ID: ClassVar[int] = 0x0D
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    window_id: int
    button_id: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.BYTE, self.window_id)
        buf.write_value(StructFormat.BYTE, self.button_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        window_id = buf.read_value(StructFormat.BYTE)
        button_id = buf.read_value(StructFormat.BYTE)
        return cls(window_id=window_id, button_id=button_id)


class ClickMode(IntEnum):
    """The click mode for the Click Container Packet."""

    NORMAL = 0
    SHIFT = 1
    NUMBER_KEY = 2
    MIDDLE_CLICK = 3
    DROP_KEY = 4
    DRAG = 5
    DOUBLE_CLICK = 6


@final
@define
class ContainerClick(ServerBoundPacket):
    """Sent by the client when the player clicks on a slot in a window. (Client -> Server).

    Initialize the ContainerClick packet.

    :param window_id: The ID of the window which was clicked. 0 for player inventory.
    :type window_id: int
    :param state_id: The last received State ID from either a Set Container Slot or a Set Container Content packet.
    :type state_id: int
    :param slot: The clicked slot number.
    :type slot: int
    :param button: The button used in the click.
    :type button: int
    :param mode: The inventory operation mode.
    :type mode: :class:`ClickMode`
    :param changed_slots: A list of tuples containing the slot number and new data for this slot.
    :type changed_slots: list[tuple[int, Slot]]
    :param carried_item: The item carried by the cursor. Has to be empty (item ID = -1) for drop mode, otherwise
    nothing will happen.
    :type carried_item: :class:`~mcproto.types.Slot`
    """

    PACKET_ID: ClassVar[int] = 0x0E
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    window_id: int
    state_id: int
    slot: int
    button: int
    mode: ClickMode
    changed_slots: list[tuple[int, Slot]]
    carried_item: Slot

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.UBYTE, self.window_id)
        buf.write_varint(self.state_id)
        buf.write_value(StructFormat.SHORT, self.slot)
        buf.write_value(StructFormat.BYTE, self.button)
        buf.write_varint(self.mode.value)
        buf.write_varint(len(self.changed_slots))
        for slot_number, slot_data in self.changed_slots:
            buf.write_value(StructFormat.SHORT, slot_number)
            slot_data.serialize_to(buf)
        self.carried_item.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        window_id = buf.read_value(StructFormat.UBYTE)
        state_id = buf.read_varint()
        slot = buf.read_value(StructFormat.SHORT)
        button = buf.read_value(StructFormat.BYTE)
        mode = ClickMode(buf.read_varint())
        changed_slots: list[tuple[int, Slot]] = []
        for _ in range(buf.read_varint()):
            slot_number = buf.read_value(StructFormat.SHORT)
            slot_data = Slot.deserialize(buf)
            changed_slots.append((slot_number, slot_data))
        carried_item = Slot.deserialize(buf)
        return cls(
            window_id=window_id,
            state_id=state_id,
            slot=slot,
            button=button,
            mode=mode,
            changed_slots=changed_slots,
            carried_item=carried_item,
        )


@final
@define
class ContainerClose(ServerBoundPacket):
    """Sent by the client when closing a window. (Client -> Server).

    Initialize the ContainerClose packet.

    :param window_id: The ID of the window that was closed. 0 for player inventory.
    :type window_id: int
    """

    PACKET_ID: ClassVar[int] = 0x0F
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    window_id: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.UBYTE, self.window_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        window_id = buf.read_value(StructFormat.UBYTE)
        return cls(window_id=window_id)


@final
@define
class ContainerSlotStateChanged(ServerBoundPacket):
    """Sent by the client when toggling the state of a Crafter. (Client -> Server).

    Initialize the ContainerSlotStateChanged packet.

    :param slot_id: The ID of the slot that was changed.
    :type slot_id: int
    :param window_id: The ID of the window that was changed.
    :type window_id: int
    :param state: The new state of the slot. True for enabled, false for disabled.
    :type state: bool
    """

    PACKET_ID: ClassVar[int] = 0x10
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    slot_id: int
    window_id: int
    state: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.slot_id)
        buf.write_varint(self.window_id)
        buf.write_value(StructFormat.BOOL, self.state)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        slot_id = buf.read_varint()
        window_id = buf.read_varint()
        state = buf.read_value(StructFormat.BOOL)
        return cls(slot_id=slot_id, window_id=window_id, state=state)


@final
@define
class CookieResponse(ServerBoundPacket):
    """Response to a Cookie Request (play) from the server. (Client -> Server).

    The Notchian server only accepts responses of up to 5 kiB in size.

    Initialize the CookieResponse packet.

    :param key: The identifier of the cookie.
    :type key: bytes
    :param payload: The data of the cookie, if any.
    :type payload: bytes | None
    """

    PACKET_ID: ClassVar[int] = 0x11
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

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
    """Mods and plugins can use this to send their data. (Client -> Server).

    Initialize the ServerboundCustomPayload packet.

    :param channel: The name of the plugin channel used to send the data.
    :type channel: str
    :param data: Any data, depending on the channel.
    :type data: bytes
    """

    PACKET_ID: ClassVar[int] = 0x12
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

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
class DebugSampleSubscription(ServerBoundPacket):
    """Subscribes to the specified type of debug sample data. (Client -> Server).

    The Notchian server only allows subscriptions from players that are server operators.

    Initialize the DebugSampleSubscription packet.

    :param sample_type: The type of debug sample to subscribe to.
    :type sample_type: :class:`DebugSampleType`
    """

    PACKET_ID: ClassVar[int] = 0x13
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    sample_type: DebugSampleType

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.sample_type.value)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        sample_type = DebugSampleType(buf.read_varint())
        return cls(sample_type=sample_type)


@final
@define
class EditBook(ServerBoundPacket):
    """Used when a player edits a book. (Client -> Server).

    Initialize the EditBook packet.

    :param slot: The hotbar slot where the written book is located.
    :type slot: int
    :param entries: The text from each page.
    :type entries: list[str]
    :param title: The title of the book.
    :type title: str | None
    """

    PACKET_ID: ClassVar[int] = 0x14
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    slot: int = field()
    entries: list[str] = field(validator=[validators.max_len(200), validators.deep_iterable(validators.max_len(8192))])
    title: str | None = field(validator=validators.optional([validators.max_len(128)]))

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.slot)
        buf.write_varint(len(self.entries))
        for entry in self.entries:
            buf.write_utf(entry)
        buf.write_optional(self.title, buf.write_utf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        slot = buf.read_varint()
        entries: list[str] = [buf.read_utf() for _ in range(buf.read_varint())]
        title = buf.read_optional(buf.read_utf)
        return cls(slot=slot, entries=entries, title=title)


@final
@define
class EntityTagQuery(ServerBoundPacket):
    """Used when F3+I is pressed while looking at an entity. (Client -> Server).

    Initialize the EntityTagQuery packet.

    :param transaction_id: An incremental ID so that the client can verify that the response matches.
    :type transaction_id: int
    :param entity_id: The ID of the entity to query.
    :type entity_id: int
    """

    PACKET_ID: ClassVar[int] = 0x15
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    transaction_id: int
    entity_id: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.transaction_id)
        buf.write_varint(self.entity_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        transaction_id = buf.read_varint()
        entity_id = buf.read_varint()
        return cls(transaction_id=transaction_id, entity_id=entity_id)


class InteractType(IntEnum):
    """The type of interaction for the Interact Packet."""

    INTERACT = 0
    ATTACK = 1
    INTERACT_AT = 2


class Hand(IntEnum):
    """The hand used for the Interact Packet."""

    MAIN_HAND = 0
    OFF_HAND = 1


@final
@define
class Interact(ServerBoundPacket):
    """Sent from the client to the server when the client attacks or right-clicks another entity. (Client -> Server).

    Initialize the Interact packet.

    :param entity_id: The ID of the entity to interact.
    :type entity_id: int
    :param interact_type: The type of interaction.
    :type interact_type: :class:`InteractType`
    :param target: The coordinates of the target, if the interaction type is INTERACT_AT.
    :type target: Vec3 | None
    :param hand: The hand used for the interaction, if the interaction type is INTERACT or INTERACT_AT.
    :type hand: :class:`Hand` | None
    :param sneaking: Whether the client is sneaking.
    :type sneaking: bool

    .. note:: For the Ender Dragon, you can only interact with the hitboxes designated as `entity_id+1` through
    `entity_id+8` in this order : Head, Neck, Body, Tail 1, Tail 2, Tail 3, Wing 1, Wing 2.
    """

    PACKET_ID: ClassVar[int] = 0x16
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    interact_type: InteractType
    target: Vec3 | None
    hand: Hand | None
    sneaking: bool

    def __attrs_post_init__(self):
        if self.interact_type == InteractType.INTERACT_AT and self.target is None:
            raise ValueError("target_x, target_y, and target_z must be set for INTERACT_AT")
        if self.interact_type in (InteractType.INTERACT, InteractType.INTERACT_AT):
            if self.hand is None:
                raise ValueError("hand must be set for INTERACT and INTERACT_AT")

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_varint(self.interact_type.value)
        if self.interact_type == InteractType.INTERACT_AT:
            self.target = cast(Vec3, self.target)
            self.target.serialize_to(buf)
        if self.interact_type in (InteractType.INTERACT, InteractType.INTERACT_AT):
            self.hand = cast(Hand, self.hand)
            buf.write_varint(self.hand.value)
        buf.write_value(StructFormat.BOOL, self.sneaking)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        interact_type = InteractType(buf.read_varint())
        target = None
        if interact_type == InteractType.INTERACT_AT:
            target = Vec3.deserialize(buf)
        hand = None
        if interact_type in (InteractType.INTERACT, InteractType.INTERACT_AT):
            hand = Hand(buf.read_varint())
        sneaking = buf.read_value(StructFormat.BOOL)
        return cls(
            entity_id=entity_id,
            interact_type=interact_type,
            target=target,
            hand=hand,
            sneaking=sneaking,
        )


@final
@define
class JigsawGenerate(ServerBoundPacket):
    """Sent when Generate is pressed on the Jigsaw Block interface. (Client -> Server).

    Initialize the JigsawGenerate packet.

    :param location: The block entity location.
    :type location: :class:`Position`
    :param levels: The value of the levels slider/max depth to generate.
    :type levels: int
    :param keep_jigsaws: Whether to keep jigsaws.
    :type keep_jigsaws: bool
    """

    PACKET_ID: ClassVar[int] = 0x17
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    location: Position
    levels: int
    keep_jigsaws: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.location.serialize_to(buf)
        buf.write_varint(self.levels)
        buf.write_value(StructFormat.BOOL, self.keep_jigsaws)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        location = Position.deserialize(buf)
        levels = buf.read_varint()
        keep_jigsaws = buf.read_value(StructFormat.BOOL)
        return cls(location=location, levels=levels, keep_jigsaws=keep_jigsaws)


@final
@define
class KeepAlive(ServerBoundPacket):
    """Keep the connection alive. (Client -> Server).

    The server will frequently send out a keep-alive, each containing a random ID. The client must respond with the
    same packet. (Client -> Server).

    Initialize the ServerboundKeepAlive packet.

    :param keep_alive_id: The keep-alive ID.
    :type keep_alive_id: int
    """

    PACKET_ID: ClassVar[int] = 0x18
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    keep_alive_id: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.LONG, self.keep_alive_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        keep_alive_id = buf.read_value(StructFormat.LONG)
        return cls(keep_alive_id=keep_alive_id)


@final
@define
class LockDifficulty(ServerBoundPacket):
    """Lock the difficulty button in the pause menu. (Client -> Server).

    Must have at least op level 2 to use. Appears to only be used on singleplayer; the difficulty buttons are still
    disabled in multiplayer. (Client -> Server).

    Initialize the LockDifficulty packet.

    :param locked: Whether the difficulty is locked.
    :type locked: bool
    """

    PACKET_ID: ClassVar[int] = 0x19
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    locked: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.BOOL, self.locked)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        locked = buf.read_value(StructFormat.BOOL)
        return cls(locked=locked)


@final
@define
class MovePlayerPos(ServerBoundPacket):
    """Updates the player's XYZ position on the server. (Client -> Server).

    Initialize the MovePlayerPos packet.

    :param feet_position: The absolute feet position.
    :type feet_position: :class:`Vec3`
    :param on_ground: Whether the client is on the ground.
    :type on_ground: bool
    """

    PACKET_ID: ClassVar[int] = 0x1A
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    EYES_POSITION: ClassVar[Vec3] = Vec3(0, 1.62, 0)

    feet_position: Vec3
    on_ground: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.feet_position.serialize_to_double(buf)
        buf.write_value(StructFormat.BOOL, self.on_ground)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        feet_position = Vec3.deserialize_double(buf)
        on_ground = buf.read_value(StructFormat.BOOL)
        return cls(feet_position=feet_position, on_ground=on_ground)

    @classmethod
    def from_position(cls, position: Vec3, on_ground: bool) -> Self:
        """Create a MovePlayerPos packet from a :class:`Position` instance.

        .. note:: The y value of the position is the head position, so the feet position is calculated by subtracting
        1.62 from the y value.
        """
        return cls(feet_position=position - cls.EYES_POSITION, on_ground=on_ground)

    def to_position(self) -> Vec3:
        """Convert the MovePlayerPos packet to a :class:`Position` instance (head position)."""
        return self.feet_position + self.EYES_POSITION


@define
class MovePlayerPosRot(ServerBoundPacket):
    """A combination of Move Player Rotation and Move Player Position. (Client -> Server).

    Initialize the MovePlayerPosRot packet.

    :param feet_position: The absolute feet position.
    :type feet_position: :class:`Vec3`
    :param yaw: The absolute rotation on the X axis, in degrees.
    :type yaw: float
    :param pitch: The absolute rotation on the Y axis, in degrees.
    :type pitch: float
    :param on_ground: Whether the client is on the ground.
    :type on_ground: bool
    """

    PACKET_ID: ClassVar[int] = 0x1B
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    EYES_POSITION: ClassVar[Vec3] = Vec3(0, 1.62, 0)

    feet_position: Vec3
    yaw: float
    pitch: float
    on_ground: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.feet_position.serialize_to_double(buf)
        buf.write_value(StructFormat.FLOAT, self.yaw)
        buf.write_value(StructFormat.FLOAT, self.pitch)
        buf.write_value(StructFormat.BOOL, self.on_ground)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        feet_position = Vec3.deserialize_double(buf)
        yaw = buf.read_value(StructFormat.FLOAT)
        pitch = buf.read_value(StructFormat.FLOAT)
        on_ground = buf.read_value(StructFormat.BOOL)
        return cls(feet_position=feet_position, yaw=yaw, pitch=pitch, on_ground=on_ground)

    @classmethod
    def look_at(cls, head_position: Vec3, target_position: Vec3, on_ground: bool = True) -> Self:
        """Look at a target position from the head position."""
        d = target_position - head_position
        r = d.norm()
        yaw = math.degrees(-math.atan2(d.x, d.z)) % 360
        pitch = math.degrees(-math.asin(d.y / r))
        return cls(feet_position=head_position - cls.EYES_POSITION, yaw=yaw, pitch=pitch, on_ground=on_ground)

    @classmethod
    def from_position(cls, position: Vec3, yaw: float, pitch: float, on_ground: bool) -> Self:
        """Create a MovePlayerPosRot packet from a :class:`Position` instance.

        .. note:: The y value of the position is the head position, so the feet position is calculated by subtracting
        1.62.
        """
        return cls(feet_position=position - cls.EYES_POSITION, yaw=yaw, pitch=pitch, on_ground=on_ground)

    def to_position(self) -> Vec3:
        """Convert the MovePlayerPos packet to a :class:`Position` instance (head position)."""
        return self.feet_position + self.EYES_POSITION


@final
@define
class MovePlayerRot(ServerBoundPacket):
    """Updates the direction the player is looking in. (Client -> Server).

    Initialize the MovePlayerRot packet.

    :param yaw: The absolute rotation on the X axis, in degrees.
    :type yaw: float
    :param pitch: The absolute rotation on the Y axis, in degrees.
    :type pitch: float
    :param on_ground: Whether the client is on the ground.
    :type on_ground: bool
    """

    PACKET_ID: ClassVar[int] = 0x1C
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    yaw: float
    pitch: float
    on_ground: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.FLOAT, self.yaw)
        buf.write_value(StructFormat.FLOAT, self.pitch)
        buf.write_value(StructFormat.BOOL, self.on_ground)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        yaw = buf.read_value(StructFormat.FLOAT)
        pitch = buf.read_value(StructFormat.FLOAT)
        on_ground = buf.read_value(StructFormat.BOOL)
        return cls(yaw=yaw, pitch=pitch, on_ground=on_ground)

    @classmethod
    def look_at(cls, head_position: Vec3, target_position: Vec3, on_ground: bool = True) -> Self:
        """Look at a target position from the head position."""
        d = target_position - head_position
        r = d.norm()
        yaw = math.degrees(-math.atan2(d.x, d.z)) % 360
        pitch = math.degrees(-math.asin(d.y / r))
        return cls(yaw=yaw, pitch=pitch, on_ground=on_ground)


@final
@define
class MovePlayerStatusOnly(ServerBoundPacket):
    """Indicates whether the player is on ground (walking/swimming), or airborne (jumping/falling). (Client -> Server).

    Initialize the MovePlayerStatusOnly packet.

    :param on_ground: Whether the client is on the ground.
    :type on_ground: bool
    """

    PACKET_ID: ClassVar[int] = 0x1D
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    on_ground: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.BOOL, self.on_ground)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        on_ground = buf.read_value(StructFormat.BOOL)
        return cls(on_ground=on_ground)


@final
@define
class MoveVehicle(ServerBoundPacket):
    """Sent when a player moves in a vehicle. (Client -> Server).

    Initialize the MoveVehicle packet.

    :param position: The absolute position of the vehicle.
    :type position: :class:`Vec3`
    :param yaw: The absolute rotation on the vertical axis, in degrees.
    :type yaw: float
    :param pitch: The absolute rotation on the horizontal axis, in degrees.
    :type pitch: float
    """

    PACKET_ID: ClassVar[int] = 0x1E
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    position: Vec3
    yaw: float
    pitch: float

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.position.serialize_to_double(buf)
        buf.write_value(StructFormat.FLOAT, self.yaw)
        buf.write_value(StructFormat.FLOAT, self.pitch)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        position = Vec3.deserialize_double(buf)
        yaw = buf.read_value(StructFormat.FLOAT)
        pitch = buf.read_value(StructFormat.FLOAT)
        return cls(position=position, yaw=yaw, pitch=pitch)


@final
@define
class PaddleBoat(ServerBoundPacket):
    """Used to visually update whether boat paddles are turning. (Client -> Server).

    Initialize the PaddleBoat packet.

    :param left_paddle_turning: Whether the left paddle is turning.
    :type left_paddle_turning: bool
    :param right_paddle_turning: Whether the right paddle is turning.
    :type right_paddle_turning: bool
    """

    PACKET_ID: ClassVar[int] = 0x1F
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    left_paddle_turning: bool
    right_paddle_turning: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.BOOL, self.left_paddle_turning)
        buf.write_value(StructFormat.BOOL, self.right_paddle_turning)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        left_paddle_turning = buf.read_value(StructFormat.BOOL)
        right_paddle_turning = buf.read_value(StructFormat.BOOL)
        return cls(left_paddle_turning=left_paddle_turning, right_paddle_turning=right_paddle_turning)


@final
@define
class PickItem(ServerBoundPacket):
    """Used to swap out an empty space on the hotbar with the item in the given inventory slot. (Client -> Server).

    Initialize the PickItem packet.

    :param slot_to_use: The slot to use. See Inventory.
    :type slot_to_use: int
    """

    PACKET_ID: ClassVar[int] = 0x20
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    slot_to_use: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.slot_to_use)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        slot_to_use = buf.read_varint()
        return cls(slot_to_use=slot_to_use)


@final
@define
class PingRequest(ServerBoundPacket):
    """Sent by the client to request a Ping Response from the server. (Client -> Server).

    Initialize the PingRequest packet.

    :param payload: The payload. May be any number. Notchian clients use a system-dependent time value which is counted
    in milliseconds.
    :type payload: int
    """

    PACKET_ID: ClassVar[int] = 0x21
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    payload: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.LONGLONG, self.payload)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        payload = buf.read_value(StructFormat.LONGLONG)
        return cls(payload=payload)


@final
@define
class PlaceRecipe(ServerBoundPacket):
    """A player clicks a recipe in the crafting book that is craftable (white border). (Client -> Server).

    Initialize the PlaceRecipe packet.

    :param window_id: The window ID.
    :type window_id: int
    :param recipe: The recipe ID.
    :type recipe: :class:`Identifier`
    :param make_all: Whether to make all items. True if shift is down when clicked.
    :type make_all: bool
    """

    PACKET_ID: ClassVar[int] = 0x22
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    window_id: int
    recipe: Identifier
    make_all: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.BYTE, self.window_id)
        self.recipe.serialize_to(buf)
        buf.write_value(StructFormat.BOOL, self.make_all)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        window_id = buf.read_value(StructFormat.BYTE)
        recipe = Identifier.deserialize(buf)
        make_all = buf.read_value(StructFormat.BOOL)
        return cls(window_id=window_id, recipe=recipe, make_all=make_all)


@final
@define
class PlayerAbilities(ServerBoundPacket):
    """Announces to the server that the client is flying with elytras. (Client -> Server).

    Initialize the PlayerAbilities packet.

    :param flying: Whether the client is flying.
    :type flying: bool
    """

    PACKET_ID: ClassVar[int] = 0x23
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    flying: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        flags = 0
        flags |= 0x02 if self.flying else 0
        buf.write_value(StructFormat.BYTE, flags)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        flags = buf.read_value(StructFormat.BYTE)
        flying = bool(flags & 0x02)
        return cls(flying=flying)


class PlayerActionStatus(IntEnum):
    """The action the player is taking against the block for the Player Action Packet."""

    STARTED_DIGGING = 0
    CANCELLED_DIGGING = 1
    FINISHED_DIGGING = 2
    DROP_ITEM_STACK = 3
    DROP_ITEM = 4
    SHOOT_ARROW_OR_FINISH_EATING = 5
    SWAP_ITEM_IN_HAND = 6


class BlockFace(IntEnum):
    """The face being hit for the Player Action Packet."""

    BOTTOM = 0
    TOP = 1
    NORTH = 2
    SOUTH = 3
    WEST = 4
    EAST = 5


@final
@define
class PlayerAction(ServerBoundPacket):
    """Sent when the player mines a block. (Client -> Server).

    A Notchian server only accepts digging packets with coordinates within a 6-unit radius between the center of the
    block and the player's eyes.

    Initialize the PlayerAction packet.

    :param status: The action the player is taking against the block.
    :type status: :class:`PlayerActionStatus`
    :param location: The block position.
    :type location: :class:`~mcproto.types.Position`
    :param face: The face being hit.
    :type face: :class:`BlockFace`
    :param sequence: The block change sequence number.
    :type sequence: int
    """

    PACKET_ID: ClassVar[int] = 0x24
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    status: PlayerActionStatus
    location: Position
    face: BlockFace
    sequence: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.status.value)
        self.location.serialize_to(buf)
        buf.write_value(StructFormat.BYTE, self.face.value)
        buf.write_varint(self.sequence)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        status = PlayerActionStatus(buf.read_varint())
        location = Position.deserialize(buf)
        face = BlockFace(buf.read_value(StructFormat.BYTE))
        sequence = buf.read_varint()
        return cls(status=status, location=location, face=face, sequence=sequence)


class PlayerActionID(IntEnum):
    """The ID of the action for the Player Command Packet."""

    START_SNEAKING = 0
    STOP_SNEAKING = 1
    LEAVE_BED = 2
    START_SPRINTING = 3
    STOP_SPRINTING = 4
    START_JUMP_WITH_HORSE = 5
    STOP_JUMP_WITH_HORSE = 6
    OPEN_VEHICLE_INVENTORY = 7
    START_FLYING_WITH_ELYTRA = 8


@final
@define
class PlayerCommand(ServerBoundPacket):
    """Sent by the client to indicate that it has performed certain actions. (Client -> Server).

    Initialize the PlayerCommand packet.

    :param entity_id: The player ID.
    :type entity_id: int
    :param action_id: The ID of the action.
    :type action_id: :class:`PlayerActionID`
    :param jump_boost: The jump boost, only used by the “start jump with horse” action.
    :type jump_boost: int
    """

    PACKET_ID: ClassVar[int] = 0x25
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    action_id: PlayerActionID
    jump_boost: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_varint(self.action_id.value)
        buf.write_varint(self.jump_boost)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        action_id = PlayerActionID(buf.read_varint())
        jump_boost = buf.read_varint()
        return cls(entity_id=entity_id, action_id=action_id, jump_boost=jump_boost)


@final
@define
class PlayerInput(ServerBoundPacket):
    """Sent by the client to indicate the player's movement and actions. (Client -> Server).

    Initialize the PlayerInput packet.

    :param sideways: Positive to the left of the player.
    :type sideways: float
    :param forward: Positive forward.
    :type forward: float
    :param jump: Whether the player is jumping.
    :type jump: bool
    :param unmount: Whether the player is unmounting.
    :type unmount: bool
    """

    PACKET_ID: ClassVar[int] = 0x26
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    sideways: float
    forward: float
    jump: bool
    unmount: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.FLOAT, self.sideways)
        buf.write_value(StructFormat.FLOAT, self.forward)
        flags = 0
        flags |= 0x01 * self.jump
        flags |= 0x02 * self.unmount

        buf.write_value(StructFormat.UBYTE, flags)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        sideways = buf.read_value(StructFormat.FLOAT)
        forward = buf.read_value(StructFormat.FLOAT)
        flags = buf.read_value(StructFormat.UBYTE)
        jump = bool(flags & 0x01)
        unmount = bool(flags & 0x02)
        return cls(sideways=sideways, forward=forward, jump=jump, unmount=unmount)


@final
@define
class Pong(ServerBoundPacket):
    """Response to the clientbound packet (Ping) with the same payload. (Client -> Server).

    Initialize the Pong packet.

    :param payload: The ID of the ping packet.
    :type payload: int
    """

    PACKET_ID: ClassVar[int] = 0x27
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    payload: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.INT, self.payload)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        payload = buf.read_value(StructFormat.INT)
        return cls(payload=payload)


class RecipeBookType(IntEnum):
    """The type of recipe book."""

    CRAFTING = 0
    FURNACE = 1
    BLAST_FURNACE = 2
    SMOKER = 3


@final
@define
class RecipeBookChangeSettings(ServerBoundPacket):
    """Replaces Recipe Book Data, type 1. (Client -> Server).

    Initialize the RecipeBookChangeSettings packet.

    :param book_id: The type of recipe book.
    :type book_id: RecipeBookType
    :param book_open: Whether the recipe book is open.
    :type book_open: bool
    :param filter_active: Whether the recipe book filter is active.
    :type filter_active: bool
    """

    PACKET_ID: ClassVar[int] = 0x28
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    book_id: RecipeBookType
    book_open: bool
    filter_active: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.book_id.value)
        buf.write_value(StructFormat.BOOL, self.book_open)
        buf.write_value(StructFormat.BOOL, self.filter_active)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        book_id = RecipeBookType(buf.read_varint())
        book_open = buf.read_value(StructFormat.BOOL)
        filter_active = buf.read_value(StructFormat.BOOL)
        return cls(book_id=book_id, book_open=book_open, filter_active=filter_active)


@final
@define
class RecipeBookSeenRecipe(ServerBoundPacket):
    """Sent when recipe is first seen in recipe book. Replaces Recipe Book Data, type 0. (Client -> Server).

    Initialize the RecipeBookSeenRecipe packet.

    :param recipe_id: The ID of the recipe.
    :type recipe_id: :class:`~mcproto.types.Identifier`
    """

    PACKET_ID: ClassVar[int] = 0x29
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    recipe_id: Identifier

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.recipe_id.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        recipe_id = Identifier.deserialize(buf)
        return cls(recipe_id=recipe_id)


@final
@define
class RenameItem(ServerBoundPacket):
    """Sent as a player is renaming an item in an anvil. (Client -> Server).

    If the new name is empty, then the item loses its custom name. The item name may be no longer than 50 characters
    long, and if it is longer than that, then the rename is silently ignored.

    Initialize the RenameItem packet.

    :param item_name: The new name of the item.
    :type item_name: str
    """

    PACKET_ID: ClassVar[int] = 0x2A
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    item_name: str

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_utf(self.item_name)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        item_name = buf.read_utf()
        return cls(item_name=item_name)


class ResourcePackResult(IntEnum):
    """The result of a resource pack response."""

    SUCCESSFULLY_DOWNLOADED = 0
    DECLINED = 1
    FAILED_TO_DOWNLOAD = 2
    ACCEPTED = 3
    INVALID_URL = 4
    FAILED_TO_RELOAD = 5
    DISCARDED = 6


@final
@define
class ResourcePack(ServerBoundPacket):
    """Sent by the client in response to a resource pack request. (Client -> Server).

    Initialize the ResourcePack packet.

    :param uuid: The unique identifier of the resource pack received in the Add Resource Pack (play) request.
    :type uuid: UUID
    :param result: The result of the resource pack request.
    :type result: ResourcePackResult
    """

    PACKET_ID: ClassVar[int] = 0x2B
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    uuid: UUID
    result: ResourcePackResult

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.uuid.serialize_to(buf)
        buf.write_varint(self.result.value)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        uuid = UUID.deserialize(buf)
        result = ResourcePackResult(buf.read_varint())
        return cls(uuid=uuid, result=result)


class SeenAdvancementsAction(IntEnum):
    """The action for the Seen Advancements packet."""

    OPENED_TAB = 0
    CLOSED_SCREEN = 1


@final
@define
class SeenAdvancements(ServerBoundPacket):
    """Sent by the client to indicate that it has opened or closed an advancement tab. (Client -> Server).

    Initialize the SeenAdvancements packet.

    :param action: The action.
    :type action: SeenAdvancementsAction
    :param tab_id: The ID of the tab, if the action is OPENED_TAB.
    :type tab_id: Identifier | None
    """

    PACKET_ID: ClassVar[int] = 0x2C
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    action: SeenAdvancementsAction
    tab_id: Identifier | None

    def __attrs_post_init__(self):
        if self.action == SeenAdvancementsAction.OPENED_TAB and self.tab_id is None:
            raise ValueError("tab_id must be set for OPENED_TAB")

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.action.value)
        if self.action == SeenAdvancementsAction.OPENED_TAB:
            self.tab_id = cast(Identifier, self.tab_id)
            self.tab_id.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        action = SeenAdvancementsAction(buf.read_varint())
        tab_id = buf.read_optional(lambda: Identifier.deserialize(buf))
        return cls(action=action, tab_id=tab_id)


@final
@define
class SelectTrade(ServerBoundPacket):
    """Sent by the client to indicate that it has selected a trade with a villager NPC. (Client -> Server).

    Initialize the SelectTrade packet.

    :param selected_slot: The selected slot in the player's current inventory.
    :type selected_slot: int
    """

    PACKET_ID: ClassVar[int] = 0x2D
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    selected_slot: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.selected_slot)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        selected_slot = buf.read_varint()
        return cls(selected_slot=selected_slot)


@final
@define
class SetBeacon(ServerBoundPacket):
    """Changes the effect of the current beacon. (Client -> Server).

    Initialize the SetBeacon packet.

    :param primary_effect: The primary effect, if any.
    :type primary_effect: int | None
    :param secondary_effect: The secondary effect, if any.
    :type secondary_effect: int | None
    """

    PACKET_ID: ClassVar[int] = 0x2E
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    primary_effect: int | None
    secondary_effect: int | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_optional(self.primary_effect, buf.write_varint)
        buf.write_optional(self.secondary_effect, buf.write_varint)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        primary_effect = buf.read_optional(buf.read_varint)
        secondary_effect = buf.read_optional(buf.read_varint)
        return cls(
            primary_effect=primary_effect,
            secondary_effect=secondary_effect,
        )


@final
@define
class SetCarriedItem(ServerBoundPacket):
    """Sent when the player changes the slot selection. (Client -> Server).

    Initialize the SetCarriedItem packet.

    :param slot: The slot which the player has selected (0-8).
    :type slot: int
    """

    PACKET_ID: ClassVar[int] = 0x2F
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    slot: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.SHORT, self.slot)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        slot = buf.read_value(StructFormat.SHORT)
        return cls(slot=slot)


class CommandBlockMode(IntEnum):
    """The mode of a command block."""

    SEQUENCE = 0
    AUTO = 1
    REDSTONE = 2


@final
@define
class SetCommandBlock(ServerBoundPacket):
    """Programs a command block. (Client -> Server).

    Initialize the SetCommandBlock packet.

    :param location: The location of the command block.
    :type location: Position
    :param command: The command to be executed.
    :type command: str
    :param mode: The mode of the command block.
    :type mode: CommandBlockMode
    :param track_output: Whether the output of the previous command should be stored within the command block.
    :type track_output: bool
    :param is_conditional: Whether the command block is conditional.
    :type is_conditional: bool
    :param automatic: Whether the command block is automatic.
    :type automatic: bool

    """

    PACKET_ID: ClassVar[int] = 0x30
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    location: Position
    command: str
    mode: CommandBlockMode
    track_output: bool
    is_conditional: bool
    automatic: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.location.serialize_to(buf)
        buf.write_utf(self.command)
        buf.write_varint(self.mode.value)
        flags = 0
        flags |= 0x01 * self.track_output
        flags |= 0x02 * self.is_conditional
        flags |= 0x04 * self.automatic
        buf.write_value(StructFormat.BYTE, flags)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        location = Position.deserialize(buf)
        command = buf.read_utf()
        mode = CommandBlockMode(buf.read_varint())
        flags = buf.read_value(StructFormat.BYTE)
        track_output = bool(flags & 0x01)
        is_conditional = bool(flags & 0x02)
        automatic = bool(flags & 0x04)
        return cls(
            location=location,
            command=command,
            mode=mode,
            track_output=track_output,
            is_conditional=is_conditional,
            automatic=automatic,
        )


@final
@define
class SetCommandMinecart(ServerBoundPacket):
    """Programs a command block minecart. (Client -> Server).

    Initialize the SetCommandMinecart packet.

    :param entity_id: The entity ID of the command block minecart.
    :type entity_id: int
    :param command: The command to be executed.
    :type command: str
    :param track_output: Whether the output of the previous command should be stored within the command block.
    :type track_output: bool
    """

    PACKET_ID: ClassVar[int] = 0x31
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    command: str
    track_output: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_utf(self.command)
        buf.write_value(StructFormat.BOOL, self.track_output)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        command = buf.read_utf()
        track_output = buf.read_value(StructFormat.BOOL)
        return cls(entity_id=entity_id, command=command, track_output=track_output)


@final
@define
class SetCreativeModeSlot(ServerBoundPacket):
    """Sent when the player changes the slot selection in Creative mode. (Client -> Server).

    Initialize the SetCreativeModeSlot packet.

    :param slot: The inventory slot.
    :type slot: int
    :param clicked_item: The clicked item.
    :type clicked_item: Slot
    """

    PACKET_ID: ClassVar[int] = 0x32
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    slot: int
    clicked_item: Slot

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.SHORT, self.slot)
        self.clicked_item.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        slot = buf.read_value(StructFormat.SHORT)
        clicked_item = Slot.deserialize(buf)
        return cls(slot=slot, clicked_item=clicked_item)


class StructureBlockEvent(IntEnum):
    """The action to perform on a structure block."""

    UPDATE_DATA = 0
    SAVE = 1
    LOAD = 2
    DETECT_SIZE = 3


class StructureBlockMode(IntEnum):
    """The mode of a structure block."""

    SAVE = 0
    LOAD = 1
    CORNER = 2
    DATA = 3


class StructureBlockMirror(IntEnum):
    """The mirror mode of a structure block."""

    NONE = 0
    LEFT_RIGHT = 1
    FRONT_BACK = 2


class StructureBlockRotation(IntEnum):
    """The rotation mode of a structure block."""

    NONE = 0
    CLOCKWISE_90 = 1
    CLOCKWISE_180 = 2
    COUNTERCLOCKWISE_90 = 3


@final
@define
class SetJigsawBlock(ServerBoundPacket):
    """Sent when Done is pressed on the Jigsaw Block interface. (Client -> Server).

    Initialize the SetJigsawBlock packet.

    :param location: The block entity location.
    :type location: Position
    :param name: The name of the jigsaw block.
    :type name: :class:`~mcproto.types.Identifier`
    :param target: The target of the jigsaw block.
    :type target: :class:`~mcproto.types.Identifier`
    :param pool: The pool of the jigsaw block.
    :type pool: :class:`~mcproto.types.Identifier`
    :param final_state: The final state of the jigsaw block.
    :type final_state: str
    :param joint_type: The joint type of the jigsaw block.
    :type joint_type: str
    :param selection_priority: The selection priority of the jigsaw block.
    :type selection_priority: int
    :param placement_priority: The placement priority of the jigsaw block.
    :type placement_priority: int
    """

    PACKET_ID: ClassVar[int] = 0x33
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    location: Position
    name: str
    target: str
    pool: str
    final_state: str
    joint_type: str
    selection_priority: int
    placement_priority: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.location.serialize_to(buf)
        buf.write_utf(self.name)
        buf.write_utf(self.target)
        buf.write_utf(self.pool)
        buf.write_utf(self.final_state)
        buf.write_utf(self.joint_type)
        buf.write_varint(self.selection_priority)
        buf.write_varint(self.placement_priority)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        location = Position.deserialize(buf)
        name = buf.read_utf()
        target = buf.read_utf()
        pool = buf.read_utf()
        final_state = buf.read_utf()
        joint_type = buf.read_utf()
        selection_priority = buf.read_varint()
        placement_priority = buf.read_varint()
        return cls(
            location=location,
            name=name,
            target=target,
            pool=pool,
            final_state=final_state,
            joint_type=joint_type,
            selection_priority=selection_priority,
            placement_priority=placement_priority,
        )


@final
@define
class SetStructureBlock(ServerBoundPacket):
    """Sent when a structure block is programmed. (Client -> Server).

    Initialize the SetStructureBlock packet.

    :param location: The block entity location.
    :type location: Position
    :param action: The action to perform on the structure block.
    :type action: StructureBlockEvent
    :param mode: The mode of the structure block.
    :type mode: StructureBlockMode
    :param name: The name of the structure block.
    :type name: str
    :param offset_x: The X offset of the structure block.
    :type offset_x: int
    :param offset_y: The Y offset of the structure block.
    :type offset_y: int
    :param offset_z: The Z offset of the structure block.
    :type offset_z: int
    :param size_x: The X size of the structure block.
    :type size_x: int
    :param size_y: The Y size of the structure block.
    :type size_y: int
    :param size_z: The Z size of the structure block.
    :type size_z: int
    :param mirror: The mirror mode of the structure block.
    :type mirror: StructureBlockMirror
    :param rotation: The rotation mode of the structure block.
    :type rotation: StructureBlockRotation
    :param metadata: The metadata of the structure block.
    :type metadata: str
    :param integrity: The integrity of the structure block.
    :type integrity: float
    :param seed: The seed of the structure block.
    :type seed: int
    :param ignore_entities: Whether to ignore entities in the structure block.
    :type ignore_entities: bool
    :param show_air: Whether to show air in the structure block.
    :type show_air: bool
    :param show_bounding_box: Whether to show the bounding box of the structure block.
    :type show_bounding_box: bool

    """

    PACKET_ID: ClassVar[int] = 0x34
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    location: Position = field()
    action: StructureBlockEvent = field()
    mode: StructureBlockMode = field()
    name: str = field()
    offset_x: int = field(validator=[validators.ge(-48), validators.le(48)])
    offset_y: int = field(validator=[validators.ge(-48), validators.le(48)])
    offset_z: int = field(validator=[validators.ge(-48), validators.le(48)])
    size_x: int = field(validator=[validators.ge(0), validators.le(48)])
    size_y: int = field(validator=[validators.ge(0), validators.le(48)])
    size_z: int = field(validator=[validators.ge(0), validators.le(48)])
    mirror: StructureBlockMirror = field()
    rotation: StructureBlockRotation = field()
    metadata: str = field()
    integrity: float = field(validator=[validators.ge(0.0), validators.le(1.0)])
    seed: int = field()
    ignore_entities: bool = field()
    show_air: bool = field()
    show_bounding_box: bool = field()

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.location.serialize_to(buf)
        buf.write_varint(self.action.value)
        buf.write_varint(self.mode.value)
        buf.write_utf(self.name)
        buf.write_value(StructFormat.BYTE, self.offset_x)
        buf.write_value(StructFormat.BYTE, self.offset_y)
        buf.write_value(StructFormat.BYTE, self.offset_z)
        buf.write_value(StructFormat.BYTE, self.size_x)
        buf.write_value(StructFormat.BYTE, self.size_y)
        buf.write_value(StructFormat.BYTE, self.size_z)
        buf.write_varint(self.mirror.value)
        buf.write_varint(self.rotation.value)
        buf.write_utf(self.metadata)
        buf.write_value(StructFormat.FLOAT, self.integrity)
        buf.write_varlong(self.seed)
        flags = 0
        flags |= 0x01 * self.ignore_entities
        flags |= 0x02 * self.show_air
        flags |= 0x04 * self.show_bounding_box
        buf.write_value(StructFormat.BYTE, flags)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        location = Position.deserialize(buf)
        action = StructureBlockEvent(buf.read_varint())
        mode = StructureBlockMode(buf.read_varint())
        name = buf.read_utf()
        offset_x = buf.read_value(StructFormat.BYTE)
        offset_y = buf.read_value(StructFormat.BYTE)
        offset_z = buf.read_value(StructFormat.BYTE)
        size_x = buf.read_value(StructFormat.BYTE)
        size_y = buf.read_value(StructFormat.BYTE)
        size_z = buf.read_value(StructFormat.BYTE)
        mirror = StructureBlockMirror(buf.read_varint())
        rotation = StructureBlockRotation(buf.read_varint())
        metadata = buf.read_utf()
        integrity = buf.read_value(StructFormat.FLOAT)
        seed = buf.read_varlong()
        flags = buf.read_value(StructFormat.BYTE)
        ignore_entities = bool(flags & 0x01)
        show_air = bool(flags & 0x02)
        show_bounding_box = bool(flags & 0x04)

        return cls(
            location=location,
            action=action,
            mode=mode,
            name=name,
            offset_x=offset_x,
            offset_y=offset_y,
            offset_z=offset_z,
            size_x=size_x,
            size_y=size_y,
            size_z=size_z,
            mirror=mirror,
            rotation=rotation,
            metadata=metadata,
            integrity=integrity,
            seed=seed,
            ignore_entities=ignore_entities,
            show_air=show_air,
            show_bounding_box=show_bounding_box,
        )


validators.max_len(384)


@final
@define
class SignUpdate(ServerBoundPacket):
    """Sent when the player updates a sign. (Client -> Server).

    Initialize the SignUpdate packet.

    :param location: The block coordinates of the sign.
    :type location: Position
    :param is_front_text: Whether the updated text is in front or on the back of the sign.
    :type is_front_text: bool
    :param line_1: The first line of text in the sign.
    :type line_1: str
    :param line_2: The second line of text in the sign.
    :type line_2: str
    :param line_3: The third line of text in the sign.
    :type line_3: str
    :param line_4: The fourth line of text in the sign.
    :type line_4: str
    """

    PACKET_ID: ClassVar[int] = 0x35
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    location: Position = field()
    is_front_text: bool = field()
    line_1: str = field(validator=validators.max_len(384))
    line_2: str = field(validator=validators.max_len(384))
    line_3: str = field(validator=validators.max_len(384))
    line_4: str = field(validator=validators.max_len(384))

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.location.serialize_to(buf)
        buf.write_value(StructFormat.BOOL, self.is_front_text)
        buf.write_utf(self.line_1)
        buf.write_utf(self.line_2)
        buf.write_utf(self.line_3)
        buf.write_utf(self.line_4)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        location = Position.deserialize(buf)
        is_front_text = buf.read_value(StructFormat.BOOL)
        line_1 = buf.read_utf()
        line_2 = buf.read_utf()
        line_3 = buf.read_utf()
        line_4 = buf.read_utf()
        return cls(
            location=location,
            is_front_text=is_front_text,
            line_1=line_1,
            line_2=line_2,
            line_3=line_3,
            line_4=line_4,
        )


@final
@define
class Swing(ServerBoundPacket):
    """Sent when the player's arm swings. (Client -> Server).

    Initialize the Swing packet.

    :param hand: The hand used for the animation.
    :type hand: Hand
    """

    PACKET_ID: ClassVar[int] = 0x36
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    hand: Hand

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.hand.value)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        hand = Hand(buf.read_varint())
        return cls(hand=hand)


@final
@define
class TeleportToEntity(ServerBoundPacket):
    """Teleports the player to the given entity. (Client -> Server).

    The player must be in spectator mode. The entity does not need to be in the same dimension as the player; if
    necessary, the player will be respawned in the right world. If the given entity cannot be found (or isn't loaded),
    this packet will be ignored. It will also be ignored if the player attempts to teleport to themselves.

    Initialize the TeleportToEntity packet.

    :param target_player: The UUID of the player to teleport to (can also be an entity UUID).
    :type target_player: UUID
    """

    PACKET_ID: ClassVar[int] = 0x37
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    target_player: UUID

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.target_player.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        target_player = UUID.deserialize(buf)
        return cls(target_player=target_player)


@final
@define
class UseItemOn(ServerBoundPacket):
    """Sent when the player uses an item on a block or entity. (Client -> Server).

    Initialize the UseItemOn packet.

    :param hand: The hand from which the item is used.
    :type hand: Hand
    :param location: The block position.
    :type location: Position
    :param face: The face on which the item is used.
    :type face: :class:`BlockFace`
    :param cursor_position_x: The position of the crosshair on the block, from 0 to 1 increasing from west to east.
    :type cursor_position_x: float
    :param cursor_position_y: The position of the crosshair on the block, from 0 to 1 increasing from bottom to top.
    :type cursor_position_y: float
    :param cursor_position_z: The position of the crosshair on the block, from 0 to 1 increasing from north to south.
    :type cursor_position_z: float
    :param inside_block: True when the player's head is inside of a block.
    :type inside_block: bool
    :param sequence: The block change sequence number.
    :type sequence: int
    """

    PACKET_ID: ClassVar[int] = 0x38
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    hand: Hand
    location: Position
    face: BlockFace
    cursor_position: Vec3
    inside_block: bool
    sequence: int

    def __attrs_post_init__(self):
        if not (
            0 <= self.cursor_position.x <= 1 and 0 <= self.cursor_position.y <= 1 and 0 <= self.cursor_position.z <= 1
        ):
            raise ValueError("cursor_position_x must be between 0 and 1")

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.hand.value)
        self.location.serialize_to(buf)
        buf.write_varint(self.face)
        self.cursor_position.serialize_to(buf)
        buf.write_value(StructFormat.BOOL, self.inside_block)
        buf.write_varint(self.sequence)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        hand = Hand(buf.read_varint())
        location = Position.deserialize(buf)
        face = BlockFace(buf.read_varint())
        cursor_position = Vec3.deserialize(buf)
        inside_block = buf.read_value(StructFormat.BOOL)
        sequence = buf.read_varint()
        return cls(
            hand=hand,
            location=location,
            face=face,
            cursor_position=cursor_position,
            inside_block=inside_block,
            sequence=sequence,
        )


@final
@define
class UseItem(ServerBoundPacket):
    """Sent when the player uses an item. (Client -> Server).

    Initialize the UseItem packet.

    :param hand: The hand used for the animation.
    :type hand: Hand
    :param sequence: The block change sequence number.
    :type sequence: int
    :param yaw: The player head rotation along the Y-Axis.
    :type yaw: float
    :param pitch: The player head rotation along the X-Axis.
    :type pitch: float
    """

    PACKET_ID: ClassVar[int] = 0x39
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    hand: Hand
    sequence: int
    yaw: float
    pitch: float

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.hand.value)
        buf.write_varint(self.sequence)
        buf.write_value(StructFormat.FLOAT, self.yaw)
        buf.write_value(StructFormat.FLOAT, self.pitch)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        hand = Hand(buf.read_varint())
        sequence = buf.read_varint()
        yaw = buf.read_value(StructFormat.FLOAT)
        pitch = buf.read_value(StructFormat.FLOAT)
        return cls(hand=hand, sequence=sequence, yaw=yaw, pitch=pitch)
