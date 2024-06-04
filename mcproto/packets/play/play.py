from __future__ import annotations

from enum import IntEnum
from typing import ClassVar, cast
from typing import final
import warnings
from typing_extensions import override, Self

from mcproto.packets import ClientBoundPacket, GameState
from mcproto.buffer import Buffer
from mcproto.protocol.base_io import StructFormat
from attrs import define


from mcproto.types import (
    Angle,
    UUID,
    Position,
    Vec3,
    NBTag,
    TextComponent,
    Slot,
    Identifier,
    ParticleData,
    CompoundNBT,
    Bitset,
    BlockEntity,
    MapIcon,
    Trade,
)
from mcproto.types.nbt import EndNBT


@final
@define
class BundleDelimiter(ClientBoundPacket):
    """The delimiter for a bundle of packets. (Client -> Server).

    When received, the client should store every subsequent packet it receives, and wait until another delimiter is
    received. Once that happens, the client is guaranteed to process every packet in the bundle on the same tick, and
    the client
    should stop storing packets.

    Initialize the BundleDelimiter packet.
    """

    PACKET_ID: ClassVar[int] = 0x00
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
class SpawnEntity(ClientBoundPacket):
    """Sent by the server when an entity (aside from Experience Orb) is created. (Client -> Server).

    Initialize the SpawnEntity packet.

    :param entity_id: A unique integer ID mostly used in the protocol to identify the entity.
    :type entity_id: int
    :param entity_uuid: A unique identifier that is mostly used in persistence.
    :type entity_uuid: UUID
    :param entity_type: ID in the minecraft:entity_type registry (see "type" field in Entity metadata#Entities).
    :type entity_type: int
    :param x: The x coordinate of the entity.
    :type x: float
    :param y: The y coordinate of the entity.
    :type y: float
    :param z: The z coordinate of the entity.
    :type z: float
    :param pitch: The pitch of the entity. To get the real pitch, you must divide this by (256.0F / 360.0F).
    :type pitch: Angle
    :param yaw: The yaw of the entity. To get the real yaw, you must divide this by (256.0F / 360.0F).
    :type yaw: Angle
    :param head_yaw: Only used by living entities, where the head of the entity may differ from the general body
    rotation.
    :type head_yaw: Angle
    :param data: Meaning dependent on the value of the entity_type field, see Object Data for details.
    :type data: int
    :param velocity_x: Same units as Set Entity Velocity.
    :type velocity_x: int
    :param velocity_y: Same units as Set Entity Velocity.
    :type velocity_y: int
    :param velocity_z: Same units as Set Entity Velocity.
    :type velocity_z: int
    """

    PACKET_ID: ClassVar[int] = 0x01
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    entity_uuid: UUID
    entity_type: int
    x: float
    y: float
    z: float
    pitch: Angle
    yaw: Angle
    head_yaw: Angle
    data: int
    velocity_x: int
    velocity_y: int
    velocity_z: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        self.entity_uuid.serialize_to(buf)
        buf.write_varint(self.entity_type)
        buf.write_value(StructFormat.DOUBLE, self.x)
        buf.write_value(StructFormat.DOUBLE, self.y)
        buf.write_value(StructFormat.DOUBLE, self.z)
        self.pitch.serialize_to(buf)
        self.yaw.serialize_to(buf)
        self.head_yaw.serialize_to(buf)
        buf.write_varint(self.data)
        buf.write_value(StructFormat.SHORT, self.velocity_x)
        buf.write_value(StructFormat.SHORT, self.velocity_y)
        buf.write_value(StructFormat.SHORT, self.velocity_z)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        entity_uuid = UUID.deserialize(buf)
        entity_type = buf.read_varint()
        x = buf.read_value(StructFormat.DOUBLE)
        y = buf.read_value(StructFormat.DOUBLE)
        z = buf.read_value(StructFormat.DOUBLE)
        pitch = Angle.deserialize(buf)
        yaw = Angle.deserialize(buf)
        head_yaw = Angle.deserialize(buf)
        data = buf.read_varint()
        velocity_x = buf.read_value(StructFormat.SHORT)
        velocity_y = buf.read_value(StructFormat.SHORT)
        velocity_z = buf.read_value(StructFormat.SHORT)
        return cls(
            entity_id=entity_id,
            entity_uuid=entity_uuid,
            entity_type=entity_type,
            x=x,
            y=y,
            z=z,
            pitch=pitch,
            yaw=yaw,
            head_yaw=head_yaw,
            data=data,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
            velocity_z=velocity_z,
        )


@final
@define
class SpawnExperienceOrb(ClientBoundPacket):
    """Spawns one or more experience orbs. (Client -> Server).

    Initialize the SpawnExperienceOrb packet.

    :param entity_id: A unique integer ID mostly used in the protocol to identify the entity.
    :type entity_id: int
    :param x: The x coordinate of the entity.
    :type x: float
    :param y: The y coordinate of the entity.
    :type y: float
    :param z: The z coordinate of the entity.
    :type z: float
    :param count: The amount of experience this orb will reward once collected.
    :type count: int
    """

    PACKET_ID: ClassVar[int] = 0x02
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    x: float
    y: float
    z: float
    count: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_value(StructFormat.DOUBLE, self.x)
        buf.write_value(StructFormat.DOUBLE, self.y)
        buf.write_value(StructFormat.DOUBLE, self.z)
        buf.write_value(StructFormat.SHORT, self.count)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        x = buf.read_value(StructFormat.DOUBLE)
        y = buf.read_value(StructFormat.DOUBLE)
        z = buf.read_value(StructFormat.DOUBLE)
        count = buf.read_value(StructFormat.SHORT)
        return cls(entity_id=entity_id, x=x, y=y, z=z, count=count)


class Animation(IntEnum):
    """An animation for the EntityAnimation Packet."""

    SWING_MAIN_HAND = 0
    LEAVE_BED = 1
    SWING_OFFHAND = 2
    CRITICAL_EFFECT = 3
    MAGIC_CRITICAL_EFFECT = 4


@final
@define
class EntityAnimation(ClientBoundPacket):
    """Sent whenever an entity should change animation. (Client -> Server).

    Initialize the EntityAnimation packet.

    :param entity_id: Player ID.
    :type entity_id: int
    :param animation: Animation ID (see below).
    :type animation: Animation
    """

    PACKET_ID: ClassVar[int] = 0x03
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    animation: Animation

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_value(StructFormat.UBYTE, self.animation.value)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        animation = Animation(buf.read_value(StructFormat.UBYTE))
        return cls(
            entity_id=entity_id,
            animation=animation,
        )


@final
@define
class AwardStatistics(ClientBoundPacket):
    """Informs the client of its current statistics. (Client -> Server).

    Sent as a response to Client Command (id 1). Will only send the changed values if previously requested.
    .. seealso:: https://wiki.vg/Protocol#Entity_Animation

    Initialize the AwardStatistics packet.

    :param statistics: A list of tuples containing the category ID, statistic ID, and value.
    :type statistics: list[tuple[int, int, int]]
    """

    PACKET_ID: ClassVar[int] = 0x04
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    statistics: list[tuple[int, int, int]]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(len(self.statistics))
        for category_id, statistic_id, value in self.statistics:
            buf.write_varint(category_id)
            buf.write_varint(statistic_id)
            buf.write_varint(value)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        count = buf.read_varint()
        statistics: list[tuple[int, int, int]] = []
        for _ in range(count):
            category_id = buf.read_varint()
            statistic_id = buf.read_varint()
            value = buf.read_varint()
            statistics.append((category_id, statistic_id, value))
        return cls(statistics=statistics)


@final
@define
class AcknowledgeBlockChange(ClientBoundPacket):
    """Acknowledges a user-initiated block change. (Client -> Server).

    Initialize the AcknowledgeBlockChange packet.

    :param sequence_id: Represents the sequence to acknowledge.
    :type sequence_id: int
    """

    PACKET_ID: ClassVar[int] = 0x05
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    sequence_id: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.sequence_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        sequence_id = buf.read_varint()
        return cls(sequence_id=sequence_id)


@final
@define
class SetBlockDestroyStage(ClientBoundPacket):
    """Sets the block destroy stage at the given location. (Client -> Server).

    Initialize the SetBlockDestroyStage packet.

    :param entity_id: The ID of the entity breaking the block.
    :type entity_id: int
    :param location: Block Position.
    :type location: Position
    :param destroy_stage: 0-9 to set it, any other value to remove it.
    :type destroy_stage: int
    """

    PACKET_ID: ClassVar[int] = 0x06
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    location: Position
    destroy_stage: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        self.location.serialize_to(buf)
        buf.write_value(StructFormat.BYTE, self.destroy_stage)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        location = Position.deserialize(buf)
        destroy_stage = buf.read_value(StructFormat.BYTE)
        return cls(entity_id=entity_id, location=location, destroy_stage=destroy_stage)


@final
@define
class BlockEntityData(ClientBoundPacket):
    """Sets the block entity associated with the block at the given location. (Server -> Client).

    Initialize the BlockEntityData packet.

    :param location: Block Position.
    :type location: :class:`~mcproto.types.Position`
    :param action: The action to perform.
    :type action: int
    :param nbt: The NBT data of the block entity.
    :type nbt: :class:`~mcproto.types.NBTag`
    """

    PACKET_ID: ClassVar[int] = 0x07
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    location: Position
    action: int
    nbt: NBTag | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.location.serialize_to(buf)
        buf.write_varint(self.action)
        if self.nbt is None:
            EndNBT().serialize_to(buf)
        else:
            self.nbt.serialize_to(buf, with_name=False)  # TODO: Check this in WireShark

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        location = Position.deserialize(buf)
        action = buf.read_varint()
        nbt = NBTag.deserialize(buf, with_name=False)
        if isinstance(nbt, EndNBT):
            nbt = None
        return cls(location=location, action=action, nbt=nbt)


class BlockActionID(IntEnum):
    """Represents the different block action IDs."""

    NONE = 0

    EXTEND_PISTON = 0
    RETRACT_PISTON = 1
    CANCEL_PISTON = 2

    RESET_SPAWN_DELAY = 1

    END_GATEWAY_BEACON_BEAM = 1

    # Chest and shulker box
    CONTAINER_UPDATE_PLAYER_LOOKING = 1


class BlockActionParameter(IntEnum):
    """Represents the different block action parameters."""

    NONE = 0

    PISTON_DIRECTION_DOWN = 0
    PISTON_DIRECTION_UP = 1
    PISTON_DIRECTION_SOUTH = 2
    PISTON_DIRECTION_WEST = 3
    PISTON_DIRECTION_NORTH = 4
    PISTON_DIRECTION_EAST = 5


@final
@define
class BlockAction(ClientBoundPacket):
    """Used for a number of actions and animations performed by blocks, usually non-persistent. (Server -> Client).

    Initialize the BlockAction packet.

    :param location: Block coordinates.
    :type location: Position
    :param action_id: Varies depending on block — see Block Actions.
    :type action_id: BlockActionID
    :param action_parameter: Varies depending on block — see Block Actions.
    :type action_parameter: BlockActionParameter | int
    :param block_type: The block type ID for the block. This is not used by the Notchian client, as it will infer the
        type of block based on the given position.
    :type block_type: int

    .. note:: The `action_id` and `action_parameter` fields will be casted to integers.
    """

    PACKET_ID: ClassVar[int] = 0x08
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    location: Position
    action_id: BlockActionID | int
    action_parameter: BlockActionParameter | int
    block_type: int

    @override
    def __attrs_post_init__(self) -> None:
        if isinstance(self.action_id, BlockActionID):
            self.action_id = self.action_id.value
        if isinstance(self.action_parameter, BlockActionParameter):
            self.action_parameter = self.action_parameter.value

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.location.serialize_to(buf)
        self.action_id = cast(int, self.action_id)
        self.action_parameter = cast(int, self.action_parameter)

        buf.write_value(StructFormat.UBYTE, self.action_id)
        buf.write_value(StructFormat.UBYTE, self.action_parameter)
        buf.write_varint(self.block_type)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        location = Position.deserialize(buf)
        action_id = buf.read_value(StructFormat.UBYTE)
        action_parameter = buf.read_value(StructFormat.UBYTE)
        block_type = buf.read_varint()
        return cls(location=location, action_id=action_id, action_parameter=action_parameter, block_type=block_type)


@final
@define
class BlockUpdate(ClientBoundPacket):
    """Fired whenever a block is changed within the render distance. (Server -> Client).

    Initialize the BlockUpdate packet.

    :param location: Block coordinates.
    :type location: Position
    :param block_id: The new block state ID for the block as given in the block state registry.
    :type block_id: int
    """

    PACKET_ID: ClassVar[int] = 0x09
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    location: Position
    block_id: int  # Registry minecraft:block_state

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.location.serialize_to(buf)
        buf.write_varint(self.block_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        location = Position.deserialize(buf)
        block_id = buf.read_varint()
        return cls(location=location, block_id=block_id)


class BossBarColor(IntEnum):
    """Represents the different boss bar colors."""

    PINK = 0
    BLUE = 1
    RED = 2
    GREEN = 3
    YELLOW = 4
    PURPLE = 5
    WHITE = 6


class BossBarDivisionType(IntEnum):
    """Represents the different boss bar division types."""

    NONE = 0
    SIX_NOTCHES = 1
    TEN_NOTCHES = 2
    TWELVE_NOTCHES = 3
    TWENTY_NOTCHES = 4


class BossBarAction(IntEnum):
    """Represents the different boss bar actions."""

    ADD = 0
    REMOVE = 1
    UPDATE_HEALTH = 2
    UPDATE_TITLE = 3
    UPDATE_STYLE = 4
    UPDATE_FLAGS = 5


@final
@define
class BossBar(ClientBoundPacket):
    """Sent by the server to update a boss bar. (Server -> Client).

    Initialize the BossBar packet.

    :param uuid: Unique ID for this bar.
    :type uuid: UUID
    :param action: Determines the layout of the remaining packet.
    :type action: BossBarAction
    :param title: The title of the boss bar. Only present if the action is ADD or UPDATE_TITLE.
    :type title: TextComponent, optional
    :param health: From 0 to 1. Values greater than 1 do not crash a Notchian client, and start rendering part of a
    second health bar at around 1.5. Only present if the action is ADD or UPDATE_HEALTH.
    :type health: float, optional
    :param color: Color ID (see below). Only present if the action is ADD, UPDATE_HEALTH, or UPDATE_STYLE.
    :type color: BossBarColor, optional
    :param division: Type of division (see below). Only present if the action is ADD, UPDATE_HEALTH, or UPDATE_STYLE.
    :type division: BossBarDivisionType, optional
    :param flags: Bit mask. 0x1: should darken sky, 0x2: is dragon bar (used to play end music), 0x04: create fog
    (previously was also controlled by 0x02). Only present if the action is ADD, UPDATE_FLAGS, or UPDATE_STYLE.
    :type flags: int, optional
    """

    PACKET_ID: ClassVar[int] = 0x0A
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    uuid: UUID
    action: BossBarAction
    title: TextComponent | None = None
    health: float | None = None
    color: BossBarColor | None = None
    division: BossBarDivisionType | None = None
    darken_sky: bool | None = None
    is_dragon_bar: bool | None = None
    create_fog: bool | None = None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.uuid.serialize_to(buf)
        buf.write_varint(self.action.value)
        if self.action == BossBarAction.ADD:
            self.title = cast(TextComponent, self.title)
            self.health = cast(float, self.health)
            self.color = cast(BossBarColor, self.color)
            self.division = cast(BossBarDivisionType, self.division)

            flags = 0
            flags += 0x1 if self.darken_sky else 0
            flags += 0x2 if self.is_dragon_bar else 0
            flags += 0x4 if self.create_fog else 0

            self.title.serialize_to(buf)
            buf.write_value(StructFormat.FLOAT, self.health)
            buf.write_varint(self.color.value)
            buf.write_varint(self.division.value)
            buf.write_value(StructFormat.UBYTE, flags)
        elif self.action == BossBarAction.UPDATE_HEALTH:
            self.health = cast(float, self.health)
            buf.write_value(StructFormat.FLOAT, self.health)
        elif self.action == BossBarAction.UPDATE_TITLE:
            self.title = cast(TextComponent, self.title)

            self.title.serialize_to(buf)
        elif self.action == BossBarAction.UPDATE_STYLE:
            self.color = cast(BossBarColor, self.color)
            self.division = cast(BossBarDivisionType, self.division)

            buf.write_varint(self.color.value)
            buf.write_varint(self.division.value)
        elif self.action == BossBarAction.UPDATE_FLAGS:
            flags = 0
            flags += 0x1 if self.darken_sky else 0
            flags += 0x2 if self.is_dragon_bar else 0
            flags += 0x4 if self.create_fog else 0

            buf.write_value(StructFormat.UBYTE, flags)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        uuid = UUID.deserialize(buf)
        action = BossBarAction(buf.read_varint())
        title = None
        health = None
        color = None
        division = None
        darken_sky = None
        is_dragon_bar = None
        create_fog = None
        if action == BossBarAction.ADD:
            title = TextComponent.deserialize(buf)
            health = buf.read_value(StructFormat.FLOAT)
            color = BossBarColor(buf.read_varint())
            division = BossBarDivisionType(buf.read_varint())
            flags = buf.read_value(StructFormat.UBYTE)

            darken_sky = bool(flags & 0x1)
            is_dragon_bar = bool(flags & 0x2)
            create_fog = bool(flags & 0x4)

        elif action == BossBarAction.UPDATE_HEALTH:
            health = buf.read_value(StructFormat.FLOAT)
        elif action == BossBarAction.UPDATE_TITLE:
            title = TextComponent.deserialize(buf)
        elif action == BossBarAction.UPDATE_STYLE:
            color = BossBarColor(buf.read_varint())
            division = BossBarDivisionType(buf.read_varint())
        elif action == BossBarAction.UPDATE_FLAGS:
            flags = buf.read_value(StructFormat.UBYTE)

            darken_sky = bool(flags & 0x1)
            is_dragon_bar = bool(flags & 0x2)
            create_fog = bool(flags & 0x4)

        return cls(
            uuid=uuid,
            action=action,
            title=title,
            health=health,
            color=color,
            division=division,
            darken_sky=darken_sky,
            is_dragon_bar=is_dragon_bar,
            create_fog=create_fog,
        )

    @override
    def validate(self) -> None:
        if self.action == BossBarAction.ADD:
            if self.title is None:
                raise ValueError("BossBarAction.ADD requires a title")
            if self.health is None:
                raise ValueError("BossBarAction.ADD requires health")
            if self.color is None:
                raise ValueError("BossBarAction.ADD requires color")
            if self.division is None:
                raise ValueError("BossBarAction.ADD requires division")
            if self.darken_sky is None:
                raise ValueError("BossBarAction.ADD requires darken_sky")
            if self.is_dragon_bar is None:
                raise ValueError("BossBarAction.ADD requires is_dragon_bar")
            if self.create_fog is None:
                raise ValueError("BossBarAction.ADD requires create_fog")

        elif self.action == BossBarAction.UPDATE_HEALTH:
            if self.health is None:
                raise ValueError("BossBarAction.UPDATE_HEALTH requires health")
        elif self.action == BossBarAction.UPDATE_TITLE:
            if self.title is None:
                raise ValueError("BossBarAction.UPDATE_TITLE requires a title")
        elif self.action == BossBarAction.UPDATE_STYLE:
            if self.color is None:
                raise ValueError("BossBarAction.UPDATE_STYLE requires color")
            if self.division is None:
                raise ValueError("BossBarAction.UPDATE_STYLE requires division")
        elif self.action == BossBarAction.UPDATE_FLAGS:
            if self.darken_sky is None:
                raise ValueError("BossBarAction.UPDATE_FLAGS requires darken_sky")
            if self.is_dragon_bar is None:
                raise ValueError("BossBarAction.UPDATE_FLAGS requires is_dragon_bar")
            if self.create_fog is None:
                raise ValueError("BossBarAction.UPDATE_FLAGS requires create_fog")


@final
@define
class ChangeDifficulty(ClientBoundPacket):
    """Changes the difficulty setting in the client's option menu. (Server -> Client).

    Initialize the ChangeDifficulty packet.

    :param difficulty: 0: peaceful, 1: easy, 2: normal, 3: hard.
    :type difficulty: int
    :param locked: Whether the difficulty is locked.
    :type locked: bool
    """

    PACKET_ID: ClassVar[int] = 0x0B
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    difficulty: int
    locked: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.BYTE, self.difficulty)
        buf.write_value(StructFormat.BYTE, int(self.locked))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        difficulty = buf.read_value(StructFormat.BYTE)
        locked = bool(buf.read_value(StructFormat.BYTE))
        return cls(difficulty=difficulty, locked=locked)

    @override
    def validate(self) -> None:
        if self.difficulty not in {0, 1, 2, 3}:
            raise ValueError("Difficulty must be 0, 1, 2, or 3")


@final
@define
class ChunkBatchFinished(ClientBoundPacket):
    """Marks the end of a chunk batch. (Server -> Client).

    Initialize the ChunkBatchFinished packet.

    :param batch_size: Number of chunks.
    :type batch_size: int
    """

    PACKET_ID: ClassVar[int] = 0x0C
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    batch_size: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.batch_size)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        batch_size = buf.read_varint()
        return cls(batch_size=batch_size)


@final
@define
class ChunkBatchStart(ClientBoundPacket):
    """Marks the start of a chunk batch. (Server -> Client).

    Initialize the ChunkBatchStart packet.
    """

    PACKET_ID: ClassVar[int] = 0x0D
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
class ChunkBiomes(ClientBoundPacket):
    """Sent by the server to update the biomes of a chunk. (Server -> Client).

    Initialize the ChunkBiomes packet.

    :param chunk_biome_data: A list of tuples containing the chunk Z coordinate, chunk X coordinate, size, and data
    for each chunk.
    :type chunk_biome_data: list[tuple[int, int, int, bytes]]
    """

    PACKET_ID: ClassVar[int] = 0x0E
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    chunk_biome_data: list[tuple[int, int, int, bytes]]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(len(self.chunk_biome_data))
        for chunk_z, chunk_x, size, data in self.chunk_biome_data:
            buf.write_value(StructFormat.INT, chunk_z)
            buf.write_value(StructFormat.INT, chunk_x)
            buf.write_varint(size)
            buf.write(data)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        num_chunks = buf.read_varint()
        chunk_biome_data: list[tuple[int, int, int, bytes]] = []
        for _ in range(num_chunks):
            chunk_z = buf.read_value(StructFormat.INT)
            chunk_x = buf.read_value(StructFormat.INT)
            size = buf.read_varint()
            data = bytes(buf.read(size))
            chunk_biome_data.append((chunk_z, chunk_x, size, data))
        return cls(chunk_biome_data=chunk_biome_data)


@final
@define
class ClearTitles(ClientBoundPacket):
    """Clear the client's current title information, with the option to also reset it. (Server -> Client).

    Initialize the ClearTitles packet.

    :param reset: Whether to reset the title information.
    :type reset: bool
    """

    PACKET_ID: ClassVar[int] = 0x0F
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    reset: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.BYTE, int(self.reset))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        reset = bool(buf.read_value(StructFormat.BYTE))
        return cls(reset=reset)


@final
@define
class CommandSuggestionsResponse(ClientBoundPacket):
    """The server responds with a list of auto-completions of the last word sent to it. (Server -> Client).

    Initialize the CommandSuggestionsResponse packet.

    :param id: Transaction ID.
    :type id: int
    :param start: Start of the text to replace.
    :type start: int
    :param length: Length of the text to replace.
    :type length: int
    :param matches: A list of eligible values to insert.
    :type matches: list[tuple[str, bool, TextComponent | None]]
    """

    PACKET_ID: ClassVar[int] = 0x10
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    transaction_id: int
    start: int
    length: int
    matches: list[tuple[str, bool, TextComponent | None]]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.transaction_id)
        buf.write_varint(self.start)
        buf.write_varint(self.length)
        buf.write_varint(len(self.matches))
        for match, has_tooltip, tooltip in self.matches:
            buf.write_utf(match)
            buf.write_value(StructFormat.BYTE, int(has_tooltip))
            if has_tooltip:
                tooltip = cast(TextComponent, tooltip)
                tooltip.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        transaction_id = buf.read_varint()
        start = buf.read_varint()
        length = buf.read_varint()
        count = buf.read_varint()
        matches: list[tuple[str, bool, TextComponent | None]] = []
        for _ in range(count):
            match = buf.read_utf()
            has_tooltip = bool(buf.read_value(StructFormat.BYTE))
            tooltip = TextComponent.deserialize(buf) if has_tooltip else None
            matches.append((match, has_tooltip, tooltip))
        return cls(transaction_id=transaction_id, start=start, length=length, matches=matches)


@define
class Commands(ClientBoundPacket):
    """Lists all of the commands on the server, and how they are parsed. (Server -> Client).

    Initialize the Commands packet.

    :param data: The raw data of the packet.
    :type data: bytes

    .. warning:: This packet is not implemented, the raw data is stored in the `data` attribute.
    """

    PACKET_ID: ClassVar[int] = 0x11
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    data: bytes

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write(self.data)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        data = bytes(buf.read(buf.remaining))
        warnings.warn("Commands packet is not implemented", RuntimeWarning, stacklevel=1)
        return cls(data=data)


@final
@define
class CloseContainer(ClientBoundPacket):
    """Indicates that a window is forcibly closed. (Server -> Client).

    The Notchian client will close any open container regardless of the window ID.

    Initialize the CloseContainer packet.

    :param window_id: This is the ID of the window that was closed. 0 for inventory.
    :type window_id: int
    """

    PACKET_ID: ClassVar[int] = 0x12
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    window_id: int  # Registry minecraft:menu

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
class SetContainerContent(ClientBoundPacket):
    """Replaces the contents of a container window. (Server -> Client).

    Initialize the SetContainerContent packet.

    :param window_id: The ID of window which items are being sent for. 0 for player inventory.
    :type window_id: int
    :param state_id: A server-managed sequence number used to avoid desynchronization.
    :type state_id: int
    :param slot_data: A list of Slot objects representing the items in the container.
    :type slot_data: list[Slot]
    :param carried_item: The item being dragged with the mouse.
    :type carried_item: Slot
    """

    PACKET_ID: ClassVar[int] = 0x13
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    window_id: int  # Registry minecraft:menu
    state_id: int
    slot_data: list[Slot]
    carried_item: Slot

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.BYTE, self.window_id)
        buf.write_varint(self.state_id)
        buf.write_varint(len(self.slot_data))
        for slot in self.slot_data:
            slot.serialize_to(buf)
        self.carried_item.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        window_id = buf.read_value(StructFormat.BYTE)
        state_id = buf.read_varint()
        count = buf.read_varint()
        slot_data = [Slot.deserialize(buf) for _ in range(count)]
        carried_item = Slot.deserialize(buf)
        return cls(window_id=window_id, state_id=state_id, slot_data=slot_data, carried_item=carried_item)


@final
@define
class SetContainerProperty(ClientBoundPacket):
    """Inform the client that part of a GUI window should be updated. (Server -> Client).

    Initialize the SetContainerProperty packet.

    :param window_id: The ID of the window which should be updated.
    :type window_id: int
    :param key: The property to be updated.
    :type key: int
    :param value: The new value for the property.
    :type value: int
    """

    PACKET_ID: ClassVar[int] = 0x14
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    window_id: int  # Registry minecraft:menu
    key: int
    value: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.UBYTE, self.window_id)
        buf.write_value(StructFormat.SHORT, self.key)
        buf.write_value(StructFormat.SHORT, self.value)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        window_id = buf.read_value(StructFormat.UBYTE)
        key = buf.read_value(StructFormat.SHORT)
        value = buf.read_value(StructFormat.SHORT)
        return cls(window_id=window_id, key=key, value=value)


@final
@define
class SetContainerSlot(ClientBoundPacket):
    """Sent by the server when an item in a slot (in a window) is added/removed. (Server -> Client).

    Initialize the SetContainerSlot packet.

    :param window_id: The window which is being updated. 0 for player inventory.
    :type window_id: int
    :param state_id: A server-managed sequence number used to avoid desynchronization.
    :type state_id: int
    :param slot: The slot that should be updated.
    :type slot: int
    :param slot_data: The new data for the slot.
    :type slot_data: Slot
    """

    PACKET_ID: ClassVar[int] = 0x15
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    window_id: int  # Registry minecraft:menu
    state_id: int
    slot: int
    slot_data: Slot

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.BYTE, self.window_id)
        buf.write_varint(self.state_id)
        buf.write_value(StructFormat.SHORT, self.slot)
        self.slot_data.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        window_id = buf.read_value(StructFormat.BYTE)
        state_id = buf.read_varint()
        slot = buf.read_value(StructFormat.SHORT)
        slot_data = Slot.deserialize(buf)
        return cls(window_id=window_id, state_id=state_id, slot=slot, slot_data=slot_data)


@final
@define
class SetCooldown(ClientBoundPacket):
    """Applies a cooldown period to all items with the given type. (Server -> Client).

    Initialize the SetCooldown packet.

    :param item_id: Numeric ID of the item to apply a cooldown to.
    :type item_id: int
    :param cooldown_ticks: Number of ticks to apply a cooldown for, or 0 to clear the cooldown.
    :type cooldown_ticks: int
    """

    PACKET_ID: ClassVar[int] = 0x16
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    item_id: int  # registry minecraft:item
    cooldown_ticks: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.item_id)
        buf.write_varint(self.cooldown_ticks)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        item_id = buf.read_varint()
        cooldown_ticks = buf.read_varint()
        return cls(item_id=item_id, cooldown_ticks=cooldown_ticks)


@final
@define
class ChatSuggestions(ClientBoundPacket):
    """Send chat message completions to clients. (Server -> Client).

    .. warning:: Not used by the Notchian server.

    Initialize the ChatSuggestions packet.

    :param action: 0: Add, 1: Remove, 2: Set
    :type action: int
    :param entries: A list of chat message completions.
    :type entries: list[str]
    """

    PACKET_ID: ClassVar[int] = 0x17
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    action: int
    entries: list[str]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.action)
        buf.write_varint(len(self.entries))
        for entry in self.entries:
            buf.write_utf(entry)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        action = buf.read_varint()
        count = buf.read_varint()
        entries = [buf.read_utf() for _ in range(count)]
        return cls(action=action, entries=entries)


@final
@define
class ClientboundPluginMessage(ClientBoundPacket):
    """Mods and plugins can use this to send their data. (Server -> Client).

    Initialize the ClientboundPluginMessage packet.

    :param channel: Name of the plugin channel used to send the data.
    :type channel: Identifier
    :param data: Any data.
    :type data: bytes
    """

    PACKET_ID: ClassVar[int] = 0x18
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
class DamageEvent(ClientBoundPacket):
    """Sent by the server to indicate that an entity has taken damage. (Server -> Client).

    Initialize the DamageEvent packet.

    :param entity_id: The ID of the entity taking damage.
    :type entity_id: int
    :param source_type_id: The type of damage in the minecraft:damage_type registry, defined by the Registry Data
    packet.
    :type source_type_id: int
    :param source_cause_id: The ID + 1 of the entity responsible for the damage, if present. If not present, the value
    is 0.
    :type source_cause_id: int
    :param source_direct_id: The ID + 1 of the entity that directly dealt the damage, if present. If not present, the
    value is 0.
    :type source_direct_id: int
    :param has_source_position: Indicates the presence of the three following fields.
    :type has_source_position: bool
    :param source_position_x: The x coordinate of the source position, if present.
    :type source_position_x: float, optional
    :param source_position_y: The y coordinate of the source position, if present.
    :type source_position_y: float, optional
    :param source_position_z: The z coordinate of the source position, if present.
    :type source_position_z: float, optional
    """

    PACKET_ID: ClassVar[int] = 0x19
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    source_type_id: int
    source_cause_id: int
    source_direct_id: int
    has_source_position: bool
    source_position_x: float | None = None
    source_position_y: float | None = None
    source_position_z: float | None = None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_varint(self.source_type_id)
        buf.write_varint(self.source_cause_id)
        buf.write_varint(self.source_direct_id)
        buf.write_value(StructFormat.BYTE, int(self.has_source_position))
        if self.has_source_position:
            self.source_position_x = cast(float, self.source_position_x)
            self.source_position_y = cast(float, self.source_position_y)
            self.source_position_z = cast(float, self.source_position_z)

            buf.write_value(StructFormat.DOUBLE, self.source_position_x)
            buf.write_value(StructFormat.DOUBLE, self.source_position_y)
            buf.write_value(StructFormat.DOUBLE, self.source_position_z)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        source_type_id = buf.read_varint()
        source_cause_id = buf.read_varint()
        source_direct_id = buf.read_varint()
        has_source_position = bool(buf.read_value(StructFormat.BYTE))
        source_position_x = None
        source_position_y = None
        source_position_z = None
        if has_source_position:
            source_position_x = buf.read_value(StructFormat.DOUBLE)
            source_position_y = buf.read_value(StructFormat.DOUBLE)
            source_position_z = buf.read_value(StructFormat.DOUBLE)
        return cls(
            entity_id=entity_id,
            source_type_id=source_type_id,
            source_cause_id=source_cause_id,
            source_direct_id=source_direct_id,
            has_source_position=has_source_position,
            source_position_x=source_position_x,
            source_position_y=source_position_y,
            source_position_z=source_position_z,
        )

    @override
    def validate(self) -> None:
        if self.has_source_position:
            if self.source_position_x is None:
                raise ValueError("DamageEvent has_source_position requires source_position_x")
            if self.source_position_y is None:
                raise ValueError("DamageEvent has_source_position requires source_position_y")
            if self.source_position_z is None:
                raise ValueError("DamageEvent has_source_position requires source_position_z")


@final
@define
class DeleteMessage(ClientBoundPacket):
    """Removes a message from the client's chat. (Server -> Client).

    Initialize the DeleteMessage packet.

    :param message_id: The message Id + 1, used for validating message signature.
    :type message_id: int
    :param signature: The previous message's signature. Always 256 bytes and not length-prefixed.
    :type signature: bytes, optional
    """

    PACKET_ID: ClassVar[int] = 0x1A
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    message_id: int
    signature: bytes | None = None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.message_id)
        if self.signature is not None:
            buf.write(self.signature)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        message_id = buf.read_varint()
        signature = None
        if message_id == 0:
            signature = bytes(buf.read(256))
        return cls(message_id=message_id, signature=signature)


@final
@define
class Disconnect(ClientBoundPacket):
    """Sent by the server before it disconnects a client. (Server -> Client).

    Initialize the Disconnect packet.

    :param reason: Displayed to the client when the connection terminates.
    :type reason: TextComponent
    """

    PACKET_ID: ClassVar[int] = 0x1B
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

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
class DisguisedChatMessage(ClientBoundPacket):
    """Sends the client a chat message, but without any message signing information. (Server -> Client).

    Initialize the DisguisedChatMessage packet.

    :param message: This is used as the content parameter when formatting the message on the client.
    :type message: TextComponent
    :param chat_type: The type of chat in the minecraft:chat_type registry, defined by the Registry Data packet.
    :type chat_type: int
    :param sender_name: The name of the one sending the message, usually the sender's display name.
    :type sender_name: TextComponent
    :param has_target_name: True if target name is present.
    :type has_target_name: bool
    :param target_name: The name of the one receiving the message, usually the receiver's display name. Only present if
    previous boolean is true.
    :type target_name: TextComponent, optional
    """

    PACKET_ID: ClassVar[int] = 0x1C
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    message: TextComponent
    chat_type: int
    sender_name: TextComponent
    has_target_name: bool
    target_name: TextComponent | None = None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.message.serialize_to(buf)
        buf.write_varint(self.chat_type)
        self.sender_name.serialize_to(buf)
        buf.write_value(StructFormat.BYTE, int(self.has_target_name))
        if self.has_target_name:
            self.target_name = cast(TextComponent, self.target_name)
            self.target_name.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        message = TextComponent.deserialize(buf)
        chat_type = buf.read_varint()
        sender_name = TextComponent.deserialize(buf)
        has_target_name = bool(buf.read_value(StructFormat.BYTE))
        target_name = TextComponent.deserialize(buf) if has_target_name else None
        return cls(
            message=message,
            chat_type=chat_type,
            sender_name=sender_name,
            has_target_name=has_target_name,
            target_name=target_name,
        )

    @override
    def validate(self) -> None:
        if self.has_target_name:
            if self.target_name is None:
                raise ValueError("DisguisedChatMessage has_target_name requires target_name")


@final
@define
class EntityEvent(ClientBoundPacket):
    """Sent by the server to trigger an event on an entity. (Server -> Client).

    Initialize the EntityEvent packet.

    :param entity_id: The entity ID.
    :type entity_id: int
    :param entity_status: The event ID.
    :type entity_status: int
    """

    PACKET_ID: ClassVar[int] = 0x1D
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    entity_status: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_value(StructFormat.BYTE, self.entity_status)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        entity_status = buf.read_value(StructFormat.BYTE)
        return cls(entity_id=entity_id, entity_status=entity_status)


@final
@define
class Explosion(ClientBoundPacket):
    """Sent when an explosion occurs (creepers, TNT, and ghast fireballs). (Server -> Client).

    Each block in Records is set to air. Coordinates for each axis in record is int(X) + record.x

    Initialize the Explosion packet.

    :param x: The X coordinate of the explosion.
    :type x: float
    :param y: The Y coordinate of the explosion.
    :type y: float
    :param z: The Z coordinate of the explosion.
    :type z: float
    :param strength: The strength of the explosion.
    :type strength: float
    :param records: A list of 3 signed bytes long; the 3 bytes are the XYZ (respectively) signed offsets of affected
    blocks.
    :type records: list[tuple[int, int, int]]
    :param player_motion_x: The X velocity of the player being pushed by the explosion.
    :type player_motion_x: float
    :param player_motion_y: The Y velocity of the player being pushed by the explosion.
    :type player_motion_y: float
    :param player_motion_z: The Z velocity of the player being pushed by the explosion.
    :type player_motion_z: float
    :param block_interaction: The block interaction type.
    :type block_interaction: int
    :param small_explosion_particle: The particle data for the small explosion.
    :type small_explosion_particle: :class:`mcproto.data_types.particle_data.ParticleData`
    :param large_explosion_particle: The particle data for the large explosion.
    :type large_explosion_particle: :class:`mcproto.data_types.particle_data.ParticleData`
    :param explosion_sound: The name of the sound played.
    :type explosion_sound: Identifier
    :param explosion_range: The fixed range of the sound.
    :type explosion_range: float, optional
    """

    PACKET_ID: ClassVar[int] = 0x1E
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    x: float
    y: float
    z: float
    strength: float
    records: list[tuple[int, int, int]]
    player_motion_x: float
    player_motion_y: float
    player_motion_z: float
    block_interaction: int
    small_explosion_particle: ParticleData
    large_explosion_particle: ParticleData
    explosion_sound: Identifier
    explosion_range: float | None = None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.DOUBLE, self.x)
        buf.write_value(StructFormat.DOUBLE, self.y)
        buf.write_value(StructFormat.DOUBLE, self.z)
        buf.write_value(StructFormat.FLOAT, self.strength)
        buf.write_varint(len(self.records))
        for record in self.records:
            buf.write_value(StructFormat.BYTE, record[0])
            buf.write_value(StructFormat.BYTE, record[1])
            buf.write_value(StructFormat.BYTE, record[2])
        buf.write_value(StructFormat.FLOAT, self.player_motion_x)
        buf.write_value(StructFormat.FLOAT, self.player_motion_y)
        buf.write_value(StructFormat.FLOAT, self.player_motion_z)
        buf.write_varint(self.block_interaction)
        self.small_explosion_particle.serialize_to(buf)
        self.large_explosion_particle.serialize_to(buf)
        self.explosion_sound.serialize_to(buf)
        buf.write_optional(self.explosion_range, lambda x: buf.write_value(StructFormat.FLOAT, x))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        x = buf.read_value(StructFormat.DOUBLE)
        y = buf.read_value(StructFormat.DOUBLE)
        z = buf.read_value(StructFormat.DOUBLE)
        strength = buf.read_value(StructFormat.FLOAT)
        record_count = buf.read_varint()
        records = [
            (buf.read_value(StructFormat.BYTE), buf.read_value(StructFormat.BYTE), buf.read_value(StructFormat.BYTE))
            for _ in range(record_count)
        ]
        player_motion_x = buf.read_value(StructFormat.FLOAT)
        player_motion_y = buf.read_value(StructFormat.FLOAT)
        player_motion_z = buf.read_value(StructFormat.FLOAT)
        block_interaction = buf.read_varint()
        small_explosion_particle = ParticleData.deserialize(buf)
        large_explosion_particle = ParticleData.deserialize(buf)
        explosion_sound = Identifier.deserialize(buf)
        explosion_range = None
        if buf.remaining:
            explosion_range = buf.read_optional(lambda: buf.read_value(StructFormat.FLOAT))

        return cls(
            x=x,
            y=y,
            z=z,
            strength=strength,
            records=records,
            player_motion_x=player_motion_x,
            player_motion_y=player_motion_y,
            player_motion_z=player_motion_z,
            block_interaction=block_interaction,
            small_explosion_particle=small_explosion_particle,
            large_explosion_particle=large_explosion_particle,
            explosion_sound=explosion_sound,
            explosion_range=explosion_range,
        )


@final
@define
class UnloadChunk(ClientBoundPacket):
    """Tells the client to unload a chunk column. (Server -> Client).

    Initialize the UnloadChunk packet.

    :param chunk_x: The X coordinate of the chunk column.
    :type chunk_x: int
    :param chunk_z: The Z coordinate of the chunk column.
    :type chunk_z: int
    """

    PACKET_ID: ClassVar[int] = 0x1F
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    chunk_x: int
    chunk_z: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        # Note: The order is inverted, because the client reads this packet as one big-endian Long,
        # with Z being the upper 32 bits.
        buf.write_value(StructFormat.INT, self.chunk_z)
        buf.write_value(StructFormat.INT, self.chunk_x)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        chunk_z = buf.read_value(StructFormat.INT)
        chunk_x = buf.read_value(StructFormat.INT)
        return cls(chunk_x=chunk_x, chunk_z=chunk_z)


class GameEventType(IntEnum):
    """wide variety of game events, from weather to bed use to game mode to demo messages."""

    NO_RESPAWN_BLOCK_AVAILABLE = 0
    END_RAINING = 1
    BEGIN_RAINING = 2
    CHANGE_GAME_MODE = 3
    WIN_GAME = 4
    DEMO_EVENT = 5
    ARROW_HIT_PLAYER = 6
    RAIN_LEVEL_CHANGE = 7
    THUNDER_LEVEL_CHANGE = 8
    PUFFER_FISH_STING = 9
    GUARDIAN_ELDER_EFFECT = 10
    IMMEDIATE_RESPAWN = 11
    LIMITED_CRAFTING = 12
    WAIT_FOR_LEVEL_CHUNKS = 13


@final
@define
class GameEvent(ClientBoundPacket):
    """Used for a wide variety of game events (e.g. weather, demo messages, ...) (Server -> Client).

    Initialize the GameEvent packet.

    :param event: The game event type.
    :type event: :class:`mcproto.packets.play.play.GameEventType`
    :param value: The value associated with the game event.
    :type value: float
    """

    PACKET_ID: ClassVar[int] = 0x20
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    event: GameEventType
    value: float

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.UBYTE, self.event.value)
        buf.write_value(StructFormat.FLOAT, self.value)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        event = GameEventType(buf.read_value(StructFormat.UBYTE))
        value = buf.read_value(StructFormat.FLOAT)
        return cls(event=event, value=value)


@final
@define
class OpenHorseScreen(ClientBoundPacket):
    """Used exclusively for opening the horse GUI. (Server -> Client).

    Open Screen is used for all other GUIs. The client will not open the inventory if the Entity ID does not point to
    an horse-like animal.

    Initialize the OpenHorseScreen packet.

    :param window_id: The window ID.
    :type window_id: int
    :param slot_count: The number of slots in the inventory.
    :type slot_count: int
    :param entity_id: The ID of the horse-like animal.
    :type entity_id: int
    """

    PACKET_ID: ClassVar[int] = 0x21
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    window_id: int
    slot_count: int
    entity_id: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.UBYTE, self.window_id)
        buf.write_varint(self.slot_count)
        buf.write_value(StructFormat.INT, self.entity_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        window_id = buf.read_value(StructFormat.UBYTE)
        slot_count = buf.read_varint()
        entity_id = buf.read_value(StructFormat.INT)
        return cls(window_id=window_id, slot_count=slot_count, entity_id=entity_id)


@final
@define
class HurtAnimation(ClientBoundPacket):
    """Plays a bobbing animation for the entity receiving damage. (Server -> Client).

    Initialize the HurtAnimation packet.

    :param entity_id: The ID of the entity taking damage.
    :type entity_id: int
    :param yaw: The direction the damage is coming from in relation to the entity.
    :type yaw: float
    """

    PACKET_ID: ClassVar[int] = 0x22
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    yaw: float

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_value(StructFormat.FLOAT, self.yaw)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        yaw = buf.read_value(StructFormat.FLOAT)
        return cls(entity_id=entity_id, yaw=yaw)


@final
@define
class InitializeWorldBorder(ClientBoundPacket):
    """Initialize World Border (Server -> Client).

    Initialize the InitializeWorldBorder packet.

    :param x: The X coordinate of the world border center.
    :type x: float
    :param z: The Z coordinate of the world border center.
    :type z: float
    :param old_diameter: The current length of a single side of the world border, in meters.
    :type old_diameter: float
    :param new_diameter: The target length of a single side of the world border, in meters.
    :type new_diameter: float
    :param speed: The number of real-time milliseconds until :arg:`new_diameter` is reached.
    :type speed: int
    :param portal_teleport_boundary: The resulting coordinates from a portal teleport are limited to ±value.
    :type portal_teleport_boundary: int
    :param warning_blocks: The warning distance from the world border, in meters.
    :type warning_blocks: int
    :param warning_time: The warning time set by `/worldborder warning time`, in seconds.
    :type warning_time: int
    """

    PACKET_ID: ClassVar[int] = 0x23
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    x: float
    z: float
    old_diameter: float
    new_diameter: float
    speed: int
    portal_teleport_boundary: int
    warning_blocks: int
    warning_time: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.DOUBLE, self.x)
        buf.write_value(StructFormat.DOUBLE, self.z)
        buf.write_value(StructFormat.DOUBLE, self.old_diameter)
        buf.write_value(StructFormat.DOUBLE, self.new_diameter)
        buf.write_varlong(self.speed)
        buf.write_varint(self.portal_teleport_boundary)
        buf.write_varint(self.warning_blocks)
        buf.write_varint(self.warning_time)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        x = buf.read_value(StructFormat.DOUBLE)
        z = buf.read_value(StructFormat.DOUBLE)
        old_diameter = buf.read_value(StructFormat.DOUBLE)
        new_diameter = buf.read_value(StructFormat.DOUBLE)
        speed = buf.read_varlong()
        portal_teleport_boundary = buf.read_varint()
        warning_blocks = buf.read_varint()
        warning_time = buf.read_varint()
        return cls(
            x=x,
            z=z,
            old_diameter=old_diameter,
            new_diameter=new_diameter,
            speed=speed,
            portal_teleport_boundary=portal_teleport_boundary,
            warning_blocks=warning_blocks,
            warning_time=warning_time,
        )


@final
@define
class ClientboundKeepAlive(ClientBoundPacket):
    """The server will frequently send out a keep-alive, each containing a random ID. (Server -> Client).

    The client must respond with the same payload (see Serverbound Keep Alive). If the client does not respond to a
    Keep Alive packet within 15 seconds after it was sent, the server kicks the client. Vice versa, if the server does
    not send any keep-alives for 20 seconds, the client will disconnect and yields a "Timed out" exception.

    The Notchian server uses a system-dependent time in milliseconds to generate the keep alive ID value.

    Initialize the ClientboundKeepAlive packet.

    :param keep_alive_id: The keep alive ID.
    :type keep_alive_id: int
    """

    PACKET_ID: ClassVar[int] = 0x24
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

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
class ChunkDataAndUpdateLight(ClientBoundPacket):
    """Sent when a chunk comes into the client's view distance. (Server -> Client).

    Specifies its terrain, lighting and block entities (e.g. banners, signs, etc.)

    Initialize the ChunkDataAndUpdateLight packet.

    :param chunk_x: The X coordinate of the chunk.
    :type chunk_x: int
    :param chunk_z: The Z coordinate of the chunk.
    :type chunk_z: int
    :param heightmaps: The heightmaps data.
    :type heightmaps: CompoundNBT
    :param data: The chunk data.
    :type data: bytes
    :param block_entities: A list of block entities in the chunk.
    :type block_entities: list[BlockEntity]
    :param sky_light_mask: A bitset containing bits for each section in the world + 2.
    :type sky_light_mask: Bitset
    :param block_light_mask: A bitset containing bits for each section in the world + 2.
    :type block_light_mask: Bitset
    :param empty_sky_light_mask: A bitset containing bits for each section in the world + 2.
    :type empty_sky_light_mask: Bitset
    :param empty_block_light_mask: A bitset containing bits for each section in the world + 2.
    :type empty_block_light_mask: Bitset
    :param sky_light_arrays: A list of sky light arrays.
    :type sky_light_arrays: list[bytes]
    :param block_light_arrays: A list of block light arrays.
    :type block_light_arrays: list[bytes]
    """

    PACKET_ID: ClassVar[int] = 0x25
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    chunk_x: int
    chunk_z: int
    heightmaps: CompoundNBT
    data: bytes
    block_entities: list[BlockEntity]
    sky_light_mask: Bitset
    block_light_mask: Bitset
    empty_sky_light_mask: Bitset
    empty_block_light_mask: Bitset
    sky_light_arrays: list[bytes]
    block_light_arrays: list[bytes]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.INT, self.chunk_x)
        buf.write_value(StructFormat.INT, self.chunk_z)
        self.heightmaps.serialize_to(buf, with_type=True, with_name=False)
        buf.write_varint(len(self.data))
        buf.write(self.data)
        buf.write_varint(len(self.block_entities))
        for block_entity in self.block_entities:
            block_entity.serialize_to(buf)
        self.sky_light_mask.serialize_to(buf)
        self.block_light_mask.serialize_to(buf)
        self.empty_sky_light_mask.serialize_to(buf)
        self.empty_block_light_mask.serialize_to(buf)
        buf.write_varint(len(self.sky_light_arrays))
        for sky_light_array in self.sky_light_arrays:
            buf.write_varint(len(sky_light_array))
            buf.write(sky_light_array)
        buf.write_varint(len(self.block_light_arrays))
        for block_light_array in self.block_light_arrays:
            buf.write_varint(len(block_light_array))
            buf.write(block_light_array)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        chunk_x = buf.read_value(StructFormat.INT)
        chunk_z = buf.read_value(StructFormat.INT)
        heightmaps = CompoundNBT.deserialize(buf, with_type=True, with_name=False)
        size = buf.read_varint()
        data = bytes(buf.read(size))
        num_block_entities = buf.read_varint()
        block_entities = [BlockEntity.deserialize(buf) for _ in range(num_block_entities)]
        sky_light_mask = Bitset.deserialize(buf)
        block_light_mask = Bitset.deserialize(buf)
        empty_sky_light_mask = Bitset.deserialize(buf)
        empty_block_light_mask = Bitset.deserialize(buf)
        sky_light_array_count = buf.read_varint()
        sky_light_arrays = [bytes(buf.read(buf.read_varint())) for _ in range(sky_light_array_count)]
        block_light_array_count = buf.read_varint()
        block_light_arrays = [bytes(buf.read(buf.read_varint())) for _ in range(block_light_array_count)]
        return cls(
            chunk_x=chunk_x,
            chunk_z=chunk_z,
            heightmaps=heightmaps,
            data=data,
            block_entities=block_entities,
            sky_light_mask=sky_light_mask,
            block_light_mask=block_light_mask,
            empty_sky_light_mask=empty_sky_light_mask,
            empty_block_light_mask=empty_block_light_mask,
            sky_light_arrays=sky_light_arrays,
            block_light_arrays=block_light_arrays,
        )


@final
@define
class WorldEvent(ClientBoundPacket):
    """Sent when a client is to play a sound or particle effect. (Server -> Client).

    Initialize the WorldEvent packet.

    :param event: The event type.
    :type event: int
    :param location: The location of the event.
    :type location: Position
    :param data: Extra data for certain events.
    :type data: int
    :param disable_relative_volume: Whether to disable relative volume.
    :type disable_relative_volume: bool
    """

    PACKET_ID: ClassVar[int] = 0x26
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    event: int
    location: Position
    data: int
    disable_relative_volume: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.INT, self.event)
        self.location.serialize_to(buf)
        buf.write_value(StructFormat.INT, self.data)
        buf.write_value(StructFormat.BYTE, int(self.disable_relative_volume))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        event = buf.read_value(StructFormat.INT)
        location = Position.deserialize(buf)
        data = buf.read_value(StructFormat.INT)
        disable_relative_volume = bool(buf.read_value(StructFormat.BYTE))
        return cls(
            event=event,
            location=location,
            data=data,
            disable_relative_volume=disable_relative_volume,
        )


@final
@define
class Particle(ClientBoundPacket):
    """Displays the named particle. (Server -> Client).

    Initialize the Particle packet.

    :param particle: The particle data (including ID).
    :type particle: :class:`mcproto.data_types.particle_data.ParticleData`
    :param long_distance: If true, particle distance increases from 256 to 65536.
    :type long_distance: bool
    :param x: X position of the particle.
    :type x: float
    :param y: Y position of the particle.
    :type y: float
    :param z: Z position of the particle.
    :type z: float
    :param offset_x: This is added to the X position after being multiplied by random.nextGaussian().
    :type offset_x: float
    :param offset_y: This is added to the Y position after being multiplied by random.nextGaussian().
    :type offset_y: float
    :param offset_z: This is added to the Z position after being multiplied by random.nextGaussian().
    :type offset_z: float
    :param max_speed: The maximum speed of the particle.
    :type max_speed: float
    :param particle_count: The number of particles to create.
    :type particle_count: int
    """

    PACKET_ID: ClassVar[int] = 0x27
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    particle: ParticleData
    long_distance: bool
    x: float
    y: float
    z: float
    offset_x: float
    offset_y: float
    offset_z: float
    max_speed: float
    particle_count: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.particle.particle_id)
        buf.write_value(StructFormat.BYTE, int(self.long_distance))
        buf.write_value(StructFormat.DOUBLE, self.x)
        buf.write_value(StructFormat.DOUBLE, self.y)
        buf.write_value(StructFormat.DOUBLE, self.z)
        buf.write_value(StructFormat.FLOAT, self.offset_x)
        buf.write_value(StructFormat.FLOAT, self.offset_y)
        buf.write_value(StructFormat.FLOAT, self.offset_z)
        buf.write_value(StructFormat.FLOAT, self.max_speed)
        buf.write_value(StructFormat.INT, self.particle_count)
        self.particle.serialize_to(buf, with_id=False)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        particle_id = buf.read_varint()
        long_distance = bool(buf.read_value(StructFormat.BYTE))
        x = buf.read_value(StructFormat.DOUBLE)
        y = buf.read_value(StructFormat.DOUBLE)
        z = buf.read_value(StructFormat.DOUBLE)
        offset_x = buf.read_value(StructFormat.FLOAT)
        offset_y = buf.read_value(StructFormat.FLOAT)
        offset_z = buf.read_value(StructFormat.FLOAT)
        max_speed = buf.read_value(StructFormat.FLOAT)
        particle_count = buf.read_value(StructFormat.INT)
        particle = ParticleData.deserialize(buf, particle_id)
        return cls(
            particle=particle,
            long_distance=long_distance,
            x=x,
            y=y,
            z=z,
            offset_x=offset_x,
            offset_y=offset_y,
            offset_z=offset_z,
            max_speed=max_speed,
            particle_count=particle_count,
        )


@final
@define
class UpdateLight(ClientBoundPacket):
    """Updates light levels for a chunk. (Server -> Client).

    Initialize the UpdateLight packet.

    :param chunk_x: The X coordinate of the chunk.
    :type chunk_x: int
    :param chunk_z: The Z coordinate of the chunk.
    :type chunk_z: int
    :param sky_light_mask: A bitset containing bits for each section in the world + 2.
    :type sky_light_mask: Bitset
    :param block_light_mask: A bitset containing bits for each section in the world + 2.
    :type block_light_mask: Bitset
    :param empty_sky_light_mask: A bitset containing bits for each section in the world + 2.
    :type empty_sky_light_mask: Bitset
    :param empty_block_light_mask: A bitset containing bits for each section in the world + 2.
    :type empty_block_light_mask: Bitset
    :param sky_light_arrays: A list of sky light arrays.
    :type sky_light_arrays: list[bytes]
    :param block_light_arrays: A list of block light arrays.
    :type block_light_arrays: list[bytes]
    """

    PACKET_ID: ClassVar[int] = 0x28
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    chunk_x: int
    chunk_z: int
    sky_light_mask: Bitset
    block_light_mask: Bitset
    empty_sky_light_mask: Bitset
    empty_block_light_mask: Bitset
    sky_light_arrays: list[bytes]
    block_light_arrays: list[bytes]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.chunk_x)
        buf.write_varint(self.chunk_z)
        self.sky_light_mask.serialize_to(buf)
        self.block_light_mask.serialize_to(buf)
        self.empty_sky_light_mask.serialize_to(buf)
        self.empty_block_light_mask.serialize_to(buf)
        buf.write_varint(len(self.sky_light_arrays))
        for sky_light_array in self.sky_light_arrays:
            buf.write_varint(len(sky_light_array))
            buf.write(sky_light_array)
        buf.write_varint(len(self.block_light_arrays))
        for block_light_array in self.block_light_arrays:
            buf.write_varint(len(block_light_array))
            buf.write(block_light_array)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        chunk_x = buf.read_varint()
        chunk_z = buf.read_varint()
        sky_light_mask = Bitset.deserialize(buf)
        block_light_mask = Bitset.deserialize(buf)
        empty_sky_light_mask = Bitset.deserialize(buf)
        empty_block_light_mask = Bitset.deserialize(buf)
        sky_light_array_count = buf.read_varint()
        sky_light_arrays = [bytes(buf.read(buf.read_varint())) for _ in range(sky_light_array_count)]
        block_light_array_count = buf.read_varint()
        block_light_arrays = [bytes(buf.read(buf.read_varint())) for _ in range(block_light_array_count)]
        return cls(
            chunk_x=chunk_x,
            chunk_z=chunk_z,
            sky_light_mask=sky_light_mask,
            block_light_mask=block_light_mask,
            empty_sky_light_mask=empty_sky_light_mask,
            empty_block_light_mask=empty_block_light_mask,
            sky_light_arrays=sky_light_arrays,
            block_light_arrays=block_light_arrays,
        )


@final
@define
class Login(ClientBoundPacket):
    """Login (play) packet. (Server -> Client).

    Initialize the Login packet.

    :param entity_id: The player's Entity ID (EID).
    :type entity_id: int
    :param is_hardcore: Whether the world is hardcore.
    :type is_hardcore: bool
    :param dimension_names: Identifiers for all dimensions on the server.
    :type dimension_names: list[Identifier]
    :param max_players: Was once used by the client to draw the player list, but now is ignored.
    :type max_players: int
    :param view_distance: Render distance (2-32).
    :type view_distance: int
    :param simulation_distance: The distance that the client will process specific things, such as entities.
    :type simulation_distance: int
    :param reduced_debug_info: If true, a Notchian client shows reduced information on the debug screen.
    :type reduced_debug_info: bool
    :param enable_respawn_screen: Set to false when the doImmediateRespawn gamerule is true.
    :type enable_respawn_screen: bool
    :param do_limited_crafting: Whether players can only craft recipes they have already unlocked.
    :type do_limited_crafting: bool
    :param dimension_type: The type of dimension in the minecraft:dimension_type registry.
    :type dimension_type: Identifier
    :param dimension_name: Name of the dimension being spawned into.
    :type dimension_name: Identifier
    :param hashed_seed: First 8 bytes of the SHA-256 hash of the world's seed.
    :type hashed_seed: int
    :param game_mode: 0: Survival, 1: Creative, 2: Adventure, 3: Spectator.
    :type game_mode: int
    :param previous_game_mode: The previous game mode.
    :type previous_game_mode: int
    :param is_debug: True if the world is a debug mode world; debug mode worlds cannot be modified and have predefined
    blocks.
    :type is_debug: bool
    :param is_flat: True if the world is a superflat world; flat worlds have different void fog and a horizon at y=0
    instead of y=63.
    :type is_flat: bool
    :param has_death_location: If true, then the next two fields are present.
    :type has_death_location: bool
    :param death_dimension_name: Name of the dimension the player died in.
    :type death_dimension_name: Identifier, optional
    :param death_location: The location that the player died at.
    :type death_location: Position, optional
    :param portal_cooldown: The number of ticks until the player can use the portal again.
    :type portal_cooldown: int
    """

    PACKET_ID: ClassVar[int] = 0x29
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    is_hardcore: bool
    dimension_names: list[Identifier]
    max_players: int
    view_distance: int
    simulation_distance: int
    reduced_debug_info: bool
    enable_respawn_screen: bool
    do_limited_crafting: bool
    dimension_type: Identifier
    dimension_name: Identifier
    hashed_seed: int
    game_mode: int
    previous_game_mode: int
    is_debug: bool
    is_flat: bool
    has_death_location: bool = False
    death_dimension_name: Identifier | None = None
    death_location: Position | None = None
    portal_cooldown: int = 0

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.INT, self.entity_id)
        buf.write_value(StructFormat.BYTE, int(self.is_hardcore))
        buf.write_varint(len(self.dimension_names))
        for dimension_name in self.dimension_names:
            dimension_name.serialize_to(buf)
        buf.write_varint(self.max_players)
        buf.write_varint(self.view_distance)
        buf.write_varint(self.simulation_distance)
        buf.write_value(StructFormat.BYTE, int(self.reduced_debug_info))
        buf.write_value(StructFormat.BYTE, int(self.enable_respawn_screen))
        buf.write_value(StructFormat.BYTE, int(self.do_limited_crafting))
        self.dimension_type.serialize_to(buf)
        self.dimension_name.serialize_to(buf)
        buf.write_value(StructFormat.LONGLONG, self.hashed_seed)
        buf.write_value(StructFormat.UBYTE, self.game_mode)
        buf.write_value(StructFormat.BYTE, self.previous_game_mode)
        buf.write_value(StructFormat.BYTE, int(self.is_debug))
        buf.write_value(StructFormat.BYTE, int(self.is_flat))
        buf.write_value(StructFormat.BYTE, int(self.has_death_location))
        if self.has_death_location:
            self.death_dimension_name = cast(Identifier, self.death_dimension_name)
            self.death_location = cast(Position, self.death_location)

            self.death_dimension_name.serialize_to(buf)
            self.death_location.serialize_to(buf)
        buf.write_varint(self.portal_cooldown)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_value(StructFormat.INT)
        is_hardcore = bool(buf.read_value(StructFormat.BYTE))
        dimension_count = buf.read_varint()
        dimension_names = [Identifier.deserialize(buf) for _ in range(dimension_count)]
        max_players = buf.read_varint()
        view_distance = buf.read_varint()
        simulation_distance = buf.read_varint()
        reduced_debug_info = bool(buf.read_value(StructFormat.BYTE))
        enable_respawn_screen = bool(buf.read_value(StructFormat.BYTE))
        do_limited_crafting = bool(buf.read_value(StructFormat.BYTE))
        dimension_type = Identifier.deserialize(buf)
        dimension_name = Identifier.deserialize(buf)
        hashed_seed = buf.read_value(StructFormat.LONGLONG)
        game_mode = buf.read_value(StructFormat.UBYTE)
        previous_game_mode = buf.read_value(StructFormat.BYTE)
        is_debug = bool(buf.read_value(StructFormat.BYTE))
        is_flat = bool(buf.read_value(StructFormat.BYTE))
        has_death_location = bool(buf.read_value(StructFormat.BYTE))
        death_dimension_name = Identifier.deserialize(buf) if has_death_location else None
        death_location = Position.deserialize(buf) if has_death_location else None
        portal_cooldown = buf.read_varint()
        return cls(
            entity_id=entity_id,
            is_hardcore=is_hardcore,
            dimension_names=dimension_names,
            max_players=max_players,
            view_distance=view_distance,
            simulation_distance=simulation_distance,
            reduced_debug_info=reduced_debug_info,
            enable_respawn_screen=enable_respawn_screen,
            do_limited_crafting=do_limited_crafting,
            dimension_type=dimension_type,
            dimension_name=dimension_name,
            hashed_seed=hashed_seed,
            game_mode=game_mode,
            previous_game_mode=previous_game_mode,
            is_debug=is_debug,
            is_flat=is_flat,
            has_death_location=has_death_location,
            death_dimension_name=death_dimension_name,
            death_location=death_location,
            portal_cooldown=portal_cooldown,
        )

    @override
    def validate(self) -> None:
        if self.has_death_location != (self.death_dimension_name is not None and self.death_location is not None):
            raise ValueError("Death dimension name and location must be both present or both absent.")


@final
@define
class MapData(ClientBoundPacket):
    """Updates a rectangular area on a map item. (Server -> Client).

    Initialize the MapData packet.

    :param map_id: Map ID of the map being modified.
    :type map_id: int
    :param scale: From 0 for a fully zoomed-in map (1 block per pixel) to 4 for a fully zoomed-out map (16 blocks per
    pixel).
    :type scale: int
    :param locked: True if the map has been locked in a cartography table.
    :type locked: bool
    :param has_icons: Whether the map has icons.
    :type has_icons: bool
    :param icons: A list of icons on the map.
    :type icons: list[MapIcon] | None
    :param columns: Number of columns updated.
    :type columns: int
    :param rows: Number of rows updated.
    :type rows: int | None
    :param x: X offset of the westernmost column.
    :type x: int | None
    :param z: Z offset of the northernmost row.
    :type z: int | None
    :param data: The map data.
    :type data: bytes | None
    """

    PACKET_ID: ClassVar[int] = 0x2A
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    map_id: int
    scale: int
    locked: bool
    has_icons: bool
    icons: list[MapIcon] | None
    columns: int
    rows: int | None
    x: int | None
    z: int | None
    data: list[int] | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.map_id)
        buf.write_value(StructFormat.BYTE, self.scale)
        buf.write_value(StructFormat.BYTE, int(self.locked))
        buf.write_value(StructFormat.BYTE, int(self.has_icons))
        if self.has_icons:
            self.icons = cast("list[MapIcon]", self.icons)
            buf.write_varint(len(self.icons))
            for icon in self.icons:
                icon.serialize_to(buf)
        buf.write_value(StructFormat.UBYTE, self.columns)
        if self.columns > 0:
            self.rows = cast(int, self.rows)
            self.x = cast(int, self.x)
            self.z = cast(int, self.z)
            self.data = cast("list[int]", self.data)

            buf.write_value(StructFormat.UBYTE, self.rows)
            buf.write_value(StructFormat.UBYTE, self.x)
            buf.write_value(StructFormat.UBYTE, self.z)
            buf.write_varint(len(self.data))
            for datum in self.data:
                buf.write_value(StructFormat.UBYTE, datum)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        map_id = buf.read_varint()
        scale = buf.read_value(StructFormat.BYTE)
        locked = bool(buf.read_value(StructFormat.BYTE))
        has_icons = bool(buf.read_value(StructFormat.BYTE))
        icons = None
        if has_icons:
            icon_count = buf.read_varint()
            icons = [MapIcon.deserialize(buf) for _ in range(icon_count)]
        columns = buf.read_value(StructFormat.UBYTE)
        rows = buf.read_value(StructFormat.UBYTE) if columns > 0 else None
        x = buf.read_value(StructFormat.UBYTE) if columns > 0 else None
        z = buf.read_value(StructFormat.UBYTE) if columns > 0 else None
        data = [buf.read_value(StructFormat.UBYTE) for _ in range(buf.read_varint())] if columns > 0 else None
        return cls(
            map_id=map_id,
            scale=scale,
            locked=locked,
            has_icons=has_icons,
            icons=icons,
            columns=columns,
            rows=rows,
            x=x,
            z=z,
            data=data,
        )


@final
@define
class MerchantOffers(ClientBoundPacket):
    """The list of trades a villager NPC is offering. (Server -> Client).

    Initialize the MerchantOffers packet.

    :param window_id: The ID of the window that is open.
    :type window_id: int
    :param trades: A list of trades offered by the villager.
    :type trades: list[:class:`mcproto.data_types.trade.Trade`]
    :param villager_level: The level of the villager.
    :type villager_level: int
    :param experience: The total experience for this villager.
    :type experience: int
    :param is_regular_villager: True if this is a regular villager; false for the wandering trader.
    :type is_regular_villager: bool
    :param can_restock: True for regular villagers and false for the wandering trader.
    :type can_restock: bool
    """

    PACKET_ID: ClassVar[int] = 0x2B
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    window_id: int
    trades: list[Trade]
    villager_level: int
    experience: int
    is_regular_villager: bool
    can_restock: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.window_id)
        buf.write_varint(len(self.trades))
        for trade in self.trades:
            trade.serialize_to(buf)
        buf.write_varint(self.villager_level)
        buf.write_varint(self.experience)
        buf.write_value(StructFormat.BYTE, int(self.is_regular_villager))
        buf.write_value(StructFormat.BYTE, int(self.can_restock))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        window_id = buf.read_varint()
        size = buf.read_varint()
        trades = [Trade.deserialize(buf) for _ in range(size)]
        villager_level = buf.read_varint()
        experience = buf.read_varint()
        is_regular_villager = bool(buf.read_value(StructFormat.BYTE))
        can_restock = bool(buf.read_value(StructFormat.BYTE))
        return cls(
            window_id=window_id,
            trades=trades,
            villager_level=villager_level,
            experience=experience,
            is_regular_villager=is_regular_villager,
            can_restock=can_restock,
        )


@final
@define
class UpdateEntityPosition(ClientBoundPacket):
    """Indicates that an entity moved less than 8 blocks. (Server -> Client).

    Initialize the UpdateEntityPosition packet.

    :param entity_id: The ID of the entity.
    :type entity_id: int
    :param delta_x: Change in X position as (currentX * 32 - prevX * 32) * 128.
    :type delta_x: int
    :param delta_y: Change in Y position as (currentY * 32 - prevY * 32) * 128.
    :type delta_y: int
    :param delta_z: Change in Z position as (currentZ * 32 - prevZ * 32) * 128.
    :type delta_z: int
    :param on_ground: Whether the entity is on the ground.
    :type on_ground: bool
    """

    PACKET_ID: ClassVar[int] = 0x2C
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    delta_x: int
    delta_y: int
    delta_z: int
    on_ground: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_value(StructFormat.SHORT, self.delta_x)
        buf.write_value(StructFormat.SHORT, self.delta_y)
        buf.write_value(StructFormat.SHORT, self.delta_z)
        buf.write_value(StructFormat.BYTE, int(self.on_ground))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        delta_x = buf.read_value(StructFormat.SHORT)
        delta_y = buf.read_value(StructFormat.SHORT)
        delta_z = buf.read_value(StructFormat.SHORT)
        on_ground = bool(buf.read_value(StructFormat.BYTE))
        return cls(
            entity_id=entity_id,
            delta_x=delta_x,
            delta_y=delta_y,
            delta_z=delta_z,
            on_ground=on_ground,
        )

    @staticmethod
    def deltas(initial: Vec3, final: Vec3) -> tuple[int, int, int]:
        """Calculate the deltas for the UpdateEntityPosition packet.

        :param initial: The initial position.
        :type initial: Vec3
        :param final: The final position.
        :type final: Vec3
        :return: The deltas.

        .. note:: The deltas are calculated as (current * 32 - prev * 32) * 128.

        .. warning:: The deltas must be between -8 and 8, for larger movements use a TeleportEntity packet.
        :rtype: tuple[int, int, int]
        """
        delta_x = int((final.x * 32 - initial.x * 32) * 128)
        delta_y = int((final.y * 32 - initial.y * 32) * 128)
        delta_z = int((final.z * 32 - initial.z * 32) * 128)
        if delta_x < -32768 or delta_x > 32767:
            raise ValueError("Delta X must be between -8 and 8.")
        if delta_y < -32768 or delta_y > 32767:
            raise ValueError("Delta Y must be between -8 and 8.")
        if delta_z < -32768 or delta_z > 32767:
            raise ValueError("Delta Z must be between -8 and 8.")
        return delta_x, delta_y, delta_z


@final
@define
class UpdateEntityPositionAndRotation(ClientBoundPacket):
    """Indicates that an entity rotated and moved. (Server -> Client).

    Initialize the UpdateEntityPositionAndRotation packet.

    :param entity_id: The ID of the entity.
    :type entity_id: int
    :param delta_x: Change in X position as (currentX * 32 - prevX * 32) * 128.
    :type delta_x: int
    :param delta_y: Change in Y position as (currentY * 32 - prevY * 32) * 128.
    :type delta_y: int
    :param delta_z: Change in Z position as (currentZ * 32 - prevZ * 32) * 128.
    :type delta_z: int
    :param yaw: New angle, not a delta.
    :type yaw: Angle
    :param pitch: New angle, not a delta.
    :type pitch: Angle
    :param on_ground: Whether the entity is on the ground.
    :type on_ground: bool
    """

    PACKET_ID: ClassVar[int] = 0x2D
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    delta_x: int
    delta_y: int
    delta_z: int
    yaw: Angle
    pitch: Angle
    on_ground: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_value(StructFormat.SHORT, self.delta_x)
        buf.write_value(StructFormat.SHORT, self.delta_y)
        buf.write_value(StructFormat.SHORT, self.delta_z)
        self.yaw.serialize_to(buf)
        self.pitch.serialize_to(buf)
        buf.write_value(StructFormat.BYTE, int(self.on_ground))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        delta_x = buf.read_value(StructFormat.SHORT)
        delta_y = buf.read_value(StructFormat.SHORT)
        delta_z = buf.read_value(StructFormat.SHORT)
        yaw = Angle.deserialize(buf)
        pitch = Angle.deserialize(buf)
        on_ground = bool(buf.read_value(StructFormat.BYTE))
        return cls(
            entity_id=entity_id,
            delta_x=delta_x,
            delta_y=delta_y,
            delta_z=delta_z,
            yaw=yaw,
            pitch=pitch,
            on_ground=on_ground,
        )


@final
@define
class UpdateEntityRotation(ClientBoundPacket):
    """Indicates that an entity rotated. (Server -> Client).

    Initialize the UpdateEntityRotation packet.

    :param entity_id: The ID of the entity.
    :type entity_id: int
    :param yaw: New angle, not a delta.
    :type yaw: Angle
    :param pitch: New angle, not a delta.
    :type pitch: Angle
    :param on_ground: Whether the entity is on the ground.
    :type on_ground: bool
    """

    PACKET_ID: ClassVar[int] = 0x2E
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    yaw: Angle
    pitch: Angle
    on_ground: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        self.yaw.serialize_to(buf)
        self.pitch.serialize_to(buf)
        buf.write_value(StructFormat.BYTE, int(self.on_ground))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        yaw = Angle.deserialize(buf)
        pitch = Angle.deserialize(buf)
        on_ground = bool(buf.read_value(StructFormat.BYTE))
        return cls(
            entity_id=entity_id,
            yaw=yaw,
            pitch=pitch,
            on_ground=on_ground,
        )


@final
@define
class MoveVehicle(ClientBoundPacket):
    """Sent to move a vehicle. (Server -> Client).

    Note that all fields use absolute positioning and do not allow for relative positioning.

    Initialize the MoveVehicle packet.

    :param x: Absolute position (X coordinate).
    :type x: float
    :param y: Absolute position (Y coordinate).
    :type y: float
    :param z: Absolute position (Z coordinate).
    :type z: float
    :param yaw: Absolute rotation on the vertical axis, in degrees.
    :type yaw: float
    :param pitch: Absolute rotation on the horizontal axis, in degrees.
    :type pitch: float
    """

    PACKET_ID: ClassVar[int] = 0x2F
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    x: float
    y: float
    z: float
    yaw: float
    pitch: float

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.DOUBLE, self.x)
        buf.write_value(StructFormat.DOUBLE, self.y)
        buf.write_value(StructFormat.DOUBLE, self.z)
        buf.write_value(StructFormat.FLOAT, self.yaw)
        buf.write_value(StructFormat.FLOAT, self.pitch)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        x = buf.read_value(StructFormat.DOUBLE)
        y = buf.read_value(StructFormat.DOUBLE)
        z = buf.read_value(StructFormat.DOUBLE)
        yaw = buf.read_value(StructFormat.FLOAT)
        pitch = buf.read_value(StructFormat.FLOAT)
        return cls(x=x, y=y, z=z, yaw=yaw, pitch=pitch)


@final
@define
class OpenBook(ClientBoundPacket):
    """Sent when a player right clicks with a signed book. (Server -> Client).

    This tells the client to open the book GUI.

    Initialize the OpenBook packet.

    :param off_hand: True if the player is holding the book in their offhand.
    :type off_hand: bool
    """

    PACKET_ID: ClassVar[int] = 0x30
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    off_hand: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(int(self.off_hand))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        off_hand = bool(buf.read_varint())
        return cls(off_hand=off_hand)


@final
@define
class OpenScreen(ClientBoundPacket):
    """Sent to the client when it should open an inventory (Server -> Client).

    This message is not sent to clients opening their own inventory, nor do clients inform the server in any way when
    doing so. From the server's perspective, the inventory is always "open" whenever no other windows are.

    Initialize the OpenScreen packet.

    :param window_id: An identifier for the window to be displayed.
    :type window_id: int
    :param window_type: The window type to use for display. Contained in the `minecraft:menu` registry; see Inventory
    for the different values.
    :type window_type: int
    :param window_title: The title of the window.
    :type window_title: TextComponent
    """

    PACKET_ID: ClassVar[int] = 0x31
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    window_id: int
    window_type: int  # registry minecraft:menu
    window_title: TextComponent

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.window_id)
        buf.write_varint(self.window_type)
        self.window_title.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        window_id = buf.read_varint()
        window_type = buf.read_varint()
        window_title = TextComponent.deserialize(buf)
        return cls(window_id=window_id, window_type=window_type, window_title=window_title)


@final
@define
class OpenSignEditor(ClientBoundPacket):
    """Sent when the client has placed a sign and is allowed to send Update Sign. (Server -> Client).

    There must already be a sign at the given location (which the client does not do automatically) - send a
    :class:`BlockUpdate` first.

    Initialize the OpenSignEditor packet.

    :param location: The position of the sign.
    :type location: Position
    :param is_front_text: Whether the opened editor is for the front or on the back of the sign.
    :type is_front_text: bool
    """

    PACKET_ID: ClassVar[int] = 0x32
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    location: Position
    is_front_text: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.location.serialize_to(buf)
        buf.write_value(StructFormat.BYTE, int(self.is_front_text))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        location = Position.deserialize(buf)
        is_front_text = bool(buf.read_value(StructFormat.BYTE))
        return cls(location=location, is_front_text=is_front_text)


@final
@define
class Ping(ClientBoundPacket):
    """Ping packet sent by the server to the client. (Server -> Client).

    When sent to the client, client responds with a Pong packet with the same id.
    Packet is not used by the Notchian server.

    Initialize the Ping packet.

    :param ping_id: The ID of the ping.
    :type ping_id: int
    """

    PACKET_ID: ClassVar[int] = 0x33
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    ping_id: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.INT, self.ping_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        ping_id = buf.read_value(StructFormat.INT)
        return cls(ping_id=ping_id)


@final
@define
class PingResponse(ClientBoundPacket):
    """Sent in response to a Ping packet. (Server -> Client).

    Initialize the PingResponse packet.

    :param payload: The payload of the ping response.
    :type payload: int
    """

    PACKET_ID: ClassVar[int] = 0x34
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
class PlaceGhostRecipe(ClientBoundPacket):
    """Response to the serverbound packet (:class:`PlaceRecipe`), with the same recipe ID.  (Server -> Client).

    Appears to be used to notify the UI.

    Initialize the PlaceGhostRecipe packet.

    :param window_id: The ID of the window.
    :type window_id: int
    :param recipe: The recipe ID.
    :type recipe: Identifier
    """

    PACKET_ID: ClassVar[int] = 0x35
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    window_id: int
    recipe: Identifier

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.BYTE, self.window_id)
        self.recipe.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        window_id = buf.read_value(StructFormat.BYTE)
        recipe = Identifier.deserialize(buf)
        return cls(window_id=window_id, recipe=recipe)


@final
@define
class PlayerAbilities(ClientBoundPacket):
    """Sent to update the player's abilities. (Server -> Client).

    Initialize the PlayerAbilities packet.

    :param invulnerable: Whether the player is invulnerable.
    :type invulnerable: bool
    :param flying: Whether the player is flying.
    :type flying: bool
    :param allow_flying: Whether the player is allowed to fly.
    :type allow_flying: bool
    :param creative_mode: Whether the player is in creative mode.
    :type creative_mode: bool
    :param flying_speed: The flying speed.
    :type flying_speed: float
    :param field_of_view_modifier: The field of view modifier.
    :type field_of_view_modifier: float
    """

    PACKET_ID: ClassVar[int] = 0x36
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    invulnerable: bool
    flying: bool
    allow_flying: bool
    creative_mode: bool
    flying_speed: float = 0.05
    field_of_view_modifier: float = 0.1

    @override
    def serialize_to(self, buf: Buffer) -> None:
        flags = (
            (int(self.invulnerable) << 0)
            | (int(self.flying) << 1)
            | (int(self.allow_flying) << 2)
            | (int(self.creative_mode) << 3)
        )
        buf.write_value(StructFormat.BYTE, flags)
        buf.write_value(StructFormat.FLOAT, self.flying_speed)
        buf.write_value(StructFormat.FLOAT, self.field_of_view_modifier)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        flags = buf.read_value(StructFormat.BYTE)
        invulnerable = bool(flags & 0x01)
        flying = bool(flags & 0x02)
        allow_flying = bool(flags & 0x04)
        creative_mode = bool(flags & 0x08)
        flying_speed = buf.read_value(StructFormat.FLOAT)
        field_of_view_modifier = buf.read_value(StructFormat.FLOAT)
        return cls(
            invulnerable=invulnerable,
            flying=flying,
            allow_flying=allow_flying,
            creative_mode=creative_mode,
            flying_speed=flying_speed,
            field_of_view_modifier=field_of_view_modifier,
        )


@final
@define
class PlayerChatMessage(ClientBoundPacket):
    """Sends the client a chat message from a player. (Server -> Client).

    Initialize the PlayerChatMessage packet.

    :param sender: The UUID of the sender.
    :type sender: UUID
    :param index: The index of the message.
    :type index: int
    :param message_signature_bytes: The message signature bytes.
    :type message_signature_bytes: bytes, optional
    :param body: The raw (optionally signed) sent message content.
    :type body: str
    :param timestamp: The time the message was signed as milliseconds since the epoch.
    :type timestamp: int
    :param salt: The salt used for validating the message signature.
    :type salt: int
    :param previous_messages: A list of previous messages.
    :type previous_messages: list[tuple[int, bytes]]
    :param unsigned_content: The unsigned content. Only present if unsigned_content_present is True.
    :type unsigned_content: TextComponent, optional
    :param filter_type: The type of filtering applied to the message.
    :type filter_type: int
    :param filter_type_bits: The bits specifying the indexes at which characters in the original message string should
    be replaced with the # symbol. Only present if filter_type is 2.
    :type filter_type_bits: BitSet, optional
    :param chat_formatting: The type of chat in the minecraft:chat_type registry.
    :type chat_formatting: int
    :param sender_name: The name of the one sending the message.
    :type sender_name: TextComponent
    :param target_name: The name of the one receiving the message.
    :type target_name: TextComponent, optional
    """

    PACKET_ID: ClassVar[int] = 0x37
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    sender: UUID
    index: int
    message_signature_bytes: bytes | None
    body: str
    timestamp: int
    salt: int
    previous_messages: list[tuple[int, bytes | None]]
    unsigned_content: TextComponent | None
    filter_type: int
    filter_type_bits: Bitset | None
    chat_formatting: int
    sender_name: TextComponent
    target_name: TextComponent | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.sender.serialize_to(buf)
        buf.write_varint(self.index)
        buf.write_optional(self.message_signature_bytes, buf.write)
        buf.write_utf(self.body)
        buf.write_value(StructFormat.LONGLONG, self.timestamp)
        buf.write_value(StructFormat.LONGLONG, self.salt)
        buf.write_varint(len(self.previous_messages))
        for message_id, signature in self.previous_messages:
            buf.write_varint(message_id)
            if message_id == 0:
                signature = cast(bytes, signature)
                buf.write(signature)
        buf.write_optional(self.unsigned_content, lambda x: x.serialize_to(buf))
        buf.write_varint(self.filter_type)
        if self.filter_type == 2:  # Partially Filtered
            self.filter_type_bits = cast(Bitset, self.filter_type_bits)
            self.filter_type_bits.serialize_to(buf)
        buf.write_varint(self.chat_formatting)
        self.sender_name.serialize_to(buf)
        buf.write_optional(self.target_name, lambda x: x.serialize_to(buf))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        sender = UUID.deserialize(buf)
        index = buf.read_varint()
        message_signature_bytes = buf.read_optional(lambda: bytes(buf.read(256)))
        body = buf.read_utf()
        timestamp = buf.read_value(StructFormat.LONGLONG)
        salt = buf.read_value(StructFormat.LONGLONG)
        total_previous_messages = buf.read_varint()
        previous_messages: list[tuple[int, bytes | None]] = []
        for _ in range(total_previous_messages):
            message_id = buf.read_varint()
            signature = bytes(buf.read(256)) if message_id == 0 else None
            previous_messages.append((message_id, signature))
        unsigned_content = buf.read_optional(lambda: TextComponent.deserialize(buf))
        filter_type = buf.read_varint()
        filter_type_bits = Bitset.deserialize(buf) if filter_type == 2 else None
        chat_formatting = buf.read_varint()
        sender_name = TextComponent.deserialize(buf)
        target_name = buf.read_optional(lambda: TextComponent.deserialize(buf))
        return cls(
            sender=sender,
            index=index,
            message_signature_bytes=message_signature_bytes,
            body=body,
            timestamp=timestamp,
            salt=salt,
            previous_messages=previous_messages,
            unsigned_content=unsigned_content,
            filter_type=filter_type,
            filter_type_bits=filter_type_bits,
            chat_formatting=chat_formatting,
            sender_name=sender_name,
            target_name=target_name,
        )

    @override
    def validate(self) -> None:
        if (self.filter_type == 2) != (self.filter_type_bits is not None):
            raise ValueError("Filter type bits must be present only for partially filtered messages.")


@final
@define
class EndCombat(ClientBoundPacket):
    """Packet once used for twitch.tv metadata circa 1.8. (Server -> Client).

    Unused by the Notchian client.

    Initialize the EndCombat packet.

    :param duration: The length of the combat in ticks.
    :type duration: int
    """

    PACKET_ID: ClassVar[int] = 0x38
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    duration: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.duration)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        duration = buf.read_varint()
        return cls(duration=duration)


@final
@define
class EnterCombat(ClientBoundPacket):
    """Packet once used for twitch.tv metadata circa 1.8. (Server -> Client).

    Unused by the Notchian client.

    Initialize the EnterCombat packet.
    """

    PACKET_ID: ClassVar[int] = 0x39
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
class CombatDeath(ClientBoundPacket):
    """Used to send a respawn screen. (Server -> Client).

    Initialize the CombatDeath packet.

    :param player_id: The entity ID of the player that died.
    :type player_id: int
    :param message: The death message.
    :type message: TextComponent
    """

    PACKET_ID: ClassVar[int] = 0x3A
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    player_id: int
    message: TextComponent

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.player_id)
        self.message.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        player_id = buf.read_varint()
        message = TextComponent.deserialize(buf)
        return cls(player_id=player_id, message=message)
