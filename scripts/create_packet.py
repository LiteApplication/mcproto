from __future__ import annotations
from typing import TypeVar, TypedDict
from typing_extensions import override

from mcproto.packets import GameState, PacketDirection
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.document import Document

from enum import Enum
import contextlib

try:
    import pyperclip  # pip install pyperclip
except ImportError:
    pyperclip = None


class VariableType(Enum):
    """Types of variables that can be used in a packet."""

    BOOLEAN = "boolean"
    BYTE = "byte"
    SHORT = "short"
    UNSIGNED_SHORT = "unsigned_short"
    INT = "int"
    LONG = "long"
    FLOAT = "float"
    DOUBLE = "double"
    STRING = "string"
    VARINT = "varint"
    BYTEARRAY = "bytearray"
    BYTEARRAY_REMAINING = "bytearray_remaining"

    ANGLE = "angle"
    POSITION = "position"
    VEC3F = "vec3"
    TEXTCOMPONENT = "text"
    JSONTEXTCOMPONENT = "jsontext"
    NBT = "nbt"
    NBT_COMPOUND = "compound"
    BITSET = "bitset"
    FIXED_BITSET = "fixedbitset"
    IDENTIFIER = "identifier"
    QUATERNION = "quaternion"
    UUID = "uuid"


CLASS_PARENT = {PacketDirection.SERVERBOUND: "ServerBoundPacket", PacketDirection.CLIENTBOUND: "ClientBoundPacket"}

DIRECTION_STRING = {PacketDirection.SERVERBOUND: "Server -> Client", PacketDirection.CLIENTBOUND: "Client -> Server"}

GAMESTATE_ENUM = {state: GameState.__name__ + "." + state.name for state in GameState}

BUFFER_READ_TYPES = {
    VariableType.VARINT: "buf.read_varint()",
    VariableType.STRING: "buf.read_utf()",
    VariableType.DOUBLE: "buf.read_value(StructFormat.DOUBLE)",
    VariableType.BOOLEAN: "bool(buf.read_value(StructFormat.BYTE))",
    VariableType.BYTE: "buf.read_value(StructFormat.BYTE)",
    VariableType.SHORT: "buf.read_value(StructFormat.SHORT)",
    VariableType.UNSIGNED_SHORT: "buf.read_value(StructFormat.UNSIGNED_SHORT)",
    VariableType.INT: "buf.read_value(StructFormat.INT)",
    VariableType.LONG: "buf.read_value(StructFormat.LONGLONG)",
    VariableType.FLOAT: "buf.read_value(StructFormat.FLOAT)",
    VariableType.BYTEARRAY: "buf.read_bytearray()",
    VariableType.BYTEARRAY_REMAINING: "bytes(buf.read(buf.remaining))",
}

DESERIALIZE_OPTIONAL = "buf.read_optional(lambda: {deserialize})"
DESERIALIZE_CLASS = "{cls}.deserialize(buf)"

ASSIGN_VARIABLE = "{variable_name} = {deserialize}"

BUFFER_WRITE_TYPES = {
    VariableType.VARINT: "buf.write_varint({name})",
    VariableType.STRING: "buf.write_utf({name})",
    VariableType.DOUBLE: "buf.write_value(StructFormat.DOUBLE, {name})",
    VariableType.BOOLEAN: "buf.write_value(StructFormat.BYTE, int({name}))",
    VariableType.BYTE: "buf.write_value(StructFormat.BYTE, {name})",
    VariableType.SHORT: "buf.write_value(StructFormat.SHORT, {name})",
    VariableType.UNSIGNED_SHORT: "buf.write_value(StructFormat.UNSIGNED_SHORT, {name})",
    VariableType.INT: "buf.write_value(StructFormat.INT, {name})",
    VariableType.LONG: "buf.write_value(StructFormat.LONGLONG, {name})",
    VariableType.FLOAT: "buf.write_value(StructFormat.FLOAT, {name})",
    VariableType.BYTEARRAY: "buf.write_bytearray({name})",
    VariableType.BYTEARRAY_REMAINING: "buf.write({name})",
}
WRITE_OPTIONAL = "buf.write_optional({name}, lambda x: {serialize})"
SERIALIZE_CLASS = "{name}.serialize_to(buf)"

TYPES_WITH_CLASS = {  # Used with deserialize and serialize and as type hints
    VariableType.ANGLE: "Angle",
    VariableType.POSITION: "Position",
    VariableType.VEC3F: "Vec3",
    VariableType.TEXTCOMPONENT: "TextComponent",
    VariableType.JSONTEXTCOMPONENT: "JSONTextComponent",
    VariableType.NBT: "NBTag",
    VariableType.NBT_COMPOUND: "CompoundNBT",
    VariableType.BITSET: "Bitset",
    VariableType.FIXED_BITSET: "FixedBitset",
    VariableType.IDENTIFIER: "Identifier",
    VariableType.QUATERNION: "Quaternion",
    VariableType.UUID: "UUID",
}

PRINTED_TYPES = {
    VariableType.VARINT: "int",
    VariableType.STRING: "str",
    VariableType.DOUBLE: "float",
    VariableType.ANGLE: "float",
    VariableType.POSITION: "tuple[int, int, int]",
    VariableType.BOOLEAN: "bool",
    VariableType.BYTE: "int",
    VariableType.SHORT: "int",
    VariableType.UNSIGNED_SHORT: "int",
    VariableType.INT: "int",
    VariableType.LONG: "int",
    VariableType.FLOAT: "float",
    VariableType.BYTEARRAY: "bytes",
    VariableType.BYTEARRAY_REMAINING: "bytes",
}

CLASS_DEFINITION = '''
@final
@define
class {class_name}({parent_class}):
    """{short_description} ({direction_string}).

    {longer_description}

    Initialize the {packet_name} packet.

    {description_variables}
    """

    PACKET_ID: ClassVar[int] = {packet_id}
    GAME_STATE: ClassVar[GameState] = {game_state_enum}

    {fields}

    @override
    def serialize_to(self, buf: Buffer) -> None:
        {serialize_variables}

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        {deserialize_variables}
        return cls({variables})
'''

FIELD_VARIABLE = "{variable_name}: {variable_type}"
FIELD_VARIABLE_OPTIONAL = "{variable_name}: {variable_type} | None"
DESCRIPTION_VARIABLE = ":param {variable_name}: {description}\n:type {variable_name}: {printed_type}"


def indent(text: str | list[str], level: int = 1) -> str:
    """Indent a block of text by a given level, skipping the first line."""
    if isinstance(text, list):
        text = "\n".join(text)
    return ("\n" + " " * 4 * level).join(line.lstrip(" ") for line in text.split("\n"))


class Variable:
    """A variable that can be used in a packet."""

    def __init__(self, description: str, vtype: VariableType, optional: bool = False):
        self.description = description
        self.type = vtype
        self.optional = optional


class Packet(TypedDict):
    """Represents a packet description that can be used to generate a packet class."""

    name: str
    packet_id: int
    game_state: GameState
    direction: PacketDirection
    description: str
    variables: dict[str, Variable]


def generate_class(
    name: str,
    packet_id: int,
    game_state: GameState,
    direction: PacketDirection,
    description: str,
    variables: dict[str, Variable],
) -> str:
    """Generate a packet class from the given parameters."""
    name = "".join(word.strip().capitalize() for word in name.split())

    short_description = description.split("\n")[0]
    longer_description = indent(description.split("\n")[1:], 1)

    game_state_string = GAMESTATE_ENUM[game_state]
    direction_string = DIRECTION_STRING[direction]

    fields: list[str] = []
    serialize_variables: list[str] = []
    deserialize_variables: list[str] = []
    deserialize_assignments: list[str] = []
    description_variables: list[str] = []

    for variable_name, variable in variables.items():
        with_class = variable.type in TYPES_WITH_CLASS
        if with_class:
            variable_type = TYPES_WITH_CLASS[variable.type]
        else:
            variable_type = PRINTED_TYPES[variable.type]

        # Field list
        fields.append(
            (FIELD_VARIABLE_OPTIONAL if variable.optional else FIELD_VARIABLE).format(
                variable_name=variable_name,
                variable_type=variable_type,
            )
        )

        # Serialize
        if with_class:
            base = SERIALIZE_CLASS
        else:
            base = BUFFER_WRITE_TYPES[variable.type]
        self_var = "self." + variable_name
        if variable.optional:
            serialize_variables.append(WRITE_OPTIONAL.format(serialize=base.format(name="x"), name=self_var))
        else:
            serialize_variables.append(base.format(name=self_var))

        # Deserialize
        if with_class:
            base = DESERIALIZE_CLASS.format(cls=TYPES_WITH_CLASS[variable.type])
        else:
            base = BUFFER_READ_TYPES[variable.type]
        if variable.optional:
            base = DESERIALIZE_OPTIONAL.format(deserialize=base)
        deserialize_variables.append(
            ASSIGN_VARIABLE.format(
                variable_name=variable_name,
                deserialize=base,
            )
        )
        deserialize_assignments.append(ASSIGN_VARIABLE.format(variable_name=variable_name, deserialize=variable_name))

        # Description
        if variable.optional:
            variable_type = variable_type + ", optional"

        description_variables.append(
            DESCRIPTION_VARIABLE.format(
                variable_name=variable_name,
                description=variable.description,
                printed_type=variable_type,
            )
        )

    return CLASS_DEFINITION.format(
        class_name=name,
        parent_class=CLASS_PARENT[direction],
        short_description=short_description,
        longer_description=indent(longer_description),
        packet_name=name,
        packet_id=hex(packet_id),
        game_state_enum=game_state_string,
        direction_string=direction_string,
        fields=indent(fields, 1),
        serialize_variables=indent(serialize_variables, 2),
        deserialize_variables=indent(deserialize_variables, 2),
        variables=", ".join(deserialize_assignments),
        description_variables=indent(description_variables),
    )


# Prompt function using prompt_toolkit
def prompt_packet() -> Packet:
    """Prompt the user to create a new packet."""
    T = TypeVar("T", bound=Enum)

    def prompt_enum(prompt_text: str, enum_class: type[T]) -> T:
        completer = WordCompleter([e.name for e in enum_class], ignore_case=True)
        return enum_class[prompt(prompt_text, completer=completer, validator=None).upper()]

    class HexValidator(Validator):
        @override
        def validate(self, document: Document) -> None:
            try:
                int(document.text, 16)
            except ValueError as e:
                raise ValidationError(
                    message="Please enter a valid hexadecimal number.", cursor_position=len(document.text)
                ) from e

    name = prompt("Enter the packet name: ")
    name = "".join(word.capitalize() for word in name.split())
    packet_id = int(
        prompt(
            "Enter the packet ID (in hexadecimal, e.g., 0A): ",
            validator=HexValidator(),
            validate_while_typing=True,
        ),
        16,
    )
    game_state = prompt_enum("Enter the game state: ", GameState)
    direction = prompt_enum("Enter the packet direction: ", PacketDirection)
    description = prompt("Enter the packet description: ")

    variables: dict[str, Variable] = {}
    while True:
        var_name = prompt("Enter the variable name (or press Enter to finish): ")
        if not var_name:
            break
        var_description = prompt(f"Enter description for variable '{var_name}': ")
        var_type = prompt_enum(f"Enter the type for variable '{var_name}': ", VariableType)
        optional = prompt(f"Is the variable '{var_name}' optional? (yes/no): ").strip().lower() in ["yes", "y"]

        variables[var_name] = Variable(description=var_description, vtype=var_type, optional=optional)

    return Packet(
        name=name,
        packet_id=packet_id,
        game_state=game_state,
        direction=direction,
        description=description,
        variables=variables,
    )


if __name__ == "__main__":
    packets = [
        Packet(
            name="Acknowledge Finish Configuration",
            packet_id=0x02,
            game_state=GameState.CONFIGURATION,
            direction=PacketDirection.CLIENTBOUND,
            description="Sent by the client to acknowledge the configuration process is finished.",
            variables={},
        ),
        Packet(
            name="Serverbound Keep Alive",
            packet_id=0x03,
            game_state=GameState.CONFIGURATION,
            direction=PacketDirection.SERVERBOUND,
            description="Response to server's keep-alive packet with the same ID.",
            variables={
                "keep_alive_id": Variable("Keep-alive ID received from the server.", VariableType.LONG),
            },
        ),
        Packet(
            name="Pong",
            packet_id=0x04,
            game_state=GameState.CONFIGURATION,
            direction=PacketDirection.CLIENTBOUND,
            description="Response to the server's ping packet with the same ID.",
            variables={
                "id": Variable("ID from the ping packet (echoed back).", VariableType.INT),
            },
        ),
        Packet(
            name="Resource Pack Response",
            packet_id=0x05,
            game_state=GameState.CONFIGURATION,
            direction=PacketDirection.CLIENTBOUND,
            description="Server's response to the client's resource pack request.",
            variables={
                "uuid": Variable("UUID of the received resource pack.", VariableType.UUID, optional=True),
                "result": Variable("Result of the resource pack request.", VariableType.VARINT),
            },
        ),
    ]

    class_str = "\n\n".join(generate_class(**packet) for packet in packets)
    # Copy the generated class to the clipboard
    with contextlib.suppress(AttributeError):
        pyperclip.copy(class_str)  # type: ignore

    print(class_str)  # noqa: T201
