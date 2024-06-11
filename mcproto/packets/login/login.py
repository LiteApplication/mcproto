from __future__ import annotations

from typing import ClassVar, cast, final

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, load_der_public_key
from typing_extensions import Self, override

from mcproto.buffer import Buffer
from mcproto.packets.packet import ClientBoundPacket, GameState, ServerBoundPacket
from mcproto.types.chat import JSONTextComponent
from mcproto.types.uuid import UUID
from attrs import define

__all__ = [
    "LoginDisconnect",
    "LoginEncryptionRequest",
    "LoginEncryptionResponse",
    "LoginPluginRequest",
    "LoginPluginResponse",
    "LoginSetCompression",
    "LoginStart",
    "LoginSuccess",
    "LoginAcknowledged",
]


@final
@define
class LoginStart(ServerBoundPacket):
    """Packet from client asking to start login process. (Client -> Server).

    Initialize the LoginStart packet.

    :param username: Username of the client who sent the request.
    :param uuid: UUID of the player logging in (if the player doesn't have a UUID, this can be ``None``)
    """

    PACKET_ID: ClassVar[int] = 0x00
    GAME_STATE: ClassVar[GameState] = GameState.LOGIN

    username: str
    uuid: UUID

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_utf(self.username)
        self.uuid.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        username = buf.read_utf()
        uuid = UUID.deserialize(buf)
        return cls(username=username, uuid=uuid)


@final
@define
class LoginEncryptionRequest(ClientBoundPacket):
    """Used by the server to ask the client to encrypt the login process. (Server -> Client).

    Initialize the LoginEncryptionRequest packet.

    :param public_key: Server's public key.
    :param verify_token: Sequence of random bytes generated by server for verification.
    :param server_id: Empty on minecraft versions 1.7.X and higher (20 random chars pre 1.7).
    """

    PACKET_ID: ClassVar[int] = 0x01
    GAME_STATE: ClassVar[GameState] = GameState.LOGIN

    public_key: RSAPublicKey
    verify_token: bytes
    server_id: str | None = None

    @override
    def __attrs_post_init__(self) -> None:
        if self.server_id is None:
            self.server_id = " " * 20

        super().__attrs_post_init__()

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.server_id = cast(str, self.server_id)

        public_key_raw = self.public_key.public_bytes(encoding=Encoding.DER, format=PublicFormat.SubjectPublicKeyInfo)
        buf.write_utf(self.server_id)
        buf.write_bytearray(public_key_raw)
        buf.write_bytearray(self.verify_token)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        server_id = buf.read_utf()
        public_key_raw = bytes(buf.read_bytearray())
        verify_token = bytes(buf.read_bytearray())

        # Key type is determined by the passed key itself, we know in our case, it will
        # be an RSA public key, so we explicitly type-cast here.
        public_key = cast(RSAPublicKey, load_der_public_key(public_key_raw, default_backend()))

        return cls(server_id=server_id, public_key=public_key, verify_token=verify_token)


@final
@define
class LoginEncryptionResponse(ServerBoundPacket):
    """Response from the client to :class:`LoginEncryptionRequest` packet. (Client -> Server).

    Initialize the LoginEncryptionResponse packet.

    :param shared_secret: Shared secret value, encrypted with server's public key.
    :param verify_token: Verify token value, encrypted with same public key.
    """

    PACKET_ID: ClassVar[int] = 0x01
    GAME_STATE: ClassVar[GameState] = GameState.LOGIN

    shared_secret: bytes
    verify_token: bytes

    @override
    def serialize_to(self, buf: Buffer) -> None:
        """Serialize the packet."""
        buf.write_bytearray(self.shared_secret)
        buf.write_bytearray(self.verify_token)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        shared_secret = bytes(buf.read_bytearray())
        verify_token = bytes(buf.read_bytearray())
        return cls(shared_secret=shared_secret, verify_token=verify_token)


@final
@define
class LoginSuccess(ClientBoundPacket):
    """Sent by the server to denote a successful login. (Server -> Client).

    Initialize the LoginSuccess packet.

    :param uuid: The UUID of the connecting player/client.
    :param username: The username of the connecting player/client.
    """

    PACKET_ID: ClassVar[int] = 0x02
    GAME_STATE: ClassVar[GameState] = GameState.LOGIN

    uuid: UUID
    username: str

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.uuid.serialize_to(buf)
        buf.write_utf(self.username)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        uuid = UUID.deserialize(buf)
        username = buf.read_utf()
        return cls(uuid, username)


@final
@define
class LoginDisconnect(ClientBoundPacket):
    """Sent by the server to kick a player while in the login state. (Server -> Client).

    Initialize the LoginDisconnect packet.

    :param reason: The reason for disconnection (kick).
    """

    PACKET_ID: ClassVar[int] = 0x00
    GAME_STATE: ClassVar[GameState] = GameState.LOGIN

    reason: JSONTextComponent

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.reason.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        reason = JSONTextComponent.deserialize(buf)
        return cls(reason)


@final
@define
class LoginPluginRequest(ClientBoundPacket):
    """Sent by the server to implement a custom handshaking flow. (Server -> Client).

    Initialize the LoginPluginRequest.

    :param message_id: Message id, generated by the server, should be unique to the connection.
    :param channel: Channel identifier, name of the plugin channel used to send data.
    :param data: Data that is to be sent.
    """

    PACKET_ID: ClassVar[int] = 0x04
    GAME_STATE: ClassVar[GameState] = GameState.LOGIN

    message_id: int
    channel: str
    data: bytes

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.message_id)
        buf.write_utf(self.channel)
        buf.write(self.data)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        message_id = buf.read_varint()
        channel = buf.read_utf()
        data = bytes(buf.read(buf.remaining))  # All of the remaining data in the buffer
        return cls(message_id, channel, data)


@final
@define
class LoginPluginResponse(ServerBoundPacket):
    """Response to LoginPluginRequest from client. (Client -> Server).

    Initialize the LoginPluginRequest packet.

    :param message_id: Message id, generated by the server, should be unique to the connection.
    :param data: Optional response data, present if client understood request.
    """

    PACKET_ID: ClassVar[int] = 0x02
    GAME_STATE: ClassVar[GameState] = GameState.LOGIN

    message_id: int
    data: bytes | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.message_id)
        buf.write_optional(self.data, buf.write)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        message_id = buf.read_varint()
        data = buf.read_optional(lambda: bytes(buf.read(buf.remaining)))
        return cls(message_id, data)


@final
@define
class LoginAcknowledged(ServerBoundPacket):
    """Acknowledgement to the Login Success packet sent by the server. (Client -> Server).

    Initialize the LoginAcknowledged packet.
    """

    PACKET_ID: ClassVar[int] = 0x3
    GAME_STATE: ClassVar[GameState] = GameState.LOGIN

    @override
    def serialize_to(self, buf: Buffer) -> None:
        pass

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        return cls()


@final
@define
class LoginSetCompression(ClientBoundPacket):
    """Sent by the server to specify whether to use compression on future packets or not (Server -> Client).

    Initialize the LoginSetCompression packet.


    :param threshold:
        Maximum size of a packet before it is compressed. All packets smaller than this will remain uncompressed.
        To disable compression completely, threshold can be set to -1.

    .. note:: This packet is optional, and if not set, the compression will not be enabled at all.
    """

    PACKET_ID: ClassVar[int] = 0x03
    GAME_STATE: ClassVar[GameState] = GameState.LOGIN

    threshold: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.threshold)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        threshold = buf.read_varint()
        return cls(threshold)
