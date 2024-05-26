from mcproto.types.tag import RegistryTag
from tests.helpers import gen_serializable_test
from mcproto.types.identifier import Identifier


gen_serializable_test(
    context=globals(),
    cls=RegistryTag,
    fields=[("name", Identifier), ("values", "list[int]")],
    serialize_deserialize=[
        (
            (Identifier("stone"), [1, 2, 3]),
            b"\x0fminecraft:stone\x03\x01\x02\x03",
        ),
        (
            (Identifier("stone_brick"), [1, 2, 3, 4]),
            b"\x15minecraft:stone_brick\x04\x01\x02\x03\x04",
        ),
        (
            (Identifier("stone_brick_slab"), [1, 2, 3, 4, 5]),
            b"\x1aminecraft:stone_brick_slab\x05\x01\x02\x03\x04\x05",
        ),
    ],
)


def test_tag_str():
    """Test the __str__ method of the RegistryTag class."""
    tag = RegistryTag(Identifier("stone"), [1, 2, 3])
    assert str(tag) == "#minecraft:stone"
    tag = RegistryTag(Identifier("stone_brick"), [1, 2, 3, 4])
    assert str(tag) == "#minecraft:stone_brick"
    tag = RegistryTag(Identifier("stone_brick_slab"), [1, 2, 3, 4, 5])
    assert str(tag) == "#minecraft:stone_brick_slab"
