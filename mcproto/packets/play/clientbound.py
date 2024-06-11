from __future__ import annotations

from abc import abstractmethod
from enum import IntEnum
from typing import ClassVar, cast
from typing import final
import warnings
from typing_extensions import override, Self

from mcproto.packets import ClientBoundPacket, GameState
from mcproto.buffer import Buffer
from mcproto.protocol.base_io import StructFormat
from mcproto.utils.abc import Serializable, RequiredParamsABCMixin
from attrs import define


from mcproto.types import (
    Angle,
    UUID,
    Position,
    RegistryTag,
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
    EntityMetadata,
    Advancement,
    AdvancementProgress,
    ModifierData,
    Recipe,
)
from mcproto.types.nbt import EndNBT


@final
@define
class BundleDelimiter(ClientBoundPacket):
    """The delimiter for a bundle of packets. (Server -> Client).

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
    """Sent by the server when an entity (aside from Experience Orb) is created. (Server -> Client).

    Initialize the SpawnEntity packet.

    :param entity_id: A unique integer ID mostly used in the protocol to identify the entity.
    :type entity_id: int
    :param entity_uuid: A unique identifier that is mostly used in persistence.
    :type entity_uuid: UUID
    :param entity_type: ID in the minecraft:entity_type registry (see "type" field in Entity metadata#Entities).
    :type entity_type: int
    :param entity_position: The position of the entity.
    :type entity_position: :class:`mcproto.types.Vec3`
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
    entity_position: Vec3
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
        self.entity_position.serialize_to_double(buf)
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
        entity_position = Vec3.deserialize_double(buf)
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
            entity_position=entity_position,
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
    """Spawns one or more experience orbs. (Server -> Client).

    Initialize the SpawnExperienceOrb packet.

    :param entity_id: A unique integer ID mostly used in the protocol to identify the entity.
    :type entity_id: int
    :param position: The position of the orb.
    :type position: :class:`~mcproto.types.Vec3`
    :param count: The amount of experience this orb will reward once collected.
    :type count: int
    """

    PACKET_ID: ClassVar[int] = 0x02
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    position: Vec3
    count: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        self.position.serialize_to_double(buf)
        buf.write_value(StructFormat.SHORT, self.count)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        position = Vec3.deserialize_double(buf)
        count = buf.read_value(StructFormat.SHORT)
        return cls(entity_id=entity_id, position=position, count=count)


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
    """Sent whenever an entity should change animation. (Server -> Client).

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
    """Informs the client of its current statistics. (Server -> Client).

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
    """Acknowledges a user-initiated block change. (Server -> Client).

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
    """Sets the block destroy stage at the given location. (Server -> Client).

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
        buf.write_value(StructFormat.BOOL, self.locked)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        difficulty = buf.read_value(StructFormat.BYTE)
        locked = bool(buf.read_value(StructFormat.BOOL))
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
        buf.write_value(StructFormat.BOOL, self.reset)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        reset = bool(buf.read_value(StructFormat.BOOL))
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
    :type matches: list[tuple[str, TextComponent | None]]
    """

    PACKET_ID: ClassVar[int] = 0x10
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    transaction_id: int
    start: int
    length: int
    matches: list[tuple[str, TextComponent | None]]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.transaction_id)
        buf.write_varint(self.start)
        buf.write_varint(self.length)
        buf.write_varint(len(self.matches))
        for match, tooltip in self.matches:
            buf.write_utf(match)
            buf.write_optional(tooltip, lambda x: x.serialize_to(buf))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        transaction_id = buf.read_varint()
        start = buf.read_varint()
        length = buf.read_varint()
        count = buf.read_varint()
        matches: list[tuple[str, TextComponent | None]] = []
        for _ in range(count):
            match = buf.read_utf()
            tooltip = buf.read_optional(lambda: TextComponent.deserialize(buf))
            matches.append((match, tooltip))
        return cls(transaction_id=transaction_id, start=start, length=length, matches=matches)


@final
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
class CookieRequest(ClientBoundPacket):
    """Requests a cookie that was previously stored.

    Initialize the CookieRequest packet.

    :param identifier: The identifier of the cookie.
    :type: :class:`mcproto.types.Identifier`
    """

    PACKET_ID: ClassVar[int] = 0x16
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    identifier: Identifier

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.identifier.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        identifier = Identifier.deserialize(buf)
        return cls(identifier=identifier)


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

    PACKET_ID: ClassVar[int] = 0x17
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

    PACKET_ID: ClassVar[int] = 0x18
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

    PACKET_ID: ClassVar[int] = 0x19
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
    :param source_position: The position of the source of the damage.
    :type source_position: :class:`mcproto.types.Vec3`, optional
    """

    PACKET_ID: ClassVar[int] = 0x1A
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    source_type_id: int
    source_cause_id: int
    source_direct_id: int
    source_position: Vec3 | None = None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_varint(self.source_type_id)
        buf.write_varint(self.source_cause_id)
        buf.write_varint(self.source_direct_id)
        buf.write_optional(self.source_position, lambda x: x.serialize_to_double(buf))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        source_type_id = buf.read_varint()
        source_cause_id = buf.read_varint()
        source_direct_id = buf.read_varint()
        source_position = buf.read_optional(lambda: Vec3.deserialize_double(buf))
        return cls(
            entity_id=entity_id,
            source_type_id=source_type_id,
            source_cause_id=source_cause_id,
            source_direct_id=source_direct_id,
            source_position=source_position,
        )


class DebugSampleType(IntEnum):
    """Represents the different debug sample types."""

    TICK_TIME = 0


@final
@define
class DebugSample(ClientBoundPacket):
    """Sent periodically after the client has subscribed with Debug Sample Subscription. (Server -> Client).

    The Notchian server only sends debug samples to players that are server operators.
    :param sample_data: Array of type-dependent samples.
    :type: list[int]
    :param sample_type: The type of debug sample.
    :type sample_type: :class:`DebugSampleType`
    """

    PACKET_ID: ClassVar[int] = 0x1B
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    sample_data: list[int]
    sample_type: DebugSampleType

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(len(self.sample_data))
        for data in self.sample_data:
            buf.write_varint(data)
        buf.write_varint(self.sample_type)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        sample_data = [buf.read_varint() for _ in range(buf.read_varint())]
        sample_type = DebugSampleType(buf.read_varint())
        return cls(sample_data=sample_data, sample_type=sample_type)


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

    PACKET_ID: ClassVar[int] = 0x1C
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

    PACKET_ID: ClassVar[int] = 0x1D
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
    :param target_name: The name of the one receiving the message, usually the receiver's display name.
    :type target_name: TextComponent, optional
    """

    PACKET_ID: ClassVar[int] = 0x1E
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    message: TextComponent
    chat_type: int
    sender_name: TextComponent
    target_name: TextComponent | None = None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.message.serialize_to(buf)
        buf.write_varint(self.chat_type)
        self.sender_name.serialize_to(buf)
        buf.write_optional(self.target_name, lambda x: x.serialize_to(buf))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        message = TextComponent.deserialize(buf)
        chat_type = buf.read_varint()
        sender_name = TextComponent.deserialize(buf)
        target_name = buf.read_optional(lambda: TextComponent.deserialize(buf))
        return cls(
            message=message,
            chat_type=chat_type,
            sender_name=sender_name,
            target_name=target_name,
        )


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

    PACKET_ID: ClassVar[int] = 0x1F
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

    :param position: The position of the explosion.
    :type position: :class:`mcproto.types.Vec3`
    :param strength: The strength of the explosion.
    :type strength: float
    :param records: A list of 3 signed bytes long; the 3 bytes are the XYZ (respectively) signed offsets of affected
    blocks.
    :type records: list[tuple[int, int, int]]
    :param player_motion: The velocity of the player being pushed by the explosion.
    :type player_motion: :class:`mcproto.types.Vec3`
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

    PACKET_ID: ClassVar[int] = 0x20
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    position: Vec3
    strength: float
    records: list[tuple[int, int, int]]
    player_motion: Vec3
    block_interaction: int
    small_explosion_particle: ParticleData
    large_explosion_particle: ParticleData
    explosion_sound: Identifier
    explosion_range: float | None = None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.position.serialize_to_double(buf)
        buf.write_value(StructFormat.FLOAT, self.strength)
        buf.write_varint(len(self.records))
        for record in self.records:
            buf.write_value(StructFormat.BYTE, record[0])
            buf.write_value(StructFormat.BYTE, record[1])
            buf.write_value(StructFormat.BYTE, record[2])
        self.player_motion.serialize_to(buf)
        buf.write_varint(self.block_interaction)
        self.small_explosion_particle.serialize_to(buf)
        self.large_explosion_particle.serialize_to(buf)
        self.explosion_sound.serialize_to(buf)
        buf.write_optional(self.explosion_range, lambda x: buf.write_value(StructFormat.FLOAT, x))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        position = Vec3.deserialize_double(buf)
        strength = buf.read_value(StructFormat.FLOAT)
        record_count = buf.read_varint()
        records = [
            (buf.read_value(StructFormat.BYTE), buf.read_value(StructFormat.BYTE), buf.read_value(StructFormat.BYTE))
            for _ in range(record_count)
        ]
        player_motion = Vec3.deserialize(buf)
        block_interaction = buf.read_varint()
        small_explosion_particle = ParticleData.deserialize(buf)
        large_explosion_particle = ParticleData.deserialize(buf)
        explosion_sound = Identifier.deserialize(buf)
        explosion_range = None
        if buf.remaining:
            explosion_range = buf.read_optional(lambda: buf.read_value(StructFormat.FLOAT))

        return cls(
            position=position,
            strength=strength,
            records=records,
            player_motion=player_motion,
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

    PACKET_ID: ClassVar[int] = 0x21
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

    PACKET_ID: ClassVar[int] = 0x22
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

    PACKET_ID: ClassVar[int] = 0x23
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

    PACKET_ID: ClassVar[int] = 0x24
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

    PACKET_ID: ClassVar[int] = 0x25
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

    PACKET_ID: ClassVar[int] = 0x26
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

    PACKET_ID: ClassVar[int] = 0x27
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

    PACKET_ID: ClassVar[int] = 0x28
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
        buf.write_value(StructFormat.BOOL, self.disable_relative_volume)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        event = buf.read_value(StructFormat.INT)
        location = Position.deserialize(buf)
        data = buf.read_value(StructFormat.INT)
        disable_relative_volume = bool(buf.read_value(StructFormat.BOOL))
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
    :param position: The position of the particle.
    :type position: :class:`mcproto.types.Vec3`
    :param offset: The offset of the particle.
    :type offset: :class:`mcproto.types.Vec3`
    :param max_speed: The maximum speed of the particle.
    :type max_speed: float
    :param particle_count: The number of particles to create.
    :type particle_count: int
    """

    PACKET_ID: ClassVar[int] = 0x29
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    particle: ParticleData
    long_distance: bool
    position: Vec3
    offset: Vec3
    max_speed: float
    particle_count: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.particle.particle_id)
        buf.write_value(StructFormat.BOOL, self.long_distance)
        self.position.serialize_to_double(buf)
        self.offset.serialize_to(buf)
        buf.write_value(StructFormat.FLOAT, self.max_speed)
        buf.write_value(StructFormat.INT, self.particle_count)
        self.particle.serialize_to(buf, with_id=False)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        particle_id = buf.read_varint()
        long_distance = bool(buf.read_value(StructFormat.BOOL))
        position = Vec3.deserialize_double(buf)
        offset = Vec3.deserialize(buf)
        max_speed = buf.read_value(StructFormat.FLOAT)
        particle_count = buf.read_value(StructFormat.INT)
        particle = ParticleData.deserialize(buf, particle_id)
        return cls(
            particle=particle,
            long_distance=long_distance,
            position=position,
            offset=offset,
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

    PACKET_ID: ClassVar[int] = 0x2A
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

    PACKET_ID: ClassVar[int] = 0x2B
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
        buf.write_value(StructFormat.BOOL, self.is_hardcore)
        buf.write_varint(len(self.dimension_names))
        for dimension_name in self.dimension_names:
            dimension_name.serialize_to(buf)
        buf.write_varint(self.max_players)
        buf.write_varint(self.view_distance)
        buf.write_varint(self.simulation_distance)
        buf.write_value(StructFormat.BOOL, self.reduced_debug_info)
        buf.write_value(StructFormat.BOOL, self.enable_respawn_screen)
        buf.write_value(StructFormat.BOOL, self.do_limited_crafting)
        self.dimension_type.serialize_to(buf)
        self.dimension_name.serialize_to(buf)
        buf.write_value(StructFormat.LONGLONG, self.hashed_seed)
        buf.write_value(StructFormat.UBYTE, self.game_mode)
        buf.write_value(StructFormat.BYTE, self.previous_game_mode)
        buf.write_value(StructFormat.BOOL, self.is_debug)
        buf.write_value(StructFormat.BOOL, self.is_flat)
        buf.write_value(StructFormat.BOOL, self.has_death_location)
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
        is_hardcore = bool(buf.read_value(StructFormat.BOOL))
        dimension_count = buf.read_varint()
        dimension_names = [Identifier.deserialize(buf) for _ in range(dimension_count)]
        max_players = buf.read_varint()
        view_distance = buf.read_varint()
        simulation_distance = buf.read_varint()
        reduced_debug_info = bool(buf.read_value(StructFormat.BOOL))
        enable_respawn_screen = bool(buf.read_value(StructFormat.BOOL))
        do_limited_crafting = bool(buf.read_value(StructFormat.BOOL))
        dimension_type = Identifier.deserialize(buf)
        dimension_name = Identifier.deserialize(buf)
        hashed_seed = buf.read_value(StructFormat.LONGLONG)
        game_mode = buf.read_value(StructFormat.UBYTE)
        previous_game_mode = buf.read_value(StructFormat.BYTE)
        is_debug = bool(buf.read_value(StructFormat.BOOL))
        is_flat = bool(buf.read_value(StructFormat.BOOL))
        has_death_location = bool(buf.read_value(StructFormat.BOOL))
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

    PACKET_ID: ClassVar[int] = 0x2C
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
        locked = bool(buf.read_value(StructFormat.BOOL))
        has_icons = bool(buf.read_value(StructFormat.BOOL))
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

    PACKET_ID: ClassVar[int] = 0x2D
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
        is_regular_villager = bool(buf.read_value(StructFormat.BOOL))
        can_restock = bool(buf.read_value(StructFormat.BOOL))
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

    PACKET_ID: ClassVar[int] = 0x2E
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
        on_ground = bool(buf.read_value(StructFormat.BOOL))
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
        :type initial: :class:`mcproto.types.Vec3`
        :param final: The final position.
        :type final: :class:`mcproto.types.Vec3`
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

    PACKET_ID: ClassVar[int] = 0x2F
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
        on_ground = bool(buf.read_value(StructFormat.BOOL))
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

    PACKET_ID: ClassVar[int] = 0x30
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
        on_ground = bool(buf.read_value(StructFormat.BOOL))
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

    :param position: Absolute position (X coordinate).
    :type positio: :class:`mcproto.types.Vec3`
    :param yaw: Absolute rotation on the vertical axis, in degrees.
    :type yaw: float
    :param pitch: Absolute rotation on the horizontal axis, in degrees.
    :type pitch: float
    """

    PACKET_ID: ClassVar[int] = 0x31
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
class OpenBook(ClientBoundPacket):
    """Sent when a player right clicks with a signed book. (Server -> Client).

    This tells the client to open the book GUI.

    Initialize the OpenBook packet.

    :param off_hand: True if the player is holding the book in their offhand.
    :type off_hand: bool
    """

    PACKET_ID: ClassVar[int] = 0x32
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

    PACKET_ID: ClassVar[int] = 0x33
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

    PACKET_ID: ClassVar[int] = 0x34
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
        is_front_text = bool(buf.read_value(StructFormat.BOOL))
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

    PACKET_ID: ClassVar[int] = 0x35
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

    PACKET_ID: ClassVar[int] = 0x36
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

    PACKET_ID: ClassVar[int] = 0x37
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

    PACKET_ID: ClassVar[int] = 0x38
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
    :param unsigned_content: The unsigned content.
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

    PACKET_ID: ClassVar[int] = 0x39
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

    PACKET_ID: ClassVar[int] = 0x3A
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

    PACKET_ID: ClassVar[int] = 0x3B
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

    PACKET_ID: ClassVar[int] = 0x3C
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


@final
@define
class PlayerInfoRemove(ClientBoundPacket):
    """Removes a player from the player list. (Server -> Client).

    Initialize the PlayerInfoRemove packet.

    :param uuids: A list of UUIDs to remove.
    """

    PACKET_ID: ClassVar[int] = 0x3D
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    uuids: list[UUID]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(len(self.uuids))
        for uuid in self.uuids:
            uuid.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        uuids = [UUID.deserialize(buf) for _ in range(buf.read_varint())]
        return cls(uuids=uuids)


@final
@define
class PlayerInfoUpdate(ClientBoundPacket):
    """Update informations in the <tab> player list.

    :param player_acions: The actions for the players
    :type player_acions: dict[:class:`mcproto.types.UUID`,
    list[:class:`PlayerInfoUpdate._PlayerInfoAction`]]

    .. note:: The actions in the list have to be in the the following order:
        - :class:`PlayerInfoUpdate.AddPlayer`
        - :class:`PlayerInfoUpdate.InitializeChat`
        - :class:`PlayerInfoUpdate.UpdateGamemode`
        - :class:`PlayerInfoUpdate.UpdateListed`
        - :class:`PlayerInfoUpdate.UpdateLatency`
        - :class:`PlayerInfoUpdate.UpdateDisplayName`
        Any other order will raise a :class:`ValueError`.
    """

    PACKET_ID: ClassVar[int] = 0x3E
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    class _PlayerInfoAction(Serializable, RequiredParamsABCMixin):
        """Update informations in the <tab> player list."""

        _REQUIRED_CLASS_VARS = ("ACTION_MASK",)
        ACTION_MASK: ClassVar[int]

        __slots__ = ()

        @override
        @abstractmethod
        def serialize_to(self, buf: Buffer) -> None:
            raise NotImplementedError

        @override
        @classmethod
        @abstractmethod
        def deserialize(cls, buf: Buffer) -> Self:
            raise NotImplementedError

    @final
    @define
    class AddPlayer(_PlayerInfoAction):
        """Add a player to the <tab> player list.

        :param name: The player's name.
        :param properties: The player's properties.
        :param signatures: The properties' signatures.
        """

        ACTION_MASK: ClassVar[int] = 0x1

        name: str
        properties: dict[str, str]
        signatures: dict[str, str | None]

        @override
        def serialize_to(self, buf: Buffer) -> None:
            buf.write_utf(self.name)
            buf.write_varint(len(self.properties))
            for key in self.properties:
                buf.write_utf(key)
                buf.write_utf(self.properties[key])
                signature = self.signatures.get(key, None)
                buf.write_optional(signature, buf.write_utf)

        @override
        @classmethod
        def deserialize(cls, buf: Buffer) -> Self:
            name = buf.read_utf()
            properties: dict[str, str] = {}
            signatures: dict[str, str | None] = {}
            for _ in range(buf.read_varint()):
                key = buf.read_utf()
                value = buf.read_utf()
                signature = buf.read_optional(buf.read_utf)
                properties[key] = value
                signatures[key] = signature
            return cls(name, properties=properties, signatures=signatures)

        @override
        def validate(self) -> None:
            if any(key not in self.properties for key in self.signatures):
                raise ValueError("Signatures without properties.")

    @define
    @final
    class InitializeChat(_PlayerInfoAction):
        """Initialize the chat for the player.

        :param chat_session_id: The chat session id.
        :type chat_session_id: :class:`mcproto.types.UUID`, optional
        :param pk_expiration: The expiration time of the public key.
        :type pk_expiration: int, optional
        :param public_key: The public key.
        :type public_key: bytes, optional
        :param pk_signature: The public key signature.
        :type pk_signature: bytes, optional
        """

        ACTION_MASK: ClassVar[int] = 0x2

        chat_session_id: UUID | None
        pk_expiration: int | None
        public_key: bytes | None
        pk_signature: bytes | None

        @override
        def serialize_to(self, buf: Buffer) -> None:
            if self.chat_session_id is not None:
                self.pk_expiration = cast(int, self.pk_expiration)
                self.public_key = cast(bytes, self.public_key)
                self.pk_signature = cast(bytes, self.pk_signature)

                buf.write_value(StructFormat.BOOL, True)
                self.chat_session_id.serialize_to(buf)
                buf.write_value(StructFormat.LONG, self.pk_expiration)  # LONGLONG ?
                buf.write_bytearray(self.public_key)  # Prefixed by its length
                buf.write_bytearray(self.pk_signature)  # Prefixed by its length
            else:
                buf.write_value(StructFormat.BOOL, False)

        @override
        @classmethod
        def deserialize(cls, buf: Buffer) -> Self:
            if buf.read_value(StructFormat.BOOL):
                chat_session_id = UUID.deserialize(buf)
                pk_expiration = buf.read_value(StructFormat.LONG)
                public_key = bytes(buf.read_bytearray())
                pk_signature = bytes(buf.read_bytearray())
            else:
                chat_session_id = None
                pk_expiration = None
                public_key = None
                pk_signature = None

            return cls(
                chat_session_id=chat_session_id,
                pk_expiration=pk_expiration,
                public_key=public_key,
                pk_signature=pk_signature,
            )

        @override
        def validate(self) -> None:
            if not (
                (self.chat_session_id is None)
                == (self.pk_expiration is None)
                == (self.public_key is None)
                == (self.pk_signature is None)
            ):
                raise ValueError("All or none of the optional fields should be set.")

    @define
    @final
    class UpdateGamemode(_PlayerInfoAction):
        """Update the player's gamemode.

        :param gamemode: The player's gamemode.
        """

        ACTION_MASK: ClassVar[int] = 0x4

        gamemode: int

        @override
        def serialize_to(self, buf: Buffer) -> None:
            buf.write_varint(self.gamemode)

        @override
        @classmethod
        def deserialize(cls, buf: Buffer) -> Self:
            return cls(buf.read_varint())

    @define
    @final
    class UpdateListed(_PlayerInfoAction):
        """Update the player's listed players.

        :param listed: Should the player be listed.
        """

        ACTION_MASK: ClassVar[int] = 0x8

        listed: bool

        @override
        def serialize_to(self, buf: Buffer) -> None:
            buf.write_value(StructFormat.BOOL, self.listed)

        @override
        @classmethod
        def deserialize(cls, buf: Buffer) -> Self:
            return cls(buf.read_value(StructFormat.BOOL))

    @define
    @final
    class UpdateLatency(_PlayerInfoAction):
        """Update the player's latency.

        :param latency: The player's latency in milliseconds.
        """

        PING_NOT_AVAILABLE: ClassVar[int] = -1
        PING_5_BARS: ClassVar[int] = 1
        PING_4_BARS: ClassVar[int] = 151
        PING_3_BARS: ClassVar[int] = 301
        PING_2_BARS: ClassVar[int] = 601
        PING_1_BAR: ClassVar[int] = 1001

        ACTION_MASK: ClassVar[int] = 0x10

        latency: int

        @override
        def serialize_to(self, buf: Buffer) -> None:
            buf.write_varint(self.latency)

        @override
        @classmethod
        def deserialize(cls, buf: Buffer) -> Self:
            return cls(buf.read_varint())

    @define
    class UpdateDisplayName(_PlayerInfoAction):
        """Update the player's display name.

        :param display_name: The player's display name.
        :type display_name: :class:`mcproto.types.TextComponent`, optional
        """

        ACTION_MASK: ClassVar[int] = 0x20

        display_name: TextComponent | None

        @override
        def serialize_to(self, buf: Buffer) -> None:
            buf.write_optional(self.display_name, lambda x: x.serialize_to(buf))

        @override
        @classmethod
        def deserialize(cls, buf: Buffer) -> Self:
            return cls(buf.read_optional(lambda: TextComponent.deserialize(buf)))

    ACTIONS: ClassVar[list[type[PlayerInfoUpdate._PlayerInfoAction]]] = [
        AddPlayer,
        InitializeChat,
        UpdateGamemode,
        UpdateListed,
        UpdateLatency,
        UpdateDisplayName,
    ]

    player_actions: dict[UUID, list[PlayerInfoUpdate._PlayerInfoAction]]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        actions = 0
        if len(self.player_actions) == 0:
            buf.write_value(StructFormat.BYTE, actions)
            buf.write_varint(0)
            return
        first_uuid = next(iter(self.player_actions))
        actions = sum(action.ACTION_MASK for action in self.player_actions[first_uuid])
        buf.write_value(StructFormat.BYTE, actions)
        buf.write_varint(len(self.player_actions))
        for uuid, actions in self.player_actions.items():
            uuid.serialize_to(buf)
            for action in actions:
                action.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer) -> Self:
        player_actions: dict[UUID, list[PlayerInfoUpdate._PlayerInfoAction]] = {}
        actions_flags = buf.read_value(StructFormat.BYTE)
        for _ in range(buf.read_varint()):
            uuid = UUID.deserialize(buf)
            actions: list[PlayerInfoUpdate._PlayerInfoAction] = [
                action.deserialize(buf) for action in cls.ACTIONS if action.ACTION_MASK & actions_flags
            ]
            player_actions[uuid] = actions
        return cls(player_actions=player_actions)

    @override
    def validate(self) -> None:
        if len(self.player_actions) == 0:
            return
        first_uuid = next(iter(self.player_actions))
        # Check that the actions are in the right order (increasing order of the ACTION_MASK)
        actions = self.player_actions[first_uuid]
        action_mask_order = [action.ACTION_MASK for action in self.ACTIONS]
        if [action.ACTION_MASK for action in actions] != sorted(action_mask_order):
            raise ValueError("Actions are not in the right order.")
        # Check that all the players have the same actions
        for player_actions in self.player_actions.values():
            if any(p_action.ACTION_MASK != action.ACTION_MASK for p_action, action in zip(player_actions, actions)):
                raise ValueError("All the players should have the same actions.")


class AimWith(IntEnum):
    """Aim with the head or the feet."""

    FEET = 0
    HEAD = 1


@final
@define
class LookAt(ClientBoundPacket):
    """Used to rotate the client player to face the given location or entity (Server -> Client).

    Initialize the LookAt packet.
    :param aim_with: Aim with the head or the feet
    :type aim_with: :class:`AimWith`
    :param target: The target to look at
    :type target: :class:`mcproto.types.Vec3`
    :param entity_id: The entity ID to look at
    :type entity_id: int, optional
    :param entity_anchor: The entity anchor to look at
    :type entity_anchor: :class:`AimWith`, optional
    """

    PACKET_ID: ClassVar[int] = 0x3F
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    aim_with: AimWith
    target: Vec3
    entity_id: int | None
    entity_anchor: AimWith | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.aim_with.value)
        self.target.serialize_to_double(buf)
        if self.entity_id is not None:
            self.entity_anchor = cast(AimWith, self.entity_anchor)
            buf.write_value(StructFormat.BOOL, True)
            buf.write_varint(self.entity_id)
            buf.write_varint(self.entity_anchor.value)
        else:
            buf.write_value(StructFormat.BOOL, False)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer) -> Self:
        aim_with = AimWith(buf.read_varint())
        target = Vec3.deserialize_double(buf)
        if buf.read_value(StructFormat.BOOL):
            entity_id = buf.read_varint()
            entity_anchor = AimWith(buf.read_varint())
        else:
            entity_id = None
            entity_anchor = None
        return cls(aim_with=aim_with, target=target, entity_id=entity_id, entity_anchor=entity_anchor)

    @override
    def validate(self) -> None:
        if (self.entity_id is None) != (self.entity_anchor is None):
            raise ValueError("Entity ID and entity anchor should be both set or both unset.")


@final
@define
class SynchronizePlayerPosition(ClientBoundPacket):
    """Teleports the client, in response to invalid move packets, etc. (Server -> Client).

    Due to latency, the server may receive outdated movement packets sent before the client was aware of the teleport.
    To account for this, the server ignores all movement packets from the client until a Confirm Teleportation packet
    with an ID matching the one sent in the teleport packet is received.

    Yaw is measured in degrees, and does not follow classical trigonometry rules. The unit circle of yaw on the
    XZ-plane starts at (0, 1) and turns counterclockwise, with 90 at (-1, 0), 180 at (0, -1) and 270 at (1, 0).
    Additionally, yaw is not clamped to between 0 and 360 degrees; any number is valid, including negative numbers and
    numbers greater than 360.

    Pitch is measured in degrees, where 0 is looking straight ahead, -90 is looking straight up, and 90 is looking
    straight down.

    Initialize the SynchronizePlayerPosition packet.

    :param position: The new position (each field can be relative or absolute depending on the flags).
    :type position: :class:`mcproto.types.Vec3`
    :param yaw: The new yaw (X axis rotation), can be relative or absolute depending on the flags.
    :type yaw: float
    :param pitch: The new pitch (Y axis rotation), can be relative or absolute depending on the flags.
    :type pitch: float
    :param x_relative: Whether the X coordinate is relative.
    :type x_relative: bool
    :param y_relative: Whether the Y coordinate is relative.
    :type y_relative: bool
    :param z_relative: Whether the Z coordinate is relative.
    :type z_relative: bool
    :param pitch_relative: Whether the pitch is relative.
    :type pitch_relative: bool
    :param yaw_relative: Whether the yaw is relative.
    :type yaw_relative: bool
    :param teleport_id: The teleport ID.
    :type teleport_id: int
    """

    PACKET_ID: ClassVar[int] = 0x40
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    position: Vec3
    yaw: float
    pitch: float
    x_relative: bool
    y_relative: bool
    z_relative: bool
    pitch_relative: bool
    yaw_relative: bool
    teleport_id: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.position.serialize_to_double(buf)
        buf.write_value(StructFormat.FLOAT, self.yaw)
        buf.write_value(StructFormat.FLOAT, self.pitch)
        flags = (
            (int(self.x_relative) << 0)
            | (int(self.y_relative) << 1)
            | (int(self.z_relative) << 2)
            | (int(self.pitch_relative) << 3)
            | (int(self.yaw_relative) << 4)
        )
        buf.write_value(StructFormat.BYTE, flags)
        buf.write_varint(self.teleport_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer) -> Self:
        position = Vec3.deserialize_double(buf)
        yaw = buf.read_value(StructFormat.FLOAT)
        pitch = buf.read_value(StructFormat.FLOAT)
        flags = buf.read_value(StructFormat.BYTE)
        x_relative = bool(flags & 0x01)
        y_relative = bool(flags & 0x02)
        z_relative = bool(flags & 0x04)
        pitch_relative = bool(flags & 0x08)
        yaw_relative = bool(flags & 0x10)
        teleport_id = buf.read_varint()
        return cls(
            position=position,
            yaw=yaw,
            pitch=pitch,
            x_relative=x_relative,
            y_relative=y_relative,
            z_relative=z_relative,
            pitch_relative=pitch_relative,
            yaw_relative=yaw_relative,
            teleport_id=teleport_id,
        )


@final
@define
class UpdateRecipeBook(ClientBoundPacket):
    """Sent to update the recipe book. (Server -> Client).

    Initialize the UpdateRecipeBook packet.

    :param action: The action to perform. 0: init, 1: add, 2: remove.
    :type action: int
    :param crafting_recipe_book_open: Whether the crafting recipe book will be open when the player opens its
    inventory.
    :type crafting_recipe_book_open: bool
    :param crafting_recipe_book_filter_active: Whether the filtering option is active when the player opens its
    inventory.
    :type crafting_recipe_book_filter_active: bool
    :param smelting_recipe_book_open: Whether the smelting recipe book will be open when the player opens its
    inventory.
    :type smelting_recipe_book_open: bool
    :param smelting_recipe_book_filter_active: Whether the filtering option is active when the player opens its
    inventory.
    :type smelting_recipe_book_filter_active: bool
    :param blast_furnace_recipe_book_open: Whether the blast furnace recipe book will be open when the player opens its
    inventory.
    :type blast_furnace_recipe_book_open: bool
    :param blast_furnace_recipe_book_filter_active: Whether the filtering option is active when the player opens its
    inventory.
    :type blast_furnace_recipe_book_filter_active: bool
    :param smoker_recipe_book_open: Whether the smoker recipe book will be open when the player opens its inventory.
    :type smoker_recipe_book_open: bool
    :param smoker_recipe_book_filter_active: Whether the filtering option is active when the player opens its
    inventory.
    :type smoker_recipe_book_filter_active: bool
    :param recipe_ids: A list of recipe IDs.
    :type recipe_ids: list[Identifier]
    :param additional_recipe_ids: An additional list of recipe IDs, only present if action is 0 (init).
    :type additional_recipe_ids: list[Identifier], optional
    """

    PACKET_ID: ClassVar[int] = 0x41
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    action: int
    crafting_recipe_book_open: bool
    crafting_recipe_book_filter_active: bool
    smelting_recipe_book_open: bool
    smelting_recipe_book_filter_active: bool
    blast_furnace_recipe_book_open: bool
    blast_furnace_recipe_book_filter_active: bool
    smoker_recipe_book_open: bool
    smoker_recipe_book_filter_active: bool
    recipe_ids: list[Identifier]
    additional_recipe_ids: list[Identifier] | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.action)
        buf.write_value(StructFormat.BOOL, self.crafting_recipe_book_open)
        buf.write_value(StructFormat.BOOL, self.crafting_recipe_book_filter_active)
        buf.write_value(StructFormat.BOOL, self.smelting_recipe_book_open)
        buf.write_value(StructFormat.BOOL, self.smelting_recipe_book_filter_active)
        buf.write_value(StructFormat.BOOL, self.blast_furnace_recipe_book_open)
        buf.write_value(StructFormat.BOOL, self.blast_furnace_recipe_book_filter_active)
        buf.write_value(StructFormat.BOOL, self.smoker_recipe_book_open)
        buf.write_value(StructFormat.BOOL, self.smoker_recipe_book_filter_active)
        buf.write_varint(len(self.recipe_ids))
        for recipe_id in self.recipe_ids:
            recipe_id.serialize_to(buf)
        if self.action == 0:
            self.additional_recipe_ids = cast("list[Identifier]", self.additional_recipe_ids)
            buf.write_varint(len(self.additional_recipe_ids))
            for recipe_id in self.additional_recipe_ids:
                recipe_id.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        action = buf.read_varint()
        crafting_recipe_book_open = bool(buf.read_value(StructFormat.BOOL))
        crafting_recipe_book_filter_active = bool(buf.read_value(StructFormat.BOOL))
        smelting_recipe_book_open = bool(buf.read_value(StructFormat.BOOL))
        smelting_recipe_book_filter_active = bool(buf.read_value(StructFormat.BOOL))
        blast_furnace_recipe_book_open = bool(buf.read_value(StructFormat.BOOL))
        blast_furnace_recipe_book_filter_active = bool(buf.read_value(StructFormat.BOOL))
        smoker_recipe_book_open = bool(buf.read_value(StructFormat.BOOL))
        smoker_recipe_book_filter_active = bool(buf.read_value(StructFormat.BOOL))
        total_recipe_ids = buf.read_varint()
        recipe_ids = [Identifier.deserialize(buf) for _ in range(total_recipe_ids)]
        additional_recipe_ids = None
        if action == 0:
            total_additional_recipe_ids = buf.read_varint()
            additional_recipe_ids = [Identifier.deserialize(buf) for _ in range(total_additional_recipe_ids)]
        return cls(
            action=action,
            crafting_recipe_book_open=crafting_recipe_book_open,
            crafting_recipe_book_filter_active=crafting_recipe_book_filter_active,
            smelting_recipe_book_open=smelting_recipe_book_open,
            smelting_recipe_book_filter_active=smelting_recipe_book_filter_active,
            blast_furnace_recipe_book_open=blast_furnace_recipe_book_open,
            blast_furnace_recipe_book_filter_active=blast_furnace_recipe_book_filter_active,
            smoker_recipe_book_open=smoker_recipe_book_open,
            smoker_recipe_book_filter_active=smoker_recipe_book_filter_active,
            recipe_ids=recipe_ids,
            additional_recipe_ids=additional_recipe_ids,
        )

    @override
    def validate(self) -> None:
        if (self.action == 0) != (self.additional_recipe_ids is not None):
            raise ValueError("Additional recipe IDs must be present only when action is 0.")
        if not (0 <= self.action <= 2):
            raise ValueError("Action must be between 0 and 2.")
        if self.action != 0 and self.additional_recipe_ids is not None:
            raise ValueError("Additional recipe IDs must not be present when action is not 0.")


@final
@define
class RemoveEntities(ClientBoundPacket):
    """Sent by the server when an entity is to be destroyed on the client. (Server -> Client).

    Initialize the RemoveEntities packet.

    :param entity_ids: The list of entities to destroy.
    :type entity_ids: list[int]
    """

    PACKET_ID: ClassVar[int] = 0x42
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_ids: list[int]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(len(self.entity_ids))
        for entity_id in self.entity_ids:
            buf.write_varint(entity_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        count = buf.read_varint()
        entity_ids = [buf.read_varint() for _ in range(count)]
        return cls(entity_ids=entity_ids)


@final
@define
class RemoveEntityEffect(ClientBoundPacket):
    """Sent by the server to remove an entity effect. (Server -> Client).

    Initialize the RemoveEntityEffect packet.

    :param entity_id: The entity ID.
    :type entity_id: int
    :param effect_id: The effect ID. See this table.
    :type effect_id: int
    """

    PACKET_ID: ClassVar[int] = 0x43
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    effect_id: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_varint(self.effect_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        effect_id = buf.read_varint()
        return cls(entity_id=entity_id, effect_id=effect_id)


@final
@define
class ResetScore(ClientBoundPacket):
    """Sent to the client when it should remove a scoreboard item. (Server -> Client).

    Initialize the ResetScore packet.

    :param entity_name: The entity whose score this is. For players: username; for other entities : UUID.
    :type entity_name: str
    :param objective_name: The name of the objective the score belongs to.
    :type objective_name: str, optional
    """

    PACKET_ID: ClassVar[int] = 0x44
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_name: str
    objective_name: str | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_utf(self.entity_name)
        buf.write_optional(self.objective_name, buf.write_utf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_name = buf.read_utf()
        objective_name = buf.read_optional(buf.read_utf)
        return cls(entity_name=entity_name, objective_name=objective_name)


@final
@define
class RemoveResourcePack(ClientBoundPacket):
    """Remove Resource Pack (play) (Server -> Client).

    Initialize the RemoveResourcePack packet.

    :param uuid: The UUID of the resource pack to be removed.
    :type uuid: :class:`UUID`, optional
    """

    PACKET_ID: ClassVar[int] = 0x45
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

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
    """Add Resource Pack (play) (Server -> Client).

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

    PACKET_ID: ClassVar[int] = 0x46
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

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
        forced = bool(buf.read_value(StructFormat.BOOL))
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
class Respawn(ClientBoundPacket):
    """Change player dimension (Server -> Client).

    To change the player's dimension (overworld/nether/end), send them a respawn packet with the appropriate dimension,
    followed by prechunks/chunks for the new dimension, and finally a position and look packet. (Server -> Client).

    Initialize the Respawn packet.

    :param dimension_type: The ID of type of dimension in the minecraft:dimension_type registry, defined by the
    Registry Data packet.
    :type dimension_type: int
    :param dimension_name: Name of the dimension being spawned into.
    :type dimension_name: Identifier
    :param hashed_seed: First 8 bytes of the SHA-256 hash of the world's seed. Used client side for biome noise.
    :type hashed_seed: int
    :param game_mode: 0: Survival, 1: Creative, 2: Adventure, 3: Spectator.
    :type game_mode: int
    :param previous_game_mode: -1: Undefined (null), 0: Survival, 1: Creative, 2: Adventure, 3: Spectator. The previous
    game mode.
    :type previous_game_mode: int
    :param is_debug: True if the world is a debug mode world; debug mode worlds cannot be modified and have predefined
    blocks.
    :type is_debug: bool
    :param is_flat: True if the world is a superflat world; flat worlds have different void fog and a horizon at y=0
    instead of y=63.
    :type is_flat: bool
    :param death_dimension_name: Name of the dimension the player died in.
    :type death_dimension_name: Identifier, optional
    :param death_location: The location that the player died at.
    :type death_location: Position, optional
    :param portal_cooldown: The number of ticks until the player can use the portal again.
    :type portal_cooldown: int
    :param data_kept: Bit mask. 0x01: Keep attributes, 0x02: Keep metadata. Tells which data should be kept on the
    client side once the player has respawned.
    :type data_kept: int
    """

    PACKET_ID: ClassVar[int] = 0x47
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    dimension_type: int
    dimension_name: Identifier
    hashed_seed: int
    game_mode: int
    previous_game_mode: int
    is_debug: bool
    is_flat: bool
    death_dimension_name: Identifier | None
    death_location: Position | None
    portal_cooldown: int
    data_kept: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.dimension_type)
        self.dimension_name.serialize_to(buf)
        buf.write_value(StructFormat.LONG, self.hashed_seed)
        buf.write_value(StructFormat.UBYTE, self.game_mode)
        buf.write_value(StructFormat.BYTE, self.previous_game_mode)
        buf.write_value(StructFormat.BYTE, int(self.is_debug))
        buf.write_value(StructFormat.BYTE, int(self.is_flat))
        buf.write_value(StructFormat.BYTE, int(self.death_dimension_name is not None))
        if self.death_dimension_name is not None:
            self.death_location = cast(Position, self.death_location)
            self.death_dimension_name.serialize_to(buf)
            self.death_location.serialize_to(buf)
        buf.write_varint(self.portal_cooldown)
        buf.write_value(StructFormat.BYTE, self.data_kept)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        dimension_type = buf.read_varint()
        dimension_name = Identifier.deserialize(buf)
        hashed_seed = buf.read_value(StructFormat.LONG)
        game_mode = buf.read_value(StructFormat.UBYTE)
        previous_game_mode = buf.read_value(StructFormat.BYTE)
        is_debug = bool(buf.read_value(StructFormat.BOOL))
        is_flat = bool(buf.read_value(StructFormat.BOOL))
        has_death_location = bool(buf.read_value(StructFormat.BOOL))
        death_dimension_name = Identifier.deserialize(buf) if has_death_location else None
        death_location = Position.deserialize(buf) if has_death_location else None
        portal_cooldown = buf.read_varint()
        data_kept = buf.read_value(StructFormat.BYTE)
        return cls(
            dimension_type=dimension_type,
            dimension_name=dimension_name,
            hashed_seed=hashed_seed,
            game_mode=game_mode,
            previous_game_mode=previous_game_mode,
            is_debug=is_debug,
            is_flat=is_flat,
            death_dimension_name=death_dimension_name,
            death_location=death_location,
            portal_cooldown=portal_cooldown,
            data_kept=data_kept,
        )

    @override
    def validate(self) -> None:
        if not (0 <= self.game_mode <= 3):
            raise ValueError("Game mode must be between 0 and 3.")
        if not (-1 <= self.previous_game_mode <= 3):
            raise ValueError("Previous game mode must be between -1 and 3.")
        if not (0 <= self.data_kept <= 3):
            raise ValueError("Data kept must be between 0 and 3, only mask 0x01 and 0x02 are allowed.")
        if (self.death_dimension_name is None) != (self.death_location is None):
            raise ValueError("Death dimension name and death location should be both set or both unset.")


@final
@define
class SetHeadRotation(ClientBoundPacket):
    """Changes the direction an entity's head is facing. (Server -> Client).

    While sending the Entity Look packet changes the vertical rotation of the head, sending this packet appears to be
    necessary to rotate the head horizontally.

    Initialize the SetHeadRotation packet.

    :param entity_id: The ID of the entity.
    :type entity_id: int
    :param head_yaw: New angle, not a delta.
    :type head_yaw: Angle
    """

    PACKET_ID: ClassVar[int] = 0x48
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    head_yaw: Angle

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        self.head_yaw.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        head_yaw = Angle.deserialize(buf)
        return cls(entity_id=entity_id, head_yaw=head_yaw)


@final
@define
class UpdateSectionBlocks(ClientBoundPacket):
    """Fired whenever 2 or more blocks are changed within the same chunk on the same tick. (Server -> Client).

    Warning.png Changing blocks in chunks not loaded by the client is unsafe (see note on Block Update).

    Initialize the UpdateSectionBlocks packet.

    :param chunk_section_position: Chunk section coordinate (encoded chunk x and z with each 22 bits, and section y
    with 20 bits, from left to right).
    :type chunk_section_position: int
    :param blocks: Each entry is composed of the block state id, shifted left by 12, and the relative block position
    in the chunk section (4 bits for x, z, and y, from left to right).
    :type blocks: list[int]
    """

    PACKET_ID: ClassVar[int] = 0x49
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    chunk_section_position: int
    blocks: list[int]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.LONG, self.chunk_section_position)
        buf.write_varint(len(self.blocks))
        for block in self.blocks:
            buf.write_varlong(block)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        chunk_section_position = buf.read_value(StructFormat.LONG)
        blocks_array_size = buf.read_varint()
        blocks = [buf.read_varlong() for _ in range(blocks_array_size)]
        return cls(chunk_section_position=chunk_section_position, blocks=blocks)

    def set_chunk_section_position(self, x: int, y: int, z: int) -> Self:
        """Set the chunk section position from the x, y, z section coordinates.

        .. note :: This method is chainable.
        """
        self.chunk_section_position = ((x & 0x3FFFFF) << 42) | (y & 0xFFFFF) | ((z & 0x3FFFFF) << 20)
        return self

    def get_chunk_section_position(self) -> tuple[int, int, int]:
        """Get the x, y, z section coordinates from the chunk section position."""
        x = (self.chunk_section_position >> 42) & 0x3FFFFF
        y = self.chunk_section_position & 0xFFFFF
        z = (self.chunk_section_position >> 20) & 0x3FFFFF
        return x, y, z

    def add_block(self, block_state_id: int, x: int, y: int, z: int) -> Self:
        """Add a block to the list of blocks.

        .. note :: This method is chainable.
        """
        if not (0 <= x <= 15 and 0 <= y <= 15 and 0 <= z <= 15):
            raise ValueError("Block position must be between 0 and 15 (local coordinates).")
        self.blocks.append((block_state_id << 12) | (x << 8) | (z << 4) | y)
        return self

    def get_blocks(self) -> list[tuple[int, int, int, int]]:
        """Get the list of blocks as a list of tuples (block state id, x, y, z)."""
        return [(block >> 12, (block >> 8) & 0xF, block & 0xF, (block >> 4) & 0xF) for block in self.blocks]

    def set_blocks(self, blocks: list[tuple[int, int, int, int]]) -> Self:
        """Set the list of blocks.

        :param blocks: A list of tuples (block state id, x, y, z).

        .. note :: This method is chainable.
        """
        self.blocks = [(block_state_id << 12) | (x << 8) | (z << 4) | y for block_state_id, x, y, z in blocks]
        return self


@final
@define
class SelectAdvancementsTab(ClientBoundPacket):
    """Sent by the server to indicate that the client should switch advancement tab. (Server -> Client).

    Sent either when the client switches tab in the GUI or when an advancement in another tab is made.

    Valid identifiers are:

    - `minecraft:story/root`
    - `minecraft:nether/root`
    - `minecraft:end/root`
    - `minecraft:adventure/root`
    - `minecraft:husbandry/root`

    Initialize the SelectAdvancementsTab packet.

    :param identifier: The identifier of the advancement tab to switch to.
    :type identifier: Identifier, optional
    """

    PACKET_ID: ClassVar[int] = 0x4A
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    identifier: Identifier | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_optional(self.identifier, lambda x: x.serialize_to(buf))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        identifier = buf.read_optional(lambda: Identifier.deserialize(buf))
        return cls(identifier=identifier)


@final
@define
class ServerData(ClientBoundPacket):
    """Informations about the server. (Server -> Client).

    Initialize the ServerData packet.

    :param motd: The server's MOTD.
    :type motd: TextComponent
    :param icon: The server's icon in the PNG format. Only present if 'Has Icon' is true.
    :type icon: bytes, optional
    """

    PACKET_ID: ClassVar[int] = 0x4B
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    motd: TextComponent
    icon: bytes | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.motd.serialize_to(buf)
        buf.write_value(StructFormat.BYTE, int(self.icon is not None))
        if self.icon is not None:
            buf.write_varint(len(self.icon))
            buf.write(self.icon)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        motd = TextComponent.deserialize(buf)
        has_icon = bool(buf.read_value(StructFormat.BOOL))
        icon = bytes(buf.read(buf.read_varint())) if has_icon else None
        return cls(motd=motd, icon=icon)


@final
@define
class SetActionBarText(ClientBoundPacket):
    """Displays a message above the hotbar. (Server -> Client).

    Equivalent to System Chat Message with Overlay set to true, except that chat message blocking isn't performed.
    Used by the Notchian server only to implement the /title command.

    Initialize the SetActionBarText packet.

    :param action_bar_text: The text to display above the hotbar.
    :type action_bar_text: TextComponent
    """

    PACKET_ID: ClassVar[int] = 0x4C
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    action_bar_text: TextComponent

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.action_bar_text.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        action_bar_text = TextComponent.deserialize(buf)
        return cls(action_bar_text=action_bar_text)


@final
@define
class SetBorderCenter(ClientBoundPacket):
    """(Server -> Client).

    Initialize the SetBorderCenter packet.

    :param x: The x coordinate of the border center.
    :type x: float
    :param z: The z coordinate of the border center.
    :type z: float
    """

    PACKET_ID: ClassVar[int] = 0x4D
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    x: float
    z: float

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.DOUBLE, self.x)
        buf.write_value(StructFormat.DOUBLE, self.z)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        x = buf.read_value(StructFormat.DOUBLE)
        z = buf.read_value(StructFormat.DOUBLE)
        return cls(x=x, z=z)


@final
@define
class SetBorderLerpSize(ClientBoundPacket):
    """Indicates how the world border changes over time. (Server -> Client).

    Initialize the SetBorderLerpSize packet.

    :param old_diameter: Current length of a single side of the world border, in meters.
    :type old_diameter: float
    :param new_diameter: Target length of a single side of the world border, in meters.
    :type new_diameter: float
    :param speed: Number of real-time milliseconds until New Diameter is reached.
    :type speed: int
    """

    PACKET_ID: ClassVar[int] = 0x4E
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    old_diameter: float
    new_diameter: float
    speed: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.DOUBLE, self.old_diameter)
        buf.write_value(StructFormat.DOUBLE, self.new_diameter)
        buf.write_varlong(self.speed)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        old_diameter = buf.read_value(StructFormat.DOUBLE)
        new_diameter = buf.read_value(StructFormat.DOUBLE)
        speed = buf.read_varlong()
        return cls(old_diameter=old_diameter, new_diameter=new_diameter, speed=speed)


@final
@define
class SetBorderSize(ClientBoundPacket):
    """Describes a change in the world border size. (Server -> Client).

    Initialize the SetBorderSize packet.

    :param diameter: Length of a single side of the world border, in blocks.
    :type diameter: float
    """

    PACKET_ID: ClassVar[int] = 0x4F
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    diameter: float

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.DOUBLE, self.diameter)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        diameter = buf.read_value(StructFormat.DOUBLE)
        return cls(diameter=diameter)


@final
@define
class SetBorderWarningDelay(ClientBoundPacket):
    """(Server -> Client).

    Initialize the SetBorderWarningDelay packet.

    :param warning_time: In seconds as set by /worldborder warning time.
    :type warning_time: int
    """

    PACKET_ID: ClassVar[int] = 0x50
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    warning_time: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.warning_time)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        warning_time = buf.read_varint()
        return cls(warning_time=warning_time)


@final
@define
class SetBorderWarningDistance(ClientBoundPacket):
    """(Server -> Client).

    Initialize the SetBorderWarningDistance packet.

    :param warning_blocks: In meters.
    :type warning_blocks: int
    """

    PACKET_ID: ClassVar[int] = 0x51
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    warning_blocks: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.warning_blocks)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        warning_blocks = buf.read_varint()
        return cls(warning_blocks=warning_blocks)


@final
@define
class SetCamera(ClientBoundPacket):
    """Sets the entity that the player renders from. (Server -> Client).

    The player's camera will move with the entity and look where it is looking. The entity is often another player,
    but can be any type of entity. The player is unable to move this entity (move packets will act as if they are
    coming from the other entity).

    If the given entity is not loaded by the player, this packet is ignored. To return control to the player, send this
    packet with their entity ID.

    The Notchian server resets this (sends it back to the default entity) whenever the spectated entity is killed or
    the player sneaks, but only if they were spectating an entity. It also sends this packet whenever the player
    switches out of spectator mode (even if they weren't spectating an entity).

    Initialize the SetCamera packet.

    :param camera_id: ID of the entity to set the client's camera to.
    :type camera_id: int
    """

    PACKET_ID: ClassVar[int] = 0x52
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    camera_id: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.camera_id)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        camera_id = buf.read_varint()
        return cls(camera_id=camera_id)


@final
@define
class SetHeldItemClientBound(ClientBoundPacket):
    """Sent to change the player's slot selection. (Server -> Client).

    Initialize the SetHeldItemClientBound packet.

    :param slot: The slot which the player has selected (0-8).
    :type slot: int
    """

    PACKET_ID: ClassVar[int] = 0x53
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    slot: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.BYTE, self.slot)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        slot = buf.read_value(StructFormat.BYTE)
        return cls(slot=slot)


@final
@define
class SetCenterChunk(ClientBoundPacket):
    """Sets the center position of the client's chunk loading area. (Server -> Client).

    Initialize the SetCenterChunk packet.

    :param chunk_x: Chunk X coordinate of the loading area center.
    :type chunk_x: int
    :param chunk_z: Chunk Z coordinate of the loading area center.
    :type chunk_z: int
    """

    PACKET_ID: ClassVar[int] = 0x54
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    chunk_x: int
    chunk_z: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.chunk_x)
        buf.write_varint(self.chunk_z)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        chunk_x = buf.read_varint()
        chunk_z = buf.read_varint()
        return cls(chunk_x=chunk_x, chunk_z=chunk_z)


@final
@define
class SetRenderDistance(ClientBoundPacket):
    """Sent by the integrated singleplayer server when changing render distance. (Server -> Client).

    Initialize the SetRenderDistance packet.

    :param view_distance: Render distance (2-32).
    :type view_distance: int
    """

    PACKET_ID: ClassVar[int] = 0x55
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    view_distance: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.view_distance)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        view_distance = buf.read_varint()
        return cls(view_distance=view_distance)


@final
@define
class SetDefaultSpawnPosition(ClientBoundPacket):
    """Specify the coordinates for the spawn point. (Server -> Client).

    Sent by the server after login to specify the coordinates of the spawn point (the point at which players spawn
    at, and which the compass points to).

    Initialize the SetDefaultSpawnPosition packet.

    :param location: Spawn location.
    :type location: Position
    :param angle: The angle at which to respawn at.
    :type angle: float
    """

    PACKET_ID: ClassVar[int] = 0x56
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    location: Position
    angle: float

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.location.serialize_to(buf)
        buf.write_value(StructFormat.FLOAT, self.angle)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        location = Position.deserialize(buf)
        angle = buf.read_value(StructFormat.FLOAT)
        return cls(location=location, angle=angle)


@final
@define
class DisplayObjective(ClientBoundPacket):
    """Sent to the client when it should display a scoreboard. (Server -> Client).

    Initialize the DisplayObjective packet.

    :param position: The position of the scoreboard. 0: list, 1: sidebar, 2: below name, 3 - 18: team specific sidebar,
    indexed as 3 + team color.
    :type position: int
    :param score_name: The unique name for the scoreboard to be displayed.
    :type score_name: str
    """

    PACKET_ID: ClassVar[int] = 0x57
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    position: int
    score_name: str

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.position)
        buf.write_utf(self.score_name)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        position = buf.read_varint()
        score_name = buf.read_utf()
        return cls(position=position, score_name=score_name)

    @override
    def validate(self) -> None:
        if not (0 <= self.position <= 18):
            raise ValueError("Position must be between 0 and 18.")


@final
@define
class SetEntityMetadata(ClientBoundPacket):
    """Updates one or more metadata properties for an existing entity. (Server -> Client).

    Initialize the SetEntityMetadata packet.

    :param entity_id: The ID of the entity.
    :type entity_id: int
    :param metadata: The metadata to update.
    :type metadata: :class:`mcproto.types.EntityMetadata`
    """

    PACKET_ID: ClassVar[int] = 0x58
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    metadata: EntityMetadata

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        self.metadata.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        metadata = EntityMetadata.deserialize(buf)
        return cls(entity_id=entity_id, metadata=metadata)


@final
@define
class LinkEntities(ClientBoundPacket):
    """Sent when an entity has been leashed to another entity. (Server -> Client).

    Initialize the LinkEntities packet.

    :param attached_entity_id: Attached entity's EID.
    :type attached_entity_id: int
    :param holding_entity_id: ID of the entity holding the lead. Set to -1 to detach.
    :type holding_entity_id: int
    """

    PACKET_ID: ClassVar[int] = 0x59
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    attached_entity_id: int
    holding_entity_id: int | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.INT, self.attached_entity_id)
        buf.write_value(StructFormat.INT, self.holding_entity_id if self.holding_entity_id is not None else -1)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        attached_entity_id = buf.read_value(StructFormat.INT)
        holding_entity_id = buf.read_value(StructFormat.INT)
        if holding_entity_id == -1:
            holding_entity_id = None
        return cls(attached_entity_id=attached_entity_id, holding_entity_id=holding_entity_id)


@final
@define
class SetEntityVelocity(ClientBoundPacket):
    """Set the speed of the entity. (Server -> Client).

    Velocity is in units of 1/8000 of a block per server tick (50ms); for example, -1343 would move
    (-1343 / 8000) = -0.167875 blocks per tick (or -3.3575 blocks per second).

    Initialize the SetEntityVelocity packet.

    :param entity_id: The ID of the entity.
    :type entity_id: int
    :param velocity_x: Velocity on the X axis.
    :type velocity_x: int
    :param velocity_y: Velocity on the Y axis.
    :type velocity_y: int
    :param velocity_z: Velocity on the Z axis.
    :type velocity_z: int
    """

    PACKET_ID: ClassVar[int] = 0x5A
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    velocity_x: int
    velocity_y: int
    velocity_z: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_value(StructFormat.SHORT, self.velocity_x)
        buf.write_value(StructFormat.SHORT, self.velocity_y)
        buf.write_value(StructFormat.SHORT, self.velocity_z)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        velocity_x = buf.read_value(StructFormat.SHORT)
        velocity_y = buf.read_value(StructFormat.SHORT)
        velocity_z = buf.read_value(StructFormat.SHORT)
        return cls(entity_id=entity_id, velocity_x=velocity_x, velocity_y=velocity_y, velocity_z=velocity_z)

    @override
    def validate(self) -> None:
        if not (-32768 <= self.velocity_x <= 32767):
            raise ValueError("Velocity X must be between -32768 and 32767.")
        if not (-32768 <= self.velocity_y <= 32767):
            raise ValueError("Velocity Y must be between -32768 and 32767.")
        if not (-32768 <= self.velocity_z <= 32767):
            raise ValueError("Velocity Z must be between -32768 and 32767.")

    @classmethod
    def from_velocity(cls, entity_id: int, velocity: Vec3) -> Self:
        """Create a SetEntityVelocity packet from a Vec3 velocity in blocks per second."""
        velocity_x = int(velocity.x * 8000 / 20)
        velocity_y = int(velocity.y * 8000 / 20)
        velocity_z = int(velocity.z * 8000 / 20)
        return cls(entity_id=entity_id, velocity_x=velocity_x, velocity_y=velocity_y, velocity_z=velocity_z)

    def get_velocity(self) -> Vec3:
        """Get the velocity as a Vec3 in blocks per second."""
        return Vec3(self.velocity_x * 20 / 8000, self.velocity_y * 20 / 8000, self.velocity_z * 20 / 8000)


class EquipmentSlot(IntEnum):
    """Equipment slot enumeration."""

    MAIN_HAND = 0
    OFF_HAND = 1
    BOOTS = 2
    LEGGINGS = 3
    CHESTPLATE = 4
    HELMET = 5
    BODY = 6


@final
@define
class SetEquipment(ClientBoundPacket):
    """(Server -> Client).

    Initialize the SetEquipment packet.

    :param entity_id: Entity's ID.
    :type entity_id: int
    :param equipment: Array of equipment slots and items.
    :type equipment: list[tuple[:class:`EquipmentSlot`, :class:`mcproto.types.Slot`]]
    """

    PACKET_ID: ClassVar[int] = 0x5B
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    equipment: list[tuple[EquipmentSlot, Slot]]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        for i, (slot, item) in enumerate(self.equipment):
            buf.write_value(StructFormat.BYTE, slot | (0x80 if i < len(self.equipment) - 1 else 0))
            item.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        equipment: list[tuple[EquipmentSlot, Slot]] = []
        while True:
            slot = buf.read_value(StructFormat.BYTE)
            item = Slot.deserialize(buf)
            equipment.append((EquipmentSlot(slot & 0x7F), item))
            if not (slot & 0x80):
                break
        return cls(entity_id=entity_id, equipment=equipment)


@final
@define
class SetExperience(ClientBoundPacket):
    """Sent by the server when the client should change experience levels. (Server -> Client).

    Initialize the SetExperience packet.

    :param experience_bar: Between 0 and 1.
    :type experience_bar: float
    :param level: The player's experience level.
    :type level: int
    :param total_experience: See Experience#Leveling up on the Minecraft Wiki for Total Experience to Level conversion.
    :type total_experience: int
    """

    PACKET_ID: ClassVar[int] = 0x5C
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    experience_bar: float
    level: int
    total_experience: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.FLOAT, self.experience_bar)
        buf.write_varint(self.level)
        buf.write_varint(self.total_experience)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        experience_bar = buf.read_value(StructFormat.FLOAT)
        level = buf.read_varint()
        total_experience = buf.read_varint()
        return cls(experience_bar=experience_bar, level=level, total_experience=total_experience)


@final
@define
class SetHealth(ClientBoundPacket):
    """Sent by the server to set the health of the player it is sent to. (Server -> Client).

    Initialize the SetHealth packet.

    :param health: 0 or less = dead, 20 = full HP.
    :type health: float
    :param food: 0-20.
    :type food: int
    :param food_saturation: Seems to vary from 0.0 to 5.0 in integer increments.
    :type food_saturation: float
    """

    PACKET_ID: ClassVar[int] = 0x5D
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    health: float
    food: int
    food_saturation: float

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.FLOAT, self.health)
        buf.write_varint(self.food)
        buf.write_value(StructFormat.FLOAT, self.food_saturation)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        health = buf.read_value(StructFormat.FLOAT)
        food = buf.read_varint()
        food_saturation = buf.read_value(StructFormat.FLOAT)
        return cls(health=health, food=food, food_saturation=food_saturation)


@final
@define
class UpdateObjectives(ClientBoundPacket):
    """Sent to the client when it should create a new scoreboard objective or remove one. (Server -> Client).

    Initialize the UpdateObjectives packet.

    :param objective_name: A unique name for the objective.
    :type objective_name: str
    :param mode: 0 to create the scoreboard. 1 to remove the scoreboard. 2 to update the display text.
    :type mode: int
    :param objective_value: The text to be displayed for the score. Only if mode is 0 or 2.
    :type objective_value: TextComponent, optional
    :param objective_type: 0 = "integer", 1 = "hearts". Only if mode is 0 or 2.
    :type objective_type: int, optional
    :param number_format: Determines how the score number should be formatted. Only if mode is 0 or 2 and the previous
    boolean is true.
    :type number_format: int, optional
    :param number_format_content: The text to be used as placeholder. Only if mode is 0 or 2 and number_format is 2.
    :type number_format_content: TextComponent, optional
    """

    PACKET_ID: ClassVar[int] = 0x5E
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    objective_name: str
    mode: int
    objective_value: TextComponent | None
    objective_type: int | None
    number_format: int | None
    number_format_content: TextComponent | NBTag | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_utf(self.objective_name)
        buf.write_value(StructFormat.BYTE, self.mode)
        if self.mode in (0, 2):
            self.objective_value = cast(TextComponent, self.objective_value)
            self.objective_type = cast(int, self.objective_type)
            self.objective_value.serialize_to(buf)
            buf.write_varint(self.objective_type)
            buf.write_value(StructFormat.BYTE, int(self.number_format is not None))
            if self.number_format is None:  # Stop here
                return
            buf.write_varint(self.number_format)
            if self.number_format == 2:
                self.number_format_content = cast(TextComponent, self.number_format_content)
                self.number_format_content.serialize_to(buf)
            elif self.number_format == 1:
                self.number_format_content = cast(NBTag, self.number_format_content)
                self.number_format_content.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        objective_name = buf.read_utf()
        mode = buf.read_value(StructFormat.BYTE)
        objective_value = TextComponent.deserialize(buf) if mode in (0, 2) else None
        objective_type = buf.read_varint() if mode in (0, 2) else None
        number_format = buf.read_varint() if mode == 0 or mode == 2 and buf.read_value(StructFormat.BYTE) else None
        number_format_content = None
        if number_format is not None:
            if number_format == 2:
                number_format_content = TextComponent.deserialize(buf)
            elif number_format == 1:
                number_format_content = NBTag.deserialize(buf)
        return cls(
            objective_name=objective_name,
            mode=mode,
            objective_value=objective_value,
            objective_type=objective_type,
            number_format=number_format,
            number_format_content=number_format_content,
        )

    @override
    def validate(self) -> None:
        if not (0 <= self.mode <= 2):
            raise ValueError("Mode must be between 0 and 2.")
        if self.mode in (0, 2):
            if self.objective_value is None:
                raise ValueError("Objective value must be set when mode is 0 or 2.")
            if self.objective_type is None:
                raise ValueError("Objective type must be set when mode is 0 or 2.")
            if self.number_format is not None:
                if self.number_format == 2 and self.number_format_content is None:
                    raise ValueError("Number format content must be set when number format is 2.")
                if self.number_format == 1 and self.number_format_content is None:
                    raise ValueError("Number format content must be set when number format is 1.")


@final
@define
class SetPassengers(ClientBoundPacket):
    """(Server -> Client).

    Initialize the SetPassengers packet.

    :param entity_id: Vehicle's EID.
    :type entity_id: int
    :param passengers: EIDs of entity's passengers.
    :type passengers: list[int]
    """

    PACKET_ID: ClassVar[int] = 0x5F
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    passengers: list[int]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_varint(len(self.passengers))
        for passenger in self.passengers:
            buf.write_varint(passenger)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        passenger_count = buf.read_varint()
        passengers = [buf.read_varint() for _ in range(passenger_count)]
        return cls(entity_id=entity_id, passengers=passengers)


class TeamAction(IntEnum):
    """Team action enumeration."""

    CREATE = 0
    REMOVE = 1
    UPDATE = 2
    ADD_ENTITY = 3
    REMOVE_ENTITY = 4


@final
@define
class UpdateTeams(ClientBoundPacket):
    """Creates and updates teams. (Server -> Client).

    Initialize the UpdateTeams packet.

    :param team_name: The unique name for the team.
    :type team_name: str
    :param action: The action to perform.
    :type action: :class:`TeamAction`
    :param display_name: The team's display name. (`CREATE`, `UPDATE`)
    :type display_name: :class:`mcproto.types.TextComponent`, optional
    :param friendly_fire: Whether friendly fire is enabled. (`CREATE`, `UPDATE`)
    :type friendly_fire: bool, optional
    :param friendly_truesight: Whether friendly invisibles are visible. (`CREATE`, `UPDATE`)
    :type friendly_truesight: bool, optional
    :param name_tag_visibility: The visibility of the team name tag. [`always`, `hideForOtherTeams`, `hideForOwnTeam`,
    `never`] (`CREATE`, `UPDATE`)
    :type name_tag_visibility: str, optional
    :param collision_rule: The collision rule of the team. [`always`, `pushOtherTeams`, `pushOwnTeam`, `never`]
    (`CREATE`, `UPDATE`)
    :type collision_rule: str, optional
    :param color: The team's color. (`CREATE`, `UPDATE`)
    :type color: int, optional
    :param prefix: The team's prefix. (`CREATE`, `UPDATE`)
    :type prefix: :class:`mcproto.types.TextComponent`, optional
    :param suffix: The team's suffix. (`CREATE`, `UPDATE`)
    :type suffix: :class:`mcproto.types.TextComponent`, optional
    :param entities: The entities associated with the action. (`CREATE`, `UPDATE`, `ADD_ENTITY`, `REMOVE_ENTITY`)
    :type entities: list[str], optional
    """

    PACKET_ID: ClassVar[int] = 0x60
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    team_name: str
    action: TeamAction
    display_name: TextComponent | None
    friendly_fire: bool | None
    friendly_truesight: bool | None
    name_tag_visibility: str | None
    collision_rule: str | None
    color: int | None
    prefix: TextComponent | None
    suffix: TextComponent | None
    entities: list[str] | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_utf(self.team_name)
        buf.write_varint(self.action)
        if self.action in (TeamAction.CREATE, TeamAction.UPDATE):
            self.display_name = cast(TextComponent, self.display_name)
            self.friendly_fire = cast(bool, self.friendly_fire)
            self.friendly_truesight = cast(bool, self.friendly_truesight)
            self.name_tag_visibility = cast(str, self.name_tag_visibility)
            self.collision_rule = cast(str, self.collision_rule)
            self.color = cast(int, self.color)
            self.prefix = cast(TextComponent, self.prefix)
            self.suffix = cast(TextComponent, self.suffix)
            self.display_name.serialize_to(buf)

            friendly_flag = (int(self.friendly_fire) << 0) | (int(self.friendly_truesight) << 1)

            buf.write_value(StructFormat.BYTE, friendly_flag)

            buf.write_utf(self.name_tag_visibility)
            buf.write_utf(self.collision_rule)
            buf.write_varint(self.color)
            self.prefix.serialize_to(buf)
            self.suffix.serialize_to(buf)
        if self.action in (TeamAction.CREATE, TeamAction.UPDATE, TeamAction.ADD_ENTITY, TeamAction.REMOVE_ENTITY):
            self.entities = cast("list[str]", self.entities)

            buf.write_varint(len(self.entities))
            for entity in self.entities:
                buf.write_utf(entity)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        team_name = buf.read_utf()
        action = TeamAction(buf.read_varint())
        display_name = None
        friendly_fire = None
        friendly_truesight = None
        name_tag_visibility = None
        collision_rule = None
        color = None
        prefix = None
        suffix = None
        entities: list[str] | None = None

        if action in (TeamAction.CREATE, TeamAction.UPDATE):
            display_name = TextComponent.deserialize(buf)
            friendly_flag = buf.read_value(StructFormat.BYTE)
            friendly_fire = bool(friendly_flag & 0x1)
            friendly_truesight = bool(friendly_flag & 0x2)
            name_tag_visibility = buf.read_utf()
            collision_rule = buf.read_utf()
            color = buf.read_varint()
            prefix = TextComponent.deserialize(buf)
            suffix = TextComponent.deserialize(buf)

        if action in (TeamAction.CREATE, TeamAction.UPDATE, TeamAction.ADD_ENTITY, TeamAction.REMOVE_ENTITY):
            entities = []
            entity_count = buf.read_varint()
            for _ in range(entity_count):
                entities.append(buf.read_utf())

        return cls(
            team_name=team_name,
            action=action,
            display_name=display_name,
            friendly_fire=friendly_fire,
            friendly_truesight=friendly_truesight,
            name_tag_visibility=name_tag_visibility,
            collision_rule=collision_rule,
            color=color,
            prefix=prefix,
            suffix=suffix,
            entities=entities,
        )

    @override
    def validate(self) -> None:
        if self.action in (TeamAction.CREATE, TeamAction.UPDATE):
            if (
                self.display_name is None
                or self.prefix is None
                or self.suffix is None
                or self.color is None
                or self.friendly_fire is None
                or self.friendly_truesight is None
            ):
                raise ValueError(
                    "Display name, prefix, suffix, color, friendly fire, and friendly truesight are required."
                )

            if self.name_tag_visibility not in ("always", "hideForOtherTeams", "hideForOwnTeam", "never"):
                raise ValueError(
                    "Name tag visibility must be one of 'always', 'hideForOtherTeams', 'hideForOwnTeam', 'never'."
                )
            if self.collision_rule not in ("always", "pushOtherTeams", "pushOwnTeam", "never"):
                raise ValueError("Collision rule must be one of 'always', 'pushOtherTeams', 'pushOwnTeam', 'never'.")
            if not (0 <= self.color <= 21):
                raise ValueError("Color must be between 0 and 15.")

        if self.action in (TeamAction.CREATE, TeamAction.UPDATE, TeamAction.ADD_ENTITY, TeamAction.REMOVE_ENTITY):
            if self.entities is None:
                raise ValueError("Entities are required.")


@final
@define
class UpdateScore(ClientBoundPacket):
    """Sent to the client when it should update a scoreboard item. (Server -> Client).

    Initialize the UpdateScore packet.

    :param entity_name: The name of the entity the objective applies to.
    :type entity_name: str
    :param objective_name: A unique name for the objective.
    :type objective_name: str
    :param value: The value of the objective for this entity.
    :type value: :class: int
    :param display_name: The display name of the objective
    :param display_name: :class:`mcproto.types.TextComponent`, optional
    :param number_format: Determines how the score number should be formatted. Only if mode is 0 or 2 and the previous
    boolean is true.
    :type number_format: int, optional
    :param number_format_content: The text to be used as placeholder. Only if mode is 0 or 2 and number_format is 2.
    :type number_format_content: TextComponent, optional
    """

    PACKET_ID: ClassVar[int] = 0x61
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_name: str
    objective_name: str
    value: int
    display_name: TextComponent | None
    number_format: int | None
    number_format_content: TextComponent | NBTag | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_utf(self.entity_name)
        buf.write_utf(self.objective_name)
        buf.write_varint(self.value)
        buf.write_optional(self.display_name, lambda x: x.serialize_to(buf))
        if self.number_format is not None:
            buf.write_value(StructFormat.BOOL, True)
            buf.write_varint(self.number_format)
            if self.number_format == 2:
                self.number_format_content = cast(TextComponent, self.number_format_content)
                self.number_format_content.serialize_to(buf)
            elif self.number_format == 1:
                self.number_format_content = cast(NBTag, self.number_format_content)
                self.number_format_content.serialize_to(buf)
        else:
            buf.write_value(StructFormat.BOOL, False)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer) -> Self:
        entity_name = buf.read_utf()
        objective_name = buf.read_utf()
        value = buf.read_varint()
        display_name = buf.read_optional(lambda: TextComponent.deserialize(buf))
        number_format = None
        number_format_content = None
        if buf.read_value(StructFormat.BOOL):
            number_format = buf.read_varint()
            if number_format == 2:
                number_format_content = TextComponent.deserialize(buf)
            elif number_format == 1:
                number_format_content = NBTag.deserialize(buf)
        return cls(
            entity_name=entity_name,
            objective_name=objective_name,
            value=value,
            display_name=display_name,
            number_format=number_format,
            number_format_content=number_format_content,
        )

    @override
    def validate(self) -> None:
        if self.number_format is not None:
            if not (0 <= self.number_format <= 2):
                raise ValueError("Number format must be between 0 and 2.")
            if self.number_format == 2 and self.number_format_content is None:
                raise ValueError("Number format content must be set when number format is 2.")
            if self.number_format == 1 and self.number_format_content is None:
                raise ValueError("Number format content must be set when number format is 1.")


@final
@define
class SetSimulationDistance(ClientBoundPacket):
    """Sent by the server to set the simulation distance for the client. (Server -> Client).

    Initialize the SetSimulationDistance packet.

    :param simulation_distance: The distance that the client will process specific things, such as entities.
    :type simulation_distance: int
    """

    PACKET_ID: ClassVar[int] = 0x62
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    simulation_distance: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.simulation_distance)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        simulation_distance = buf.read_varint()
        return cls(simulation_distance=simulation_distance)


@final
@define
class SetSubtitleText(ClientBoundPacket):
    """Sent by the server to set the subtitle text for the client. (Server -> Client).

    Initialize the SetSubtitleText packet.

    :param subtitle_text: The subtitle text to display.
    :type subtitle_text: TextComponent
    """

    PACKET_ID: ClassVar[int] = 0x63
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    subtitle_text: TextComponent

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.subtitle_text.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        subtitle_text = TextComponent.deserialize(buf)
        return cls(subtitle_text=subtitle_text)


@final
@define
class UpdateTime(ClientBoundPacket):
    """Sent by the server to update the time for the client. (Server -> Client).

    Initialize the UpdateTime packet.

    :param world_age: In ticks; not changed by server commands.
    :type world_age: int
    :param time_of_day: The world (or region) time, in ticks. If negative the sun will stop moving at the Math.abs of
    the time.
    :type time_of_day: int
    """

    PACKET_ID: ClassVar[int] = 0x64
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    world_age: int
    time_of_day: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.LONG, self.world_age)
        buf.write_value(StructFormat.LONG, self.time_of_day)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        world_age = buf.read_value(StructFormat.LONG)
        time_of_day = buf.read_value(StructFormat.LONG)
        return cls(world_age=world_age, time_of_day=time_of_day)


@final
@define
class SetTitleText(ClientBoundPacket):
    """Sent by the server to set the title text for the client. (Server -> Client).

    Initialize the SetTitleText packet.

    :param title_text: The title text to display.
    :type title_text: TextComponent
    """

    PACKET_ID: ClassVar[int] = 0x65
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    title_text: TextComponent

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.title_text.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        title_text = TextComponent.deserialize(buf)
        return cls(title_text=title_text)


@final
@define
class SetTitleAnimationTimes(ClientBoundPacket):
    """Sent by the server to set the animation times for the title for the client. (Server -> Client).

    Initialize the SetTitleAnimationTimes packet.

    :param fade_in: Ticks to spend fading in.
    :type fade_in: int
    :param stay: Ticks to keep the title displayed.
    :type stay: int
    :param fade_out: Ticks to spend fading out, not when to start fading out.
    :type fade_out: int
    """

    PACKET_ID: ClassVar[int] = 0x66
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    fade_in: int
    stay: int
    fade_out: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.INT, self.fade_in)
        buf.write_value(StructFormat.INT, self.stay)
        buf.write_value(StructFormat.INT, self.fade_out)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        fade_in = buf.read_value(StructFormat.INT)
        stay = buf.read_value(StructFormat.INT)
        fade_out = buf.read_value(StructFormat.INT)
        return cls(fade_in=fade_in, stay=stay, fade_out=fade_out)


class SoundCategories(IntEnum):
    """Sound category enumeration."""

    MASTER = 0
    MUSIC = 1
    RECORD = 2
    WEATHER = 3
    BLOCKS = 4
    HOSTILE = 5
    NEUTRAL = 6
    PLAYERS = 7
    AMBIENT = 8
    VOICE = 9


@final
@define
class EntitySoundEffect(ClientBoundPacket):
    """Plays a sound effect from an entity, either by hardcoded ID or Identifier. (Server -> Client).

    Initialize the EntitySoundEffect packet.

    :param sound_id: Represents the Sound ID + 1. If the value is 0, the packet contains a sound specified by
    Identifier.
    :type sound_id: int
    :param sound_name: Only present if Sound ID is 0.
    :type sound_name: Identifier, optional
    :param fixed_range: The fixed range of the sound. Only present if previous boolean is true and Sound ID is 0.
    :type fixed_range: float, optional
    :param sound_category: The category that this sound will be played from.
    :type sound_category: :class:`SoundCategories`
    :param entity_id: The ID of the entity that the sound will be played from.
    :type entity_id: int
    :param volume: 1.0 is 100%, capped between 0.0 and 1.0 by Notchian clients.
    :type volume: float
    :param pitch: Float between 0.5 and 2.0 by Notchian clients.
    :type pitch: float
    :param seed: Seed used to pick sound variant.
    :type seed: int
    """

    PACKET_ID: ClassVar[int] = 0x67
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    sound_id: int
    sound_name: Identifier | None
    fixed_range: float | None
    sound_category: SoundCategories
    entity_id: int
    volume: float
    pitch: float
    seed: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.sound_id)
        if self.sound_id == 0:
            self.sound_name = cast(Identifier, self.sound_name)
            self.sound_name.serialize_to(buf)
            buf.write_optional(self.fixed_range, lambda x: buf.write_value(StructFormat.FLOAT, x))

        buf.write_varint(self.sound_category.value)
        buf.write_varint(self.entity_id)
        buf.write_value(StructFormat.FLOAT, self.volume)
        buf.write_value(StructFormat.FLOAT, self.pitch)
        buf.write_value(StructFormat.LONG, self.seed)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        sound_id = buf.read_varint()
        sound_name = Identifier.deserialize(buf) if sound_id == 0 else None
        fixed_range = (
            buf.read_value(StructFormat.FLOAT) if sound_id == 0 and buf.read_value(StructFormat.BYTE) else None
        )
        sound_category = SoundCategories(buf.read_varint())
        entity_id = buf.read_varint()
        volume = buf.read_value(StructFormat.FLOAT)
        pitch = buf.read_value(StructFormat.FLOAT)
        seed = buf.read_value(StructFormat.LONG)
        return cls(
            sound_id=sound_id,
            sound_name=sound_name,
            fixed_range=fixed_range,
            sound_category=sound_category,
            entity_id=entity_id,
            volume=volume,
            pitch=pitch,
            seed=seed,
        )

    @override
    def validate(self) -> None:
        if self.fixed_range is not None and self.sound_id != 0:
            raise ValueError("Fixed range must be None if Sound ID is not 0.")


@final
@define
class SoundEffect(ClientBoundPacket):
    """Plays a sound effect at the given location, either by hardcoded ID or Identifier. (Server -> Client).

    Initialize the SoundEffect packet.

    :param sound_id: Represents the Sound ID + 1. If the value is 0, the packet contains a sound specified by
    Identifier.
    :type sound_id: int
    :param sound_name: Only present if Sound ID is 0.
    :type sound_name: Identifier, optional
    :param fixed_range: The fixed range of the sound. Only present if previous boolean is true and Sound ID is 0.
    :type fixed_range: float, optional
    :param sound_category: The category that this sound will be played from (current categories).
    :type sound_category: :class:`SoundCategories`
    :param position: The position of the sound effect. (Will be rounded down to 3 binary places)
    :type position: Vec3
    :param volume: 1.0 is 100%, capped between 0.0 and 1.0 by Notchian clients.
    :type volume: float
    :param pitch: Float between 0.5 and 2.0 by Notchian clients.
    :type pitch: float
    :param seed: Seed used to pick sound variant.
    :type seed: int
    """

    PACKET_ID: ClassVar[int] = 0x68
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    sound_id: int
    sound_name: Identifier | None
    fixed_range: float | None
    sound_category: SoundCategories
    position: Vec3
    volume: float
    pitch: float
    seed: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.sound_id)
        if self.sound_id == 0:
            self.sound_name = cast(Identifier, self.sound_name)
            self.sound_name.serialize_to(buf)
            buf.write_optional(self.fixed_range, lambda x: buf.write_value(StructFormat.FLOAT, x))
        buf.write_varint(self.sound_category)
        buf.write_value(StructFormat.INT, int(self.position.x * 8))
        buf.write_value(StructFormat.INT, int(self.position.y * 8))
        buf.write_value(StructFormat.INT, int(self.position.z * 8))
        buf.write_value(StructFormat.FLOAT, self.volume)
        buf.write_value(StructFormat.FLOAT, self.pitch)
        buf.write_value(StructFormat.LONG, self.seed)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        sound_id = buf.read_varint()
        sound_name = Identifier.deserialize(buf) if sound_id == 0 else None
        fixed_range = (
            buf.read_value(StructFormat.FLOAT) if sound_id == 0 and buf.read_value(StructFormat.BYTE) else None
        )
        sound_category = SoundCategories(buf.read_varint())
        position_x = buf.read_value(StructFormat.INT)
        position_y = buf.read_value(StructFormat.INT)
        position_z = buf.read_value(StructFormat.INT)

        position = Vec3(float(position_x) / 8, float(position_y) / 8, float(position_z) / 8)
        volume = buf.read_value(StructFormat.FLOAT)
        pitch = buf.read_value(StructFormat.FLOAT)
        seed = buf.read_value(StructFormat.LONG)
        return cls(
            sound_id=sound_id,
            sound_name=sound_name,
            fixed_range=fixed_range,
            sound_category=sound_category,
            position=position,
            volume=volume,
            pitch=pitch,
            seed=seed,
        )


@final
@define
class StartConfiguration(ClientBoundPacket):
    """Sent during gameplay in order to redo the configuration process. (Server -> Client).

    The client must respond with Acknowledge Configuration for the process to start.

    Initialize the StartConfiguration packet.
    """

    PACKET_ID: ClassVar[int] = 0x69
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
class StopSound(ClientBoundPacket):
    """Stop Sound (Server -> Client).

    Initialize the StopSound packet.


    :param source: Category to stop. If not present, then all sounds are stopped.
    :type source: :class:`SoundCategories`, optional
    :param sound: Sound to stop. If not present, then all sounds in the category are stopped.
    :type sound: :class:`mcproto.types.Identifier`, optional
    """

    PACKET_ID: ClassVar[int] = 0x6A
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    source: SoundCategories | None
    sound: Identifier | None

    @override
    def serialize_to(self, buf: Buffer) -> None:
        flags = (0x1 if self.source is not None else 0) | (0x2 if self.sound is not None else 0)
        buf.write_value(StructFormat.BYTE, flags)
        buf.write_optional(self.source, lambda x: buf.write_varint(x.value))
        buf.write_optional(self.sound, lambda x: x.serialize_to(buf))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        flags = buf.read_value(StructFormat.BYTE)
        source = SoundCategories(buf.read_varint()) if flags & 0x1 else None
        sound = Identifier.deserialize(buf) if flags & 0x2 else None
        return cls(source=source, sound=sound)


@final
@define
class StoreCookie(ClientBoundPacket):
    """Stores some arbitrary data on the client, which persists between server transfers. (Server -> Client).

    The Notchian client only accepts cookies of up to 5 kiB in size.

    Initialize the StoreCookie packet.

    :param key: The identifier of the cookie.
    :type key: Identifier
    :param payload: The data of the cookie.
    :type payload: bytes
    """

    PACKET_ID: ClassVar[int] = 0x6B
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    key: Identifier
    payload: bytes

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.key.serialize_to(buf)
        buf.write_varint(len(self.payload))
        buf.write(self.payload)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        key = Identifier.deserialize(buf)
        payload_length = buf.read_varint()
        payload = bytes(buf.read(payload_length))
        return cls(key=key, payload=payload)


@final
@define
class SystemChatMessage(ClientBoundPacket):
    """Sends the client a raw system message. (Server -> Client).

    Initialize the SystemChatMessage packet.

    :param content: The content of the message.
    :type content: TextComponent
    :param overlay: Whether the message is an actionbar or chat message. See also #Set Action Bar Text.
    :type overlay: bool
    """

    PACKET_ID: ClassVar[int] = 0x6C
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    content: TextComponent
    overlay: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.content.serialize_to(buf)
        buf.write_value(StructFormat.BYTE, int(self.overlay))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        content = TextComponent.deserialize(buf)
        overlay = bool(buf.read_value(StructFormat.BYTE))
        return cls(content=content, overlay=overlay)


@final
@define
class SetTabListHeaderAndFooter(ClientBoundPacket):
    """Display additional information above/below the player list. (Server -> Client).

    It is never sent by the Notchian server.

    Initialize the SetTabListHeaderAndFooter packet.

    :param header: To remove the header, send a empty text component: {"text":""}.
    :type header: TextComponent
    :param footer: To remove the footer, send a empty text component: {"text":""}.
    :type footer: TextComponent
    """

    PACKET_ID: ClassVar[int] = 0x6D
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    header: TextComponent
    footer: TextComponent

    @override
    def serialize_to(self, buf: Buffer) -> None:
        self.header.serialize_to(buf)
        self.footer.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        header = TextComponent.deserialize(buf)
        footer = TextComponent.deserialize(buf)
        return cls(header=header, footer=footer)


@final
@define
class TagQueryResponse(ClientBoundPacket):
    """Sent in response to Query Block Entity Tag or Query Entity Tag. (Server -> Client).

    Initialize the TagQueryResponse packet.

    :param transaction_id: Can be compared to the one sent in the original query packet.
    :type transaction_id: int
    :param nbt: The NBT of the block or entity. May be a TAG_END (0) in which case no NBT is present.
    :type nbt: NBT
    """

    PACKET_ID: ClassVar[int] = 0x6E
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    transaction_id: int
    nbt: NBTag

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.transaction_id)
        self.nbt.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        transaction_id = buf.read_varint()
        nbt = NBTag.deserialize(buf)
        return cls(transaction_id=transaction_id, nbt=nbt)


@final
@define
class PickupItem(ClientBoundPacket):
    """Sent by the server when someone picks up an item lying on the ground. (Server -> Client).

    Its sole purpose appears to be the animation of the item flying towards you. It doesn't destroy the entity in the
    client memory, and it doesn't add it to your inventory. The server only checks for items to be picked up after each
    Set Player Position (and Set Player Position And Rotation) packet sent by the client. The collector entity can be
    any entity; it does not have to be a player. The collected entity also can be any entity, but the Notchian server
    only uses this for items, experience orbs, and the different varieties of arrows.

    Initialize the PickupItem packet.

    :param collected_entity_id: The ID of the collected entity.
    :type collected_entity_id: int
    :param collector_entity_id: The ID of the collector entity.
    :type collector_entity_id: int
    :param pickup_item_count: The number of items in the stack.
    :type pickup_item_count: int
    """

    PACKET_ID: ClassVar[int] = 0x6F
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    collected_entity_id: int
    collector_entity_id: int
    pickup_item_count: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.collected_entity_id)
        buf.write_varint(self.collector_entity_id)
        buf.write_varint(self.pickup_item_count)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        collected_entity_id = buf.read_varint()
        collector_entity_id = buf.read_varint()
        pickup_item_count = buf.read_varint()
        return cls(
            collected_entity_id=collected_entity_id,
            collector_entity_id=collector_entity_id,
            pickup_item_count=pickup_item_count,
        )


@final
@define
class TeleportEntity(ClientBoundPacket):
    """Sent by the server when an entity moves more than 8 blocks. (Server -> Client).

    Initialize the TeleportEntity packet.

    :param entity_id: The ID of the entity.
    :type entity_id: int
    :param position: The new position of the entity.
    :type position: Vec3
    :param yaw: The new yaw angle.
    :type yaw: Angle
    :param pitch: The new pitch angle.
    :type pitch: Angle
    :param on_ground: Whether the entity is on the ground.
    :type on_ground: bool
    """

    PACKET_ID: ClassVar[int] = 0x70
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    position: Vec3
    yaw: Angle
    pitch: Angle
    on_ground: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        self.position.serialize_to_double(buf)
        self.yaw.serialize_to(buf)
        self.pitch.serialize_to(buf)
        buf.write_value(StructFormat.BYTE, int(self.on_ground))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        position = Vec3.deserialize_double(buf)
        yaw = Angle.deserialize(buf)
        pitch = Angle.deserialize(buf)
        on_ground = bool(buf.read_value(StructFormat.BYTE))
        return cls(entity_id=entity_id, position=position, yaw=yaw, pitch=pitch, on_ground=on_ground)


@final
@define
class SetTickingState(ClientBoundPacket):
    """Used to adjust the ticking rate of the client, and whether it's frozen. (Server -> Client).

    Initialize the SetTickingState packet.

    :param tick_rate: The tick rate.
    :type tick_rate: float
    :param is_frozen: Whether the client is frozen.
    :type is_frozen: bool
    """

    PACKET_ID: ClassVar[int] = 0x71
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    tick_rate: float
    is_frozen: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.FLOAT, self.tick_rate)
        buf.write_value(StructFormat.BYTE, int(self.is_frozen))

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        tick_rate = buf.read_value(StructFormat.FLOAT)
        is_frozen = bool(buf.read_value(StructFormat.BYTE))
        return cls(tick_rate=tick_rate, is_frozen=is_frozen)


@final
@define
class StepTick(ClientBoundPacket):
    """Advances the client processing by the specified number of ticks. (Server -> Client).

    This packet has no effect unless client ticking is frozen.

    Initialize the StepTick packet.

    :param tick_steps: The number of ticks to advance.
    :type tick_steps: int
    """

    PACKET_ID: ClassVar[int] = 0x72
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    tick_steps: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.tick_steps)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        tick_steps = buf.read_varint()
        return cls(tick_steps=tick_steps)


@final
@define
class Transfer(ClientBoundPacket):
    """Notifies the client that it should transfer to the given server.(Server -> Client).

    Cookies previously stored are preserved between server transfers.

    Initialize the Transfer packet.

    :param host: The hostname of IP of the server.
    :type host: str
    :param port: The port of the server.
    :type port: int
    """

    PACKET_ID: ClassVar[int] = 0x73
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    host: str
    port: int

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_utf(self.host)
        buf.write_varint(self.port)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        host = buf.read_utf()
        port = buf.read_varint()
        return cls(host=host, port=port)


@final
@define
class UpdateAdvancements(ClientBoundPacket):
    """Updates the client's advancements. (Server -> Client).

    Initialize the UpdateAdvancements packet.

    :param clear: Whether to clear the advancements.
    :type clear: bool
    :param udpate: The advancement mapping to update.
    :type advancements: dict[:class:`mcproto.types.Identifier`, :class:`mcproto.types.Advancement`]
    :param remove: The advancement identifiers to remove.
    :type remove: list[:class:`mcproto.types.Identifier`]
    :param progress: The advancement progress mapping to update.
    :type progress: dict[:class:`mcproto.types.Identifier`, :class:`mcproto.types.AdvancementProgress`]
    """

    PACKET_ID: ClassVar[int] = 0x74
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    clear: bool
    advancements: dict[Identifier, Advancement]
    remove: list[Identifier]
    progress: dict[Identifier, AdvancementProgress]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_value(StructFormat.BOOL, self.clear)
        buf.write_varint(len(self.advancements))
        for identifier, advancement in self.advancements.items():
            identifier.serialize_to(buf)
            advancement.serialize_to(buf)
        buf.write_varint(len(self.remove))
        for identifier in self.remove:
            identifier.serialize_to(buf)
        buf.write_varint(len(self.progress))
        for identifier, progress in self.progress.items():
            identifier.serialize_to(buf)
            progress.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        clear = bool(buf.read_value(StructFormat.BOOL))
        advancements: dict[Identifier, Advancement] = {}
        advancement_count = buf.read_varint()
        for _ in range(advancement_count):
            identifier = Identifier.deserialize(buf)
            advancement = Advancement.deserialize(buf)
            advancements[identifier] = advancement

        remove: list[Identifier] = [Identifier.deserialize(buf) for _ in range(buf.read_varint())]

        progress: dict[Identifier, AdvancementProgress] = {}
        progress_count = buf.read_varint()
        for _ in range(progress_count):
            identifier = Identifier.deserialize(buf)
            progress_ = AdvancementProgress.deserialize(buf)
            progress[identifier] = progress_

        return cls(clear=clear, advancements=advancements, remove=remove, progress=progress)


class ModifierAttributes(IntEnum):
    """Modifier attribute enumeration.

    `(min < default < max)`
    """

    ARMOR = 0
    "Armor (0.0 < 0.0 < 30.0)"
    ARMOR_TOUGHNESS = 1
    "Armor Toughness (0.0 < 0.0 < 20.0)"
    ATTACK_DAMAGE = 2
    "Attack Damage (2.0 < 0.0 < 2048.0)"
    ATTACK_KNOCKBACK = 3
    "Attack Knockback (0.0 < 0.0 < 5.0)"
    ATTACK_SPEED = 4
    "Attack Speed (4.0 < 0.0 < 1024.0)"
    BLOCK_BREAK_SPEED = 5
    "Block Break Speed (1.0 < 0.0 < 1024.0)"
    BLOCK_INTERACTION_RANGE = 6
    "Block Interaction Range (4.5 < 0.0 < 64.0)"
    ENTITY_INTERACTION_RANGE = 7
    "Entity Interaction Range (3.0 < 0.0 < 64.0)"
    FALL_DAMAGE_MULTIPLIER = 8
    "Fall Damage Multiplier (1.0 < 0.0 < 100.0)"
    FLYING_SPEED = 9
    "Flying Speed (0.4 < 0.0 < 1024.0)"
    FOLLOW_RANGE = 10
    "Follow Range (32.0 < 0.0 < 2048.0)"
    GRAVITY = 11
    "Gravity (0.08 < -1.0 < 1.0)"
    JUMP_STRENGTH = 12
    "Jump Strength (0.42 < 0.0 < 32.0)"
    KNOCKBACK_RESISTANCE = 13
    "Knockback Resistance (0.0 < 0.0 < 1.0)"
    LUCK = 14
    "Luck (0.0 < -1024.0 < 1024.0)"
    MAX_ABSORPTION = 15
    "Max Absorption (0.0 < 0.0 < 2048.0)"
    MAX_HEALTH = 16
    "Max Health (20.0 < 1.0 < 1024.0)"
    MOVEMENT_SPEED = 17
    "Movement Speed (0.7 < 0.0 < 1024.0)"
    SAFE_FALL_DISTANCE = 18
    "Safe Fall Distance (3.0 < -1024.0 < 1024.0)"
    SCALE = 19
    "Scale (1.0 < 0.0625 < 16.0)"
    ZOMBIE_SPAWN_REINFORCEMENTS = 20
    "Spawn Reinforcements Chance (0.0 < 0.0 < 1.0)"
    STEP_HEIGHT = 21
    "Step Height. (0.6 < 0.0 < 10.0)"


@final
@define
class UpdateAttributes(ClientBoundPacket):
    """Sets attributes on the given entity. (Server -> Client).

    Initialize the UpdateAttributes packet.

    :param entity_id: The ID of the entity.
    :type entity_id: :class:`ModifierAttributes`
    :param properties: A list of properties to set on the entity.
    :type properties: list[tuple[int, float]]
    :param modifiers: A list of modifiers to apply to the entity's attributes.
    :type modifiers: list[ModifierData]
    """

    PACKET_ID: ClassVar[int] = 0x75
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    properties: list[tuple[ModifierAttributes, float, list[ModifierData]]]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_varint(len(self.properties))
        for prop_id, value, modifiers in self.properties:
            buf.write_varint(prop_id)
            buf.write_value(StructFormat.DOUBLE, value)
            buf.write_varint(len(modifiers))
            for modifier in modifiers:
                modifier.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        num_properties = buf.read_varint()
        properties: list[tuple[ModifierAttributes, float, list[ModifierData]]] = []
        for _ in range(num_properties):
            prop_id = ModifierAttributes(buf.read_varint())
            value = buf.read_value(StructFormat.DOUBLE)
            modifiers = [ModifierData.deserialize(buf) for _ in range(buf.read_varint())]
            properties.append((prop_id, value, modifiers))
        return cls(entity_id=entity_id, properties=properties)


@final
@define
class EntityEffect(ClientBoundPacket):
    """Sets an effect on the given entity. (Server -> Client).

    Initialize the EntityEffect packet.

    :param entity_id: The ID of the entity.
    :type entity_id: int
    :param effect_id: The ID of the effect. See this table.
    :type effect_id: int
    :param amplifier: The amplifier of the effect. Notchian client displays effect level as Amplifier + 1.
    :type amplifier: int
    :param duration: The duration of the effect in ticks. (-1 for infinite)
    :type duration: int
    :param is_ambient: Whether the effect is ambient.
    :type is_ambient: bool
    :param show_particles: Whether to show particles.
    :type show_particles: bool
    :param show_icon: Whether to show the icon in the inventory.
    :type show_icon: bool
    :param blending: Should the hard-coded blending be used. (only for darkness effectS)
    :type blending: bool
    """

    PACKET_ID: ClassVar[int] = 0x76
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    effect_id: int
    amplifier: int
    duration: int
    is_ambient: bool
    show_particles: bool
    show_icon: bool
    blending: bool

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        buf.write_varint(self.effect_id)
        buf.write_varint(self.amplifier)
        buf.write_varint(self.duration)
        flags = (self.is_ambient << 0) | (self.show_particles << 1) | (self.show_icon << 2) | (self.blending << 3)
        buf.write_value(StructFormat.BYTE, flags)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        effect_id = buf.read_varint()
        amplifier = buf.read_varint()
        duration = buf.read_varint()
        flags = buf.read_value(StructFormat.BYTE)
        is_ambient = bool(flags & 0x1)
        show_particles = bool(flags & 0x2)
        show_icon = bool(flags & 0x4)
        blending = bool(flags & 0x8)
        return cls(
            entity_id=entity_id,
            effect_id=effect_id,
            amplifier=amplifier,
            duration=duration,
            is_ambient=is_ambient,
            show_particles=show_particles,
            show_icon=show_icon,
            blending=blending,
        )


@final
@define
class UpdateRecipes(ClientBoundPacket):
    """Updates the client's recipe book with the given recipes. (Server -> Client).

    Initialize the UpdateRecipes packet.

    :param recipes: A list of recipes to update.
    :type recipes: list[:class:`mcproto.types.Recipe`]
    """

    PACKET_ID: ClassVar[int] = 0x77
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    recipes: list[Recipe]

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(len(self.recipes))
        for recipe in self.recipes:
            recipe.serialize_to(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        recipes = [Recipe.deserialize(buf) for _ in range(buf.read_varint())]
        return cls(recipes=recipes)


@final
@define
class UpdateTags(ClientBoundPacket):
    """Update Tags (configuration) (Server -> Client).

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

    PACKET_ID: ClassVar[int] = 0x78
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

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
class ProjectilePower(ClientBoundPacket):
    """Sets the power of a projectile. (Server -> Client).

    Initialize the ProjectilePower packet.

    :param entity_id: The ID of the projectile entity.
    :type entity_id: int
    :param power: The power of the projectile.
    :type power: Vec3
    """

    PACKET_ID: ClassVar[int] = 0x79
    GAME_STATE: ClassVar[GameState] = GameState.PLAY

    entity_id: int
    power: Vec3

    @override
    def serialize_to(self, buf: Buffer) -> None:
        buf.write_varint(self.entity_id)
        self.power.serialize_to_double(buf)

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        entity_id = buf.read_varint()
        power = Vec3.deserialize_double(buf)
        return cls(entity_id=entity_id, power=power)
