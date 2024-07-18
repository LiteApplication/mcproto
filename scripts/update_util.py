from __future__ import annotations

import importlib
import inspect
import json
from difflib import get_close_matches
from enum import Enum
from pathlib import Path
from typing import Literal, Sequence, Union, cast, overload

from typing_extensions import TypeAlias

from mcproto.packets import GameState, Packet
from mcproto.packets.packet import ClientBoundPacket, ServerBoundPacket
from scripts.entity_generator import format_ruff

# The names of certain packets that are defined differently in our implementation
# This is used to ignore name mismatches
VOLUNTARY_PACKETS_NAMES = {
    "Handshake": "Intention",  # Handshake os clearer
    "LoginEncryptionResponse": "Key",  # That's just not explicit enough
    "LoginEncryptionRequest": "Hello",  # Same packet name used in 2 different things
    "LoginStart": "Hello",
    "PingPong": "PongResponse",  # Used by both the client and the server
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
class {packet_name}({boundness}Packet):
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

REPLACE_PACKET_ID_TEMPLATE = "PACKET_ID: ClassVar[int] = {packet_id}"


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
    print(f"{ANSI_COLORS['red']}Error:{ANSI_COLORS['reset']}", before, message)  # noqa: T201


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
    """Check if the packet ids are continuous. Return True if the packets are continuous."""
    packets = list(packets)
    packets.sort(key=lambda packet: packet.PACKET_ID)
    previous_packet: type[Packet] | None = None
    error = False
    for packet in packets:
        if previous_packet is not None and previous_packet.PACKET_ID + 1 != packet.PACKET_ID:
            report_error(
                f"{previous_packet.__name__} (ID: {hex(previous_packet.PACKET_ID)})"
                f"-> {packet.__name__} (ID: {hex(packet.PACKET_ID)})",
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
            report_error(f"{previous_packet.__name__} is written after {packet.__name__}", game_state, boundness)
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
    expected_names = set(m_id_packets_new_name.values()).union(set(VOLUNTARY_PACKETS_NAMES.keys()))
    for packet in packets:
        if packet.__name__ not in expected_names:
            closest = get_close_matches(packet.__name__, expected_names)
            by_id = m_id_packets_new_name.get(packet.PACKET_ID, None)
            message = f"`{packet.__name__}` is not in the packets file"
            if by_id is not None:
                message += f", but mentioned in the JSON file as `{by_id}`"
            if closest:
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
        if packet_id not in o_id_packets:
            if packet_name in set(o_id_packets.values()):
                found_id = next(id_ for id_, name in o_id_packets.items() if name == packet_name)
                report_error(
                    f"`{packet_name}` has the wrong packet ID (should be"
                    f" `{hex(packet_id)}`, found `{hex(found_id)}`).",
                    game_state,
                    boundness,
                )
            else:
                report_error(
                    f"`{packet_name}` ({hex(packet_id)}) is not defined in the packets modules.",
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
    parser.add_argument("-c", "--continuity", action="store_true", help="Check the continuity of the packet ids.")
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
        "-p",
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

    parser.add_argument("-a", "--all", action="store_true", help="Run all checks.")

    parser.add_argument(
        "-G",
        "--game-state",
        type=str,
        choices=[g.name for g in GAME_STATES],
        help="The game state to check the packets for.",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Print verbose output.")

    args = parser.parse_args()
    _verbose = args.verbose

    if args.game_state:
        game_states = [{g.name: g for g in GAME_STATES}[args.game_state.upper()]]
    else:
        game_states = GAME_STATES

    packets_by_game_state = {
        game_state: list_imports_module(PACKETS_MODULES[game_state], packets_only=True) for game_state in game_states
    }

    if args.init or args.all:
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
                )
