"""Global dictionary for types."""
from typing import Dict
from typing import Sequence
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union


if TYPE_CHECKING:
    from collections import UserString
    from .type_expression import TypeName
    from .type_declaration import ITypeDeclaration
    from ._TypeDeclarationProtocol import TypeDeclarationProtocol


import logging

logger = logging.getLogger(__name__)

# handling global state
# Sources:
# - https://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python

_TYPE_DECLARATIONS: Dict[
    Union[str, "UserString", "TypeName"], "TypeDeclarationProtocol"
] = {}


def register_type_declaration(
    type_name: "str | UserString | TypeName",
    type_declaration: "TypeDeclarationProtocol",  # "ITypeDeclaration"
) -> None:
    """Register a type declaration globally.

    Args:
        type_name (str | UserString | TypeName): Identifier for the type to register
        type (Type): type declaration to register
    """
    global _TYPE_DECLARATIONS
    if type_name in _TYPE_DECLARATIONS:
        logger.warning(f"Overriding type {type_name}")
        print(f"Overriding type {type_name}")

    _TYPE_DECLARATIONS.update()


def register_type_declarations(
    type_declarations: Sequence[
        Tuple["str | UserString | TypeName", "ITypeDeclaration"]
    ]
) -> None:
    for type_name, type in type_declarations:
        register_type_declaration(type_name=type_name, type_declaration=type)


def lookup_type_declaration(
    type_name: "str | UserString | TypeName",
) -> "TypeDeclarationProtocol":
    """Lookup a type declaration in the global dictionary.

    Args:
        type_name (str | UserString | TypeName): Name of the type

    Raises:
        KeyError: Exception fo an unknown type

    Returns:
        ITypeDeclaration | NoReturn: type declaration
    """
    global _TYPE_DECLARATIONS
    if type_name in _TYPE_DECLARATIONS:
        return _TYPE_DECLARATIONS[type_name]
    raise KeyError(f"{type_name} is not registered as a type")
