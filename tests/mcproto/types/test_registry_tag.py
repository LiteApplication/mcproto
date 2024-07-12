from mcproto.types import Identifier, RegistryTag
from tests.helpers import gen_serializable_test

gen_serializable_test(
    context=globals(),
    cls=RegistryTag,
    fields=[
        ("name", Identifier),
        ("values", "list[int]"),
    ],
    serialize_deserialize=[
        ((Identifier("wool"), [1, 2, 3]), bytes(Identifier("wool").serialize() + b"\x03\x01\x02\x03")),
        ((Identifier("block"), [1, 2, 3, 4]), bytes(Identifier("block").serialize() + b"\x04\x01\x02\x03\x04")),
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
