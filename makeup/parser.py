from dataclasses import dataclass

from pycparser import c_ast, c_parser


class Type:
    pass


@dataclass
class BuiltinType(Type):
    names: list[str]


@dataclass
class EnumType(Type):
    enumerators: list[str]


@dataclass
class StructType(Type):
    fields: list[tuple[str, Type]]


@dataclass
class ArrayType(Type):
    type: Type
    size: int


@dataclass
class PointerType(Type):
    type: Type


class UnhandledType(Type):
    pass


@dataclass
class Types:
    enums: dict[str, EnumType]
    structs: dict[str, StructType]
    typedefs: dict[str, Type]


def parse(input: str) -> Types:
    parser = c_parser.CParser()
    ast = parser.parse(input)

    structs = {}
    typedefs = {}
    enums = {}

    def get_type(node) -> Type:
        match node:
            case c_ast.Decl():
                return get_type(node.type)

            case c_ast.TypeDecl():
                return get_type(node.type)

            case c_ast.IdentifierType():
                if node.names[0] in typedefs:
                    return typedefs[node.names[0]]
                return BuiltinType(node.names)

            case c_ast.PtrDecl():
                return PointerType(get_type(node.type))

            case c_ast.ArrayDecl(dim=c_ast.Constant()):
                return ArrayType(get_type(node.type), int(node.dim.value, 0))

            case c_ast.Typedef():
                type = get_type(node.type)
                typedefs[node.name] = type
                return type

            case c_ast.Struct(decls=None):
                if node.name not in structs:
                    structs[node.name] = StructType([])
                return structs[node.name]

            case c_ast.Struct():
                fields = []
                for decl in node.decls:
                    fields.append((decl.name, get_type(decl.type)))

                struct = structs.get(node.name, StructType([]))
                struct.fields = fields
                if node.name is not None:
                    structs[node.name] = struct

                return struct

            case c_ast.Enum(values=None):
                if node.name not in enums:
                    enums[node.name] = EnumType([])
                return enums[node.name]

            case c_ast.Enum():
                enumerators = [e.name for e in node.values.enumerators]

                enum = enums.get(node.name, EnumType([]))
                enum.enumerators = enumerators
                if node.name is not None:
                    enums[node.name] = enum

                return enum

            case _:
                return UnhandledType()

    for node in ast:
        get_type(node)

    return Types(enums, structs, typedefs)
