from __future__ import annotations

import importlib
import inspect
import json
import sys
from difflib import get_close_matches
from enum import Enum
from pathlib import Path
from typing import Literal, Sequence, Union, cast, overload

from typing_extensions import TypeAlias

from mcproto.packets import GameState, Packet
from mcproto.packets.packet import ClientBoundPacket, ServerBoundPacket
from scripts.entity_generator import format_ruff

# We want to ignore certain packet names when renaming/reporting them because Mojang's names are not explicit enough
IGNORE_OUR_NAMES = {
    "Handshake",  # Handshake is clearer
    "LoginEncryptionResponse",  # That's just not explicit enough
    "LoginEncryptionRequest",  # Same packet name used in 2 different things
    "LoginStart",
    "PingPong",  # Used by both the client and the server
}

IGNORE_MOJANG_NAMES = {
    "Intention",  # Handshake is clearer
    "Key",  # That's just not explicit enough
    "Hello",  # Same packet name used in 2 different things
    "PongResponse",  # Used by both the client and the server
    "PingRequest",
}

GAME_STATES = [
    GameState.CONFIGURATION,
    GameState.HANDSHAKE,
    GameState.LOGIN,
    GameState.PLAY,
    GameState.STATUS,
]

PACKETS_MODULES = {
    GameState.CONFIGURATION: [
        "mcproto.packets.configuration.clientbound",
        "mcproto.packets.configuration.serverbound",
    ],
    GameState.HANDSHAKE: ["mcproto.packets.handshaking.handshake"],
    GameState.LOGIN: ["mcproto.packets.login.login"],
    GameState.PLAY: ["mcproto.packets.play.clientbound", "mcproto.packets.play.serverbound"],
    GameState.STATUS: ["mcproto.packets.status.status", "mcproto.packets.status.ping"],
}

INIT_FILES = {
    GameState.CONFIGURATION: "mcproto/packets/configuration/__init__.py",
    GameState.HANDSHAKE: "mcproto/packets/handshaking/__init__.py",
    GameState.LOGIN: "mcproto/packets/login/__init__.py",
    GameState.PLAY: "mcproto/packets/play/__init__.py",
    GameState.STATUS: "mcproto/packets/status/__init__.py",
}

PACKET_TEMPLATE_INSERT = '''@final
@define
class {packet_name}({boundness}Packet): # TODO: IMPLEMENT THE PACKET
    """

    Initialize the {packet_name} packet.


    """
    PACKET_ID: ClassVar[int] = {packet_id}
    GAME_STATE: ClassVar[GameState] = GameState.{game_state}

    @override
    def serialize_to(self, buf: Buffer) -> None:
        raise NotImplementedError("This method is not implemented yet.")

    @override
    @classmethod
    def _deserialize(cls, buf: Buffer, /) -> Self:
        raise NotImplementedError("This method is not implemented yet.")
'''

REPLACE_PACKET_ID_TEMPLATE = "    PACKET_ID: ClassVar[int] = {packet_id}\n"


Exportable: TypeAlias = Union[type[Packet], type[Enum]]


_verbose = False


ANSI_COLORS = {
    "red": "\033[91m",
    "blue": "\033[94m",
    "gray": "\033[90m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "reset": "\033[0m",
}


def verbose_print(*args, **kwargs) -> None:
    """Print the given arguments if the verbose flag is set."""
    if _verbose:
        print(*args, **kwargs)  # noqa: T201


def report_error(message: str, game_state: GameState, boundness: Literal["clientbound", "serverbound", None]) -> None:
    """Print the given message as an error.

    If message contains a backtick (`), it will be replaced with a yellow color.
    """
    while "`" in message:
        message = message.replace("`", ANSI_COLORS["yellow"], 1).replace("`", ANSI_COLORS["reset"], 1)
    message += ANSI_COLORS["reset"]

    if boundness is None:
        before = f"[{ANSI_COLORS['blue']}{game_state.name}{ANSI_COLORS['reset']}]"
    else:
        before = (
            f"[{ANSI_COLORS['blue']}{game_state.name}{ANSI_COLORS['reset']} → {ANSI_COLORS['gray']}"
            f"{boundness[:6]}{ANSI_COLORS['reset']}]"
        )
    print(before, message)  # noqa: T201


@overload
def list_imports_module(
    name: str | list[str], packets_only: Literal[True] = True, keep: Literal[None] = None
) -> list[type[Packet]]: ...
@overload
def list_imports_module(
    name: str | list[str], packets_only: Literal[True] = True, keep: Literal["serverbound"] = "serverbound"
) -> list[type[ServerBoundPacket]]: ...
@overload
def list_imports_module(
    name: str | list[str], packets_only: Literal[True] = True, keep: Literal["clientbound"] = "clientbound"
) -> list[type[ClientBoundPacket]]: ...


@overload
def list_imports_module(
    name: str | list[str], packets_only: Literal[False] = False, keep: Literal[None] = None
) -> list[Exportable]: ...


def list_imports_module(
    name: str | list[str], packets_only: bool = False, keep: Literal[None, "serverbound", "clientbound"] = None
) -> Sequence[Exportable] | Sequence[type[Packet]]:
    """List all packets/enums in the given module."""
    if isinstance(name, list):
        ret: Sequence[Exportable] = []
        for module in name:
            ret.extend(  # Pyright is freaking out here because of the overloads, but I like the info they provide
                list_imports_module(  # pyright: ignore[reportCallIssue]
                    name=module,
                    packets_only=packets_only,  # pyright: ignore[reportArgumentType]
                    keep=keep,  # pyright: ignore[reportArgumentType]
                )
            )
        return ret
    module = importlib.import_module(name)
    packets: Sequence[Exportable] = []
    for packet_name in dir(module):
        if packet_name.startswith("__"):
            continue
        if packet_name in ("Packet", "ClientBoundPacket", "ServerBoundPacket", "GameState", "IntEnum", "StructFormat"):
            continue
        packet = getattr(module, packet_name)
        if not isinstance(packet, type):
            continue

        # Check if the packet is declared in this module
        if not issubclass(packet, Packet if packets_only else (Packet, Enum)):
            continue

        if inspect.getmodule(packet) != module:
            verbose_print(f"{module.__name__} : Skipping {packet.__name__} as it is imported from another module.")
            continue

        packets.append(packet)

    if keep is not None and packets_only:
        packets = cast("list[type[Packet]]", packets)
        return filter_bound(packets, keep)

    return packets


def filter_bound(
    packets: Sequence[type[Packet]], boundness: Literal["serverbound", "clientbound"]
) -> list[type[Packet]]:
    """Filter the packets to only include certain packets."""
    if boundness == "clientbound":
        return [packet for packet in packets if issubclass(packet, ClientBoundPacket)]
    if boundness == "serverbound":
        return [packet for packet in packets if issubclass(packet, ServerBoundPacket)]
    return []


def generate_init(game_state: GameState) -> None:
    """Generate the __init__.py file for the given game state using the packets defined in the packets modules."""
    packets: dict[str, list[Exportable]] = {}
    for module in PACKETS_MODULES[game_state]:
        packets[module] = list_imports_module(module, packets_only=False)
    init_file = Path(INIT_FILES[game_state])

    # Get the packets that are duplicated in a single game state (e.g. clientbound and serverbound packets in PLAY)
    duplicates: set[str] = set()
    packet_name: list[set[str]] = [{packet.__name__ for packet in packets[module]} for module in packets]

    for i, packet_set in enumerate(packet_name):
        for j in range(i + 1, len(packet_name)):
            duplicates.update(packet_set.intersection(packet_name[j]))

    all_packets: set[str] = set()
    with init_file.open("w") as f:
        f.write("from __future__ import annotations\n\n")
        for module in sorted(packets):
            f.write(f"from {module} import (\n")
            for packet in packets[module]:
                name = packet.__name__
                if packet.__name__ in duplicates:
                    # Change duplicate packet names to avoid conflicts if they are * imported
                    if packet.__module__.endswith("serverbound"):
                        all_packets.add("Serverbound" + name)
                        name = f"{name} as Serverbound{name}"
                    elif packet.__module__.endswith("clientbound"):
                        all_packets.add("Clientbound" + name)
                        name = f"{name} as Clientbound{name}"
                else:
                    all_packets.add(name)
                f.write(f"    {name},\n")
            f.write(")\n\n")
        f.write("\n__all__ = [\n")
        for packet in sorted(all_packets):
            f.write(f'    "{packet}",\n')
        f.write("]\n")

    format_ruff(init_file, silent=not _verbose)


def check_continuity(
    packets: Sequence[type[Packet]],
    game_state: GameState,
    boundness: Literal["clientbound", "serverbound"],
) -> bool:
    """Check if the packet ids are continuous and there are no duplicates.

    Return True if the packets are continuous.
    """
    packets = list(packets)
    packets.sort(key=lambda packet: packet.PACKET_ID)
    previous_packet: type[Packet] | None = None
    error = False
    for packet in packets:
        if previous_packet is not None and previous_packet.PACKET_ID == packet.PACKET_ID:
            report_error(
                f"Found a duplicate packet id: `{previous_packet.__name__}` and `{packet.__name__}`"
                f" ({hex(packet.PACKET_ID)})",
                game_state,
                boundness,
            )
            error = True
        elif previous_packet is not None and previous_packet.PACKET_ID + 1 != packet.PACKET_ID:
            report_error(
                f"{previous_packet.__name__} ({hex(previous_packet.PACKET_ID)})"
                f"-> {packet.__name__} ({hex(packet.PACKET_ID)})",
                game_state,
                boundness,
            )
            error = True
        previous_packet = packet
    return not error


def check_redaction_order(
    packets: Sequence[type[Packet]],
    game_state: GameState,
    boundness: Literal["clientbound", "serverbound"],
) -> bool:
    """Check if the packets are written in the correct order in the modules.

    In order for the insertion of a new packet to be easier, the packets should be written in the correct order in the
    modules.

    Returns True if the packets with a smaller packet id are written before the packets with a bigger packet id (when
    they are in the same file).
    """
    packets = list(packets)
    packets.sort(key=lambda packet: packet.PACKET_ID)
    previous_packet: type[Packet] | None = None
    previous_line = -1
    previous_file = ""
    error = False
    for packet in packets:
        file = inspect.getfile(packet)
        line = inspect.getsourcelines(packet)[1]
        if previous_packet is not None and previous_file == file and previous_line > line:
            report_error(
                f"`{previous_packet.__name__}` ({hex(previous_packet.PACKET_ID)}) "
                f"is defined after `{packet.__name__}` ({hex(packet.PACKET_ID)}).",
                game_state,
                boundness,
            )
            error = True
        previous_packet = packet
        previous_line = line
        previous_file = file
    return not error


def check_game_state(packets: Sequence[type[Packet]], game_state: GameState) -> bool:
    """Check the packets of the given game state. Return True if the packets are correct."""
    error = False
    for packet in packets:
        if game_state != packet.GAME_STATE:
            report_error(f"{packet.__name__} has the wrong game state ({packet.GAME_STATE.name})", game_state, None)
            error = True
    return not error


def check_boundness_docstring(packets: Sequence[type[Packet]], game_state: GameState) -> bool:
    """Check if the first line of the docstring is indicating which part the packet belongs to.

    Return True if the packets are correct.
    """
    error = False
    for packet in packets:
        docstring = packet.__doc__
        if docstring is None:
            report_error(f"{packet.__name__} is missing a docstring.", game_state, None)
            error = True
            continue
        first_line = docstring.split("\n")[0]
        if issubclass(packet, ServerBoundPacket) and issubclass(packet, ClientBoundPacket):
            if "Client <-> Server" not in first_line:
                report_error(
                    f"{packet.__name__} is missing the 'Client <-> Server' in the docstring.", game_state, None
                )
                error = True
        elif issubclass(packet, ServerBoundPacket):
            if "Client -> Server" not in first_line:
                if "Server -> Client" in first_line:
                    report_error(f"{packet.__name__} has the wrong boundness in the docstring.", game_state, None)
                    error = True
                else:
                    report_error(
                        f"{packet.__name__} is missing the 'Client -> Server' in the docstring.", game_state, None
                    )
                    error = True
        elif issubclass(packet, ClientBoundPacket):
            if "Server -> Client" not in first_line:
                if "Client -> Server" in first_line:
                    report_error(f"{packet.__name__} has the wrong boundness in the docstring.", game_state, None)
                    error = True
                else:
                    report_error(
                        f"{packet.__name__} is missing the 'Server -> Client' in the docstring.", game_state, None
                    )
                    error = True
    return not error


def packet_name_to_class_name(packet_name: str) -> str:
    """Convert the packet name to a class name."""
    return packet_name.replace("minecraft:", "", 1).replace("_", " ").title().replace(" ", "")


def compare_with_packet_definition(
    packets: Sequence[type[Packet]],
    game_state: GameState,
    boundness: Literal["clientbound", "serverbound"],
    packets_file: str,
    replace_names: bool = False,
    auto_insert: bool = False,
    auto_change_packet_id: bool = False,
) -> None:
    """Compare the packets with the packet definition extracted from the packets file.

    This function will check if the packets defined in the modules match the ones defined in the packets file extracted
    from the `server.jar` file.

    .. note:: `java -DbundlerMainClass=net.minecraft.data.Main -jar server.jar --reports`
    """
    with Path(packets_file).open("r") as f:
        packets_data = json.load(f)[game_state.name.lower()].get(boundness, {})

    # m_ : From Mojang, o_ : From our packets
    m_id_packets = {packets_data[packet]["protocol_id"]: packet for packet in packets_data}
    m_id_packets_new_name = {
        p_id: packet_name_to_class_name(packet_name) for p_id, packet_name in m_id_packets.items()
    }

    o_id_packets = {packet.PACKET_ID: packet.__name__ for packet in packets}

    # Try to find any packet that has the wrong name
    expected_names = set(m_id_packets_new_name.values()).union(IGNORE_OUR_NAMES)
    for packet in packets:
        if packet.__name__ not in expected_names:
            closest = get_close_matches(packet.__name__, expected_names)
            by_id = m_id_packets_new_name.get(packet.PACKET_ID, None)
            message = f"`{packet.__name__}` is not in the modules"
            if by_id is not None:  # The packet is not in the packets file, but it is mentioned in the JSON file
                message += f", but mentioned in the JSON file as `{by_id}`"
            if closest:  # Find the closest match (by name)
                message += f". Did you mean `{'` or `'.join(closest)}`?"
            report_error(message, game_state, boundness)
            if by_id is not None:
                expected_names.remove(by_id)
                if replace_names:
                    replace_occurrences(packet.__name__, by_id)

        else:
            expected_names.remove(packet.__name__)

    # Check if there are any packets that are not defined in the packets modules
    for packet_id, packet_name in m_id_packets_new_name.items():
        if packet_id not in o_id_packets:  # No packet with this ID
            if packet_name in set(o_id_packets.values()):  # Found one with the same name
                found_id = next(id_ for id_, name in o_id_packets.items() if name == packet_name)
                if auto_change_packet_id:
                    verbose_print(f"Automatically changing the packet id of {packet_name} to {hex(packet_id)}")
                    packet = next(packet for packet in packets if packet.__name__ == packet_name)
                    edit_packet_id(packet, packet_id)
                else:
                    report_error(
                        f"`{packet_name}` has the wrong packet ID (should be"
                        f" `{hex(packet_id)}`, found `{hex(found_id)}`).",
                        game_state,
                        boundness,
                    )
            elif auto_insert:  # Let's insert it
                verbose_print(f"Automatically inserting the packet {packet_name} ({hex(packet_id)})")
                insert_packet(game_state, boundness, packet_name, packet_id)
            else:  # Cowardly refuse to insert it
                report_error(
                    f"`{packet_name}` ({hex(packet_id)}) is not defined in the packets modules.",
                    game_state,
                    boundness,
                )
        elif packet_name != o_id_packets[packet_id]:  # Check if the name is correct
            if packet_name in IGNORE_MOJANG_NAMES or o_id_packets[packet_id] in IGNORE_OUR_NAMES:
                continue
            if auto_change_packet_id:
                verbose_print(f"Automatically changing the packet id of {packet_name} to {hex(packet_id)}")
                packet = next(packet for packet in packets if packet.__name__ == packet_name)
                edit_packet_id(packet, packet_id)
            else:
                report_error(
                    f"`{packet_name}` has the wrong packet ID (should be"
                    f" `{hex(packet_id)}`, found `{hex(packet_id)}`).",
                    game_state,
                    boundness,
                )


def replace_occurrences(old: str, new: str) -> None:
    """Report the occurrences of the old string, and ask if it should be replaced with the new string."""
    # Find all the files where the old string is present
    files = list(Path().rglob("*.py"))
    for file in files:
        with file.open("r") as f:
            for i, line in enumerate(f):
                if old in line:
                    print(f"{file.relative_to(Path())}:{i+1} : {line.rstrip()}")  # noqa: T201
    # Ask if the user wants to replace the old string with the new string
    if input(f"Replace all occurrences of '{old}' with '{new}'? (y/n) ").lower() == "y":
        for file in files:
            with file.open("r") as f:
                lines = f.readlines()
            with file.open("w") as f:
                for line in lines:
                    f.write(line.replace(old, new))


def edit_packet_id(packet: type[Packet], new_id: int) -> None:
    """Edit the packet id of the given packet."""
    file = inspect.getfile(packet)
    first_line = inspect.getsourcelines(packet)[1]
    line_search = REPLACE_PACKET_ID_TEMPLATE.format(packet_id="").strip()  # The template contains a new line
    with Path(file).open("r") as f:
        file_content = f.readlines()

    for i, line in enumerate(file_content):
        if i >= first_line and line_search in line:
            break
    else:
        report_error(f"Could not find the packet id for {packet.__name__}.", packet.GAME_STATE, None)
        return

    file_content[i] = REPLACE_PACKET_ID_TEMPLATE.format(packet_id=hex(new_id))
    verbose_print(f"Changing the packet id of {packet.__name__} to {hex(new_id)}")

    with Path(file).open("w") as f:
        f.writelines(file_content)


def insert_packet(
    game_state: GameState,
    boundness: Literal["clientbound", "serverbound"],
    packet_name: str,
    packet_id: int,
) -> None:
    """Insert a new packet in the packets modules. This function assumes that the redaction order is correct."""
    o_id_packets = {
        packet.PACKET_ID: packet
        for packet in list_imports_module(
            PACKETS_MODULES[game_state],
            packets_only=True,
            keep=boundness,
        )
    }

    if packet_name in [packet.__name__ for packet in o_id_packets.values()]:
        report_error(f"The packet `{packet_name}` is already defined.", game_state, boundness)
        return

    if packet_id in o_id_packets:
        file = inspect.getfile(o_id_packets[packet_id])
        line_number = inspect.getsourcelines(o_id_packets[packet_id])[1]
        verbose_print(f"Replacing and shifting the packet {packet_name} ({hex(packet_id)})")
    elif any(packet_id < id_ for id_ in o_id_packets):
        next_packet_id = min(id_ for id_ in o_id_packets if id_ > packet_id)
        file = inspect.getfile(o_id_packets[next_packet_id])
        line_number = inspect.getsourcelines(o_id_packets[next_packet_id])[1]
        verbose_print(f"Inserting the packet {packet_name} ({hex(packet_id)}) before {o_id_packets[next_packet_id]}")
    else:
        file = inspect.getfile(o_id_packets[max(o_id_packets)])
        with Path(file).open("r") as f:
            line_number = len(f.readlines())
        verbose_print(f"Appending the packet {packet_name} ({hex(packet_id)}) at the end of the file {file}")

    current_id = packet_id
    while current_id in o_id_packets:
        edit_packet_id(o_id_packets[current_id], current_id + 1)
        current_id += 1

    with Path(file).open("r") as f:
        file_content = f.readlines()
        while file_content[line_number - 1].startswith("@"):  # Avoid inserting the packet inside the decorators
            line_number -= 1

        file_content.insert(
            line_number,
            PACKET_TEMPLATE_INSERT.format(
                packet_name=packet_name,
                packet_id=hex(packet_id),
                game_state=game_state.name,
                boundness="ClientBound" if boundness == "clientbound" else "ServerBound",
            ),
        )
    with Path(file).open("w") as f:
        f.writelines(file_content)
    format_ruff(Path(file), silent=not _verbose)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Utility to update the packets modules.",
        epilog="The goal of this script is not to automate all the update process, but to help identify the changes"
        "and inconsistencies that could have been introduced between the version changes.",
    )
    parser.add_argument(
        "-i", "--init", action="store_true", help="Generate the __init__.py files for all game states."
    )
    parser.add_argument(
        "-c",
        "--continuity",
        action="store_true",
        help="Check the continuity of the packet ids and check for duplicates.",
    )
    parser.add_argument("-o", "--check-redaction-order", action="store_true", help="Check the redaction order.")
    parser.add_argument(
        "-O",
        "--skip-redaction-order",
        action="store_true",
        help="Skip the redaction order check when inserting a new packet or executing everything.",
    )
    parser.add_argument("-s", "--check-game-state", action="store_true", help="Check the game state of the packets.")
    parser.add_argument(
        "-b", "--check-boundness-docstring", action="store_true", help="Check the boundness in the docstrings."
    )
    parser.add_argument(
        "-C",
        "--compare-packets",
        type=str,
        default=None,
        metavar="packets.json",
        help="Compare the packets with the packets definition.",
    )
    parser.add_argument(
        "-r",
        "--replace-names",
        action="store_true",
        help="Replace the name of the packets in the packets modules.",
    )
    parser.add_argument(
        "-A",
        "--auto-insert",
        action="store_true",
        help="Automatically insert the packets in the code when they are missing. This works with --compare-packets.",
    )

    parser.add_argument(
        "-R",
        "--auto-change-packet-id",
        action="store_true",
        help="Automatically change the packet id. This works with --compare-packets.",
    )

    parser.add_argument("-a", "--all", action="store_true", help="Run all checks.")

    parser.add_argument(
        "-I",
        "--insert-packet",
        action="store_true",
        help="Insert a new packet in the packets modules. The packet id must be provided.",
    )

    parser.add_argument(
        "-G",
        "--game-state",
        type=str,
        choices=[g.name for g in GAME_STATES],
        help="The game state to check the packets for / insert the packets into.",
    )

    parser.add_argument(
        "-B",
        "--boundness",
        type=str,
        choices=["clientbound", "serverbound"],
        help="The boundness of the packet to be inserted.",
    )

    parser.add_argument(
        "-n",
        "--packet-name",
        type=str,
        help="The name of the packet to be inserted.",
    )

    parser.add_argument(
        "-p",
        "--packet-id",
        type=str,
        help="The id of the packet to be inserted.",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Print verbose output.")

    args = parser.parse_args()
    _verbose = args.verbose

    if args.insert_packet:
        if not args.game_state or not args.boundness or not args.packet_name or not args.packet_id:
            parser.error("The game state, boundness, packet name, and packet id must be provided.")

        packet_id = int(args.packet_id, 16)
        packet_name = packet_name_to_class_name(args.packet_name)
        game_state = {g.name: g for g in GAME_STATES}[args.game_state.upper()]
        boundness = args.boundness

        if not args.skip_redaction_order:
            packets = list_imports_module(PACKETS_MODULES[game_state], packets_only=True)
            packets_bound = filter_bound(packets, boundness)
            if not check_redaction_order(packets_bound, game_state, boundness):
                report_error(
                    "The redaction order is not correct. Please ensure that the order in which the packets are defined"
                    "is the same as the order of the packet ids before inserting a new packet.",
                    game_state,
                    boundness,
                )
                sys.exit(1)

        insert_packet(game_state, boundness, packet_name, packet_id)
        sys.exit(0)

    if args.game_state:
        game_states = [{g.name: g for g in GAME_STATES}[args.game_state.upper()]]
    else:
        game_states = GAME_STATES

    packets_by_game_state = {
        game_state: list_imports_module(PACKETS_MODULES[game_state], packets_only=True) for game_state in game_states
    }

    if args.init:
        print("Generating __init__.py files ...")  # noqa: T201
        for game_state in game_states:
            generate_init(game_state)
    if args.continuity or args.all:
        print("Checking continuity of the packets ...")  # noqa: T201
        for game_state in game_states:
            packets = packets_by_game_state[game_state]
            for boundness in ("clientbound", "serverbound"):
                packets_bound = filter_bound(packets, boundness)
                verbose_print(f"Checking continuity for {game_state.name} ({boundness})")
                check_continuity(packets_bound, game_state, boundness)

    if args.check_redaction_order or (args.all and not args.skip_redaction_order):
        print("Checking redaction order of the packets ...")  # noqa: T201
        for game_state in game_states:
            packets = packets_by_game_state[game_state]
            for boundness in ("clientbound", "serverbound"):
                packets_bound = filter_bound(packets, boundness)
                verbose_print(f"Checking redaction order for {game_state.name} ({boundness})")
                check_redaction_order(packets_bound, game_state, boundness)

    if args.check_game_state or args.all:
        print("Checking game state of the packets ...")  # noqa: T201
        for game_state in game_states:
            verbose_print(f"Checking game state for {game_state.name}")
            check_game_state(packets_by_game_state[game_state], game_state)
    if args.check_boundness_docstring or args.all:
        print("Checking boundness in the docstrings ...")  # noqa: T201
        for game_state in game_states:
            verbose_print(f"Checking boundness docstrings for {game_state.name}")
            check_boundness_docstring(packets_by_game_state[game_state], game_state)
    if args.compare_packets:
        print("Comparing packets with the packets definition ...")  # noqa: T201
        for game_state in game_states:
            for boundness in ("clientbound", "serverbound"):
                packets_bound = filter_bound(packets_by_game_state[game_state], boundness)
                verbose_print(f"Comparing packets for {game_state.name} ({boundness})")
                compare_with_packet_definition(
                    packets=packets_bound,
                    game_state=game_state,
                    boundness=boundness,
                    packets_file=args.compare_packets,
                    replace_names=args.replace_names,
                    auto_insert=args.auto_insert,
                    auto_change_packet_id=args.auto_change_packet_id,
                )
