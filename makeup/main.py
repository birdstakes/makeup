from dataclasses import dataclass
from pathlib import Path

from pycparser import c_ast, c_parser  # TODO move shit out of here

import sys
import typer


app = typer.Typer()


# TODO is this necessary?
@app.callback()
def callback():
    """
    Generate a pretty-printer for C structs
    """


# TODO is THIS necessary? this program shouldn't really have subcommands
@app.command()
def generate(
    path: Path = typer.Argument(..., exists=True, readable=True, allow_dash=True)
):
    """
    Generate a pretty-printer for C structs
    """
    # TODO move shit out of here, write tests of some sort?

    if str(path) == "-":
        input = sys.stdin.read()
    else:
        with path.open() as f:
            input = f.read()

    makeup(input)


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


def parse(input):
    parser = c_parser.CParser()
    ast = parser.parse(input)

    structs = {}
    typedefs = {}
    enums = {}

    def get_type(node) -> Type:
        if isinstance(node, c_ast.Decl):
            return get_type(node.type)

        elif isinstance(node, c_ast.TypeDecl):
            return get_type(node.type)

        elif isinstance(node, c_ast.IdentifierType):
            if node.names[0] in typedefs:
                return typedefs[node.names[0]]
            return BuiltinType(node.names)

        elif isinstance(node, c_ast.PtrDecl):
            return PointerType(get_type(node.type))

        elif isinstance(node, c_ast.ArrayDecl):
            if isinstance(node.dim, c_ast.Constant):
                return ArrayType(get_type(node.type), int(node.dim.value, 0))
            else:
                # TODO
                # it might be an enum or something
                # if so maybe generated code could just use the enum's name
                # kinda hacky but probably works most if not all of the time
                return UnhandledType()
        elif isinstance(node, c_ast.Typedef):
            type = get_type(node.type)
            typedefs[node.name] = type
            return type

        elif isinstance(node, c_ast.Struct):
            if node.decls is None:
                if node.name not in structs:
                    structs[node.name] = StructType([])
                return structs[node.name]

            fields = []
            for decl in node.decls:
                fields.append((decl.name, get_type(decl.type)))

            struct = structs.get(node.name, StructType([]))
            struct.fields = fields
            if node.name is not None:
                structs[node.name] = struct

            return struct

        elif isinstance(node, c_ast.Enum):
            if node.values is None:
                if node.name not in enums:
                    enums[node.name] = EnumType([])
                return enums[node.name]

            enumerators = [e.name for e in node.values.enumerators]

            enum = enums.get(node.name, EnumType([]))
            enum.enumerators = enumerators
            if node.name is not None:
                enums[node.name] = enum

            return enum

        else:
            return UnhandledType()

    for node in ast:
        get_type(node)

    return Types(enums, structs, typedefs)


def makeup(input: str) -> None:
    types = parse(input)

    makeup_file = open("makeup.h", "w")

    def emit(text: str = "") -> None:
        makeup_file.write(text)
        makeup_file.write("\n")

    def gen_indent(indent: int) -> None:
        spaces = " " * indent
        emit(f'MAKEUP_PRINT("{spaces}");')

    indent_size = 4
    max_array_size = 10

    def gen_printer(type: Type, expr: str, indent: int = 0) -> None:
        match type:
            case BuiltinType(names):
                # TODO try to handle these correctly
                if "float" in names:
                    emit(f"MAKEUP_PRINT_FLOAT({expr});")
                elif "unsigned" in names:
                    emit(f"MAKEUP_PRINT_UNSIGNED({expr});")
                else:
                    emit(f"MAKEUP_PRINT_SIGNED({expr});")

            case ArrayType(type, size):
                # TODO generate a for loop
                emit('MAKEUP_PRINT("[\\n");')
                for i in range(min(size, max_array_size)):
                    gen_indent(indent + indent_size)
                    gen_printer(type, f"{expr}[{i}]", indent + indent_size)
                    emit('MAKEUP_PRINT(",\\n");')
                if size > max_array_size:
                    gen_indent(indent + indent_size)
                    emit('MAKEUP_PRINT("...\\n");')
                gen_indent(indent)
                emit('MAKEUP_PRINT("]");')

            case PointerType(type):
                emit(f"MAKEUP_PRINT_POINTER({expr});")

            case StructType(fields):
                emit('MAKEUP_PRINT("{\\n");')
                for name, type in fields:
                    gen_indent(indent + indent_size)
                    emit(f'MAKEUP_PRINT("{name} = ");')
                    gen_printer(type, f"{expr}.{name}", indent + indent_size)
                    emit('MAKEUP_PRINT(",\\n");')
                gen_indent(indent)
                emit('MAKEUP_PRINT("}");')

            case EnumType(enumerators):
                emit(f"switch({expr}) {{")
                for name in enumerators:
                    emit(f'case {name}: MAKEUP_PRINT("{name}"); break;')
                emit(
                    f'default: MAKEUP_PRINT("%d (invalid enumerator)", {expr}); break;'
                )
                emit("}")

            case UnhandledType():
                emit('MAKEUP_PRINT("unhandled");')

            case _:
                raise NotImplementedError(type)

    emit("#ifndef MAKEUP_PRINT")
    emit("#include <stdio.h>")
    emit("#define MAKEUP_PRINT printf")
    emit("#endif")

    emit("#ifndef MAKEUP_PRINT_SIGNED")
    emit('#define MAKEUP_PRINT_SIGNED(i) MAKEUP_PRINT("%d", i)')
    emit("#endif")

    emit("#ifndef MAKEUP_PRINT_UNSIGNED")
    emit('#define MAKEUP_PRINT_UNSIGNED(u) MAKEUP_PRINT("%u", u)')
    emit("#endif")

    emit("#ifndef MAKEUP_PRINT_FLOAT")
    emit('#define MAKEUP_PRINT_FLOAT(f) MAKEUP_PRINT("%f", f)')
    emit("#endif")

    emit("#ifndef MAKEUP_PRINT_POINTER")
    emit('#define MAKEUP_PRINT_POINTER(p) MAKEUP_PRINT("0x%p", p)')
    emit("#endif")

    for name, type in types.enums.items():
        emit(f"void makeup_dump_enum_{name}(enum {name} *value) {{")
        gen_printer(type, "(*value)")
        emit("}")

    for name, type in types.structs.items():
        emit(f"void makeup_dump_struct_{name}(struct {name} *value) {{")
        gen_printer(type, "(*value)")
        emit("}")

    for name, type in types.typedefs.items():
        emit(f"void makeup_dump_{name}({name} *value) {{")
        gen_printer(type, "(*value)")
        emit("}")

    makeup_file.close()
