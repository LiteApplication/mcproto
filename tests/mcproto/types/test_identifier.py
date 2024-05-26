from mcproto.types.identifier import Identifier
from tests.helpers import gen_serializable_test


gen_serializable_test(
    context=globals(),
    cls=Identifier,
    fields=[("namespace", str), ("path", str)],
    serialize_deserialize=[
        (("minecraft", "stone"), b"\x0fminecraft:stone"),
        (("minecraft", "stone_brick"), b"\x15minecraft:stone_brick"),
        (("minecraft", "stone_brick_slab"), b"\x1aminecraft:stone_brick_slab"),
    ],
    validation_fail=[
        (("minecr*ft", "stone_brick_slab_top"), ValueError),  # Invalid namespace
        (("minecraft", "stone_brick_slab_t@p"), ValueError),  # Invalid path
        (("", "something"), ValueError),  # Empty namespace
        (("minecraft", ""), ValueError),  # Empty path
        (("minecraft", "a" * 32767), ValueError),  # Too long
    ],
)


def test_identifier_one_arg():
    """Test the Identifier class when only one argument is provided."""
    identifier = Identifier("minecraft:stone")
    assert identifier.namespace == "minecraft"
    assert identifier.path == "stone"

    identifier = Identifier("stone_brick")
    assert identifier.namespace == "minecraft"
    assert identifier.path == "stone_brick"

    identifier = Identifier("minecraft:stone_brick_slab")
    assert identifier.namespace == "minecraft"
    assert identifier.path == "stone_brick_slab"

    identifier = Identifier("#dirt")
    assert identifier.namespace == "minecraft"
    assert identifier.path == "dirt"


def test_identifier_dunder():
    """Test __hash__, __str__, and __repr__ methods of the Identifier class."""
    identifier = Identifier("minecraft:stone")
    assert hash(identifier) == hash(("minecraft", "stone"))
    assert str(identifier) == "minecraft:stone"
    assert repr(identifier) == "Identifier(namespace='minecraft', path='stone')"
    assert identifier == Identifier("minecraft:stone")
