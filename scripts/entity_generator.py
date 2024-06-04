from __future__ import annotations
from typing import List, Dict, Union, cast
from pathlib import Path
import subprocess
import sys

from scripts.entity_generator_data import ENTITY_DATA, EntityData, Field

BASE_CLASS = '''
class {name}({base}):
    """{class_description}

    {fields_docstring}

    """

    {fields}

    __slots__ = ()

'''


ENTRY_FIELD = """{name}: {input} = entry({type}, {default})"""
INPUT_UNAVAILABLE = """ClassVar[{input}]"""
# Mark as ignore by sphinx
PROXY_FIELD = """{name}: {input} = proxy({target}, {type}, {kwargs})"""

FIELD_DESCRIPTION = """:param {name}: {description}
:type {name}: {input}, optional, default: {default}"""
PROXY_DESCRIPTION = """:param {name}: {description} (this affects :attr:`{target}`)
:type {name}: {input}, optional"""
UNAVAILABLE_PREFIX = "_"
TYPE_SUFFIX = "EME"  # EntityMetadataEntry
NAME_SUFFIX = "EM"  # EntityMetadata


FILE_HEADER = """
######################################################################
# This file is automatically generated by the entity generator script.
#     You can modify it by changing what you want in the script.
######################################################################

from mcproto.types.entity.enums import {enums}

__all__ = [
    {all}
]
"""

BASE_FILE = """
from __future__ import annotations
{header}

from typing import ClassVar
from mcproto.types.entity.metadata import (
    proxy,
    entry,
    EntityMetadata,
)
from mcproto.types.entity.metadata_types import {types}
from mcproto.types.slot import Slot
from mcproto.types.chat import TextComponent
from mcproto.types.nbt import NBTag, EndNBT
from mcproto.types.vec3 import Position
from mcproto.types.uuid import UUID
from mcproto.types.particle_data import ParticleData

{classes}
"""
INIT_FILE = """
from mcproto.types.entity.generated import {generated}
{header}
"""

FILE_PATH = "mcproto/types/entity/generated.py"
INIT_PATH = "mcproto/types/entity/__init__.py"

# This dictionary holds the decumentation for each entity to allow it to be appended to inherited classes
main_doc_repo: dict[str, str] = {}


def generate_class(entity_description: EntityData) -> tuple[str, set[str], set[str]]:  # noqa: PLR0912
    """Generate a class from the entity description.

    :param entity_description: The entity description to generate the class from.

    :return: The generated string for the class, a set of used enums, and a set of used types.
    """
    field_docs: list[str] = []
    fields: list[str] = []
    used_enums: set[str] = set()
    used_types: set[str] = set()
    name = entity_description["name"]
    name = cast(str, name) + NAME_SUFFIX  # EntityMetadata
    base = entity_description.get("base", "EntityMetadata")
    base = cast(str, base)
    if base != "EntityMetadata":
        base += NAME_SUFFIX
    for variable in entity_description["fields"]:
        variable = cast(Field, variable)
        v_type = cast(str, variable["type"])
        v_name = cast(str, variable["name"])
        v_default = variable["default"]
        v_input = variable["input"]
        v_description = variable.get("description", "")
        v_proxy = cast(List[Dict[str, Union[type, str, int]]], variable.get("proxy", []))
        v_available = variable.get("available", True)
        v_enum = variable.get("enum", False)

        if v_enum:
            used_enums.add(v_type)
            v_default = f"{v_type}.{v_default}"

        v_type = v_type + TYPE_SUFFIX
        used_types.add(v_type)

        if not v_available:
            v_name = UNAVAILABLE_PREFIX + v_name

        if isinstance(v_input, type):
            v_input = v_input.__name__
        v_input = cast(str, v_input)

        if v_input == "str":
            v_default = f'"{v_default}"'

        if v_available:
            if v_description:
                if v_enum or not v_input.startswith(("str", "tuple", "float", "int", "bool")):
                    v_default_desc = f":attr:`{v_default}`"
                    v_input_desc = f":class:`{v_input}`"
                else:
                    v_default_desc = v_default
                    v_input_desc = v_input

                field_docs.append(
                    FIELD_DESCRIPTION.format(
                        name=v_name, description=v_description, input=v_input_desc, default=v_default_desc
                    )
                )
        else:
            v_input = INPUT_UNAVAILABLE.format(input=v_input)

        fields.append(
            ENTRY_FIELD.format(
                name=v_name,
                input=v_input,
                type=v_type,
                default=v_default,
            )
        )
        for proxy_field in v_proxy:
            proxy_name = cast(str, proxy_field["name"])
            proxy_type = cast(str, proxy_field["type"])
            proxy_input = proxy_field.get("input", int)
            proxy_description = proxy_field.get("description", "")
            proxy_target = v_name

            if isinstance(proxy_input, type):
                proxy_input = proxy_input.__name__  # convert the str type to "str" ...

            used_types.add(proxy_type)

            proxy_kwargs = ""
            for k, v in proxy_field.items():
                if k not in ("name", "type", "input", "description"):
                    if k == "mask":
                        v = cast(int, v)
                        v = hex(v)  # noqa: PLW2901
                    proxy_kwargs += f"{k}={v},"
            if proxy_kwargs:
                proxy_kwargs = proxy_kwargs[:-1]  # remove the last comma

            if proxy_description:
                field_docs.append(
                    PROXY_DESCRIPTION.format(
                        name=proxy_name,
                        description=proxy_description,
                        target=proxy_target,
                        input=proxy_input,
                    )
                )

            fields.append(
                PROXY_FIELD.format(
                    name=proxy_name,
                    input=proxy_input,
                    target=proxy_target,
                    type=proxy_type,
                    kwargs=proxy_kwargs,
                )
            )

    # Split lines inside docstrings

    if base in main_doc_repo:
        field_docs += ["", f"Inherited from :class:`{base}`:", ""] + [
            line.strip("\n\r\t").replace(" " * 4, "", 1) for line in main_doc_repo[base].split("\n")
        ]
    else:
        print(f"Warning: {base} not found in main_doc_repo")  # noqa: T201

    if field_docs[0] == "":
        field_docs = field_docs[1:]
    field_docs_str = "\n    ".join("\n".join(field_docs).split("\n"))
    main_doc_repo[name] = field_docs_str
    return (
        BASE_CLASS.format(
            name=name,
            base=base,
            class_description=entity_description["description"],
            fields_docstring=field_docs_str,
            fields="\n    ".join(fields),
        ),
        used_enums,
        used_types,
    )


def write_files(entity_data: list[EntityData]) -> None:
    """Generate the base file for the entities.

    :param entity_data: The entity data to generate the base file from.

    :return: The generated string for the base file.
    """
    types: set[str] = set()
    enums: set[str] = set()
    all_classes: list[str] = []
    class_code: list[str] = []
    generated: list[str] = []
    for entity in entity_data:
        class_str, used_enums, used_types = generate_class(entity)
        entity_name = cast(str, entity["name"]) + NAME_SUFFIX
        types.update(used_types)
        enums.update(used_enums)
        all_classes.append(entity_name)
        class_code.append(class_str)
        generated.append(entity_name)
    all_classes_str = ",\n    ".join(f'"{c}"' for c in all_classes + list(enums))
    types_str = ", ".join(sorted(types))
    enums_str = ", ".join(sorted(enums))
    generated_str = ", ".join(generated)

    header = FILE_HEADER.format(
        enums=enums_str,
        all=all_classes_str,
    )
    with Path(FILE_PATH).open("w") as file:
        file.write(
            BASE_FILE.format(
                types=types_str,
                header=header,
                classes="\n\n".join(class_code),
            )
        )

    with Path(INIT_PATH).open("w") as file:
        file.write(INIT_FILE.format(header=header, generated=generated_str))


def format_ruff(path: Path) -> None:
    """Format the generated files with ruff.

    :param path: The path to the file to format.
    """
    # Get the python site packages path
    subprocess.run(
        [sys.executable, "-m", "ruff", "format", str(path.absolute())],  # noqa: S603
        check=True,
    )


if __name__ == "__main__":
    write_files(ENTITY_DATA)
    format_ruff(Path(FILE_PATH))
    format_ruff(Path(INIT_PATH))
