from __future__ import annotations

from typing import ClassVar
from typing import final
from typing_extensions import override, Self

from mcproto.packets import ServerBoundPacket, GameState
from mcproto.buffer import Buffer
from mcproto.protocol.base_io import StructFormat
from attrs import define

from mcproto.types import Position, FixedBitset


@final
@define
class ConfirmTeleportation(ServerBoundPacket):
    """Sent by client as confirmation of Synchronize Player Position. (Client -> Server).

    Initialize the ConfirmTeleportation packet.

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
class QueryBlockEntityTag(ServerBoundPacket):
    """Used when F3+I is pressed while looking at a block. (Client -> Server).

    Initialize the QueryBlockEntityTag packet.

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
    """Must have at least op level 2 to use. Appears to only be used on singleplayer; the difficulty buttons are still disabled in multiplayer. (Client -> Server).

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
class AcknowledgeMessage(ServerBoundPacket):
    """Acknowledges receipt of a message from the server. (Client -> Server).

    Initialize the AcknowledgeMessage packet.

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
class SignedChatCommand(ServerBoundPacket):
    """Used to send a signed chat command to the server. (Client -> Server).

    Initialize the SignedChatCommand packet.

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
class ChatMessage(ServerBoundPacket):
    """Used to send a chat message to the server. (Client -> Server).

    The server will broadcast a Player Chat Message packet with Chat Type minecraft:chat to all players that
    haven't disabled chat (including the player that sent the message).

    Initialize the ChatMessage packet.

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
    :type signature: Optional[bytes]
    :param message_count: The message count.
    :type message_count: int
    :param acknowledged: The acknowledged bitset.
    :type acknowledged: bytes
    """

    PACKET_ID: ClassVar[int] = 0x06
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    message: str
    timestamp: int
    salt: int
    signature: bytes | None
    message_count: int
    acknowledged: FixedBitset[20]

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
