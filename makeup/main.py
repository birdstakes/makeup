from dataclasses import dataclass
from pathlib import Path
from typing import Optional

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


def parse(input):
    parser = c_parser.CParser()
    ast = parser.parse(input)

    structs = {}
    typedefs = {}

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
            if node.name in structs:
                struct = structs[node.name]
                struct.fields = fields
            else:
                struct = StructType(fields)
                if node.name is not None:
                    structs[node.name] = struct
            return struct
        else:
            return UnhandledType()

    for node in ast:
        get_type(node)

    return structs, typedefs


def makeup(input: str) -> None:
    structs, typedefs = parse(input)

    makeup_file = open("makeup.h", "w")

    def emit(text: str = "") -> None:
        makeup_file.write(text)
        makeup_file.write("\n")

    def gen_indent(indent: int) -> None:
        spaces = ' ' * indent
        emit(f'printf("{spaces}");')

    indent_size = 4
    max_array_size = 10

    def gen_printer(type: Type, expr: str, indent: int = 0) -> None:
        match type:
            case BuiltinType(names):
                # TODO try to handle these correctly
                if 'float' in names:
                    fmt = 'f'
                elif 'unsigned' in names:
                    fmt = 'u'
                else:
                    fmt = 'd'

                emit(f'printf("%{fmt}", {expr});')

            case ArrayType(type, size):
                # TODO generate a for loop
                emit('printf("[\\n");')
                for i in range(min(size, max_array_size)):
                    gen_indent(indent + indent_size)
                    gen_printer(type, expr + f'[{i}]', indent + indent_size)
                    emit('printf(",\\n");')
                if size > max_array_size:
                    gen_indent(indent + indent_size)
                    emit('printf("...\\n");')
                gen_indent(indent)
                emit('printf("]");')

            case PointerType(type):
                emit(f'printf("0x%p", {expr});')

            case StructType(fields):
                emit('printf("{\\n");')
                for name, type in fields:
                    gen_indent(indent + indent_size)
                    emit(f'printf("{name} = ");')
                    gen_printer(type, expr + f'.{name}', indent + indent_size)
                    emit('printf(",\\n");')
                gen_indent(indent)
                emit('printf("}");')

            case UnhandledType():
                emit('printf("unhandled");')

            case _:
                raise NotImplementedError(type)

    emit('#include <stdio.h>')

    for name, type in structs.items():
        emit(f'void makeup_dump_struct_{name}(struct {name} *value, int indent) {{')
        gen_printer(type, '(*value)')
        emit('}')

    for name, type in typedefs.items():
        emit(f'void makeup_dump_{name}({name} *value) {{')
        gen_printer(type, '(*value)')
        emit('}')

    makeup_file.close()
