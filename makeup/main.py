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
class NamedType(Type):
    name: str


@dataclass
class StructType(NamedType):
    pass


@dataclass
class Array(Type):
    t: Type
    n: int


@dataclass
class Pointer(Type):
    t: Type


class NotHandled(Type):
    pass


def parse(input):
    parser = c_parser.CParser()
    ast = parser.parse(input)

    structs = {}

    def get_type(decl) -> Type:
        if isinstance(decl, c_ast.PtrDecl):
            return Pointer(get_type(decl.type))
        elif isinstance(decl, c_ast.ArrayDecl):
            if isinstance(decl.dim, c_ast.Constant):
                return Array(get_type(decl.type), int(decl.dim.value, 0))
            else:
                # it might be an enum
                # if so maybe generated code could just use the enum's name
                # kinda hacky but probably works most if not all of the time
                return NotHandled()
        else:
            if isinstance(decl.type, c_ast.Struct):
                return StructType(decl.type.name)
            else:
                return NamedType(decl.type.names[0])

    for node in ast:
        if isinstance(node, c_ast.Decl) and isinstance(node.type, c_ast.Struct):
            struct = {}
            for decl in node.type.decls:
                struct[decl.name] = get_type(decl.type)
            structs[node.type.name] = struct

    return structs


def makeup(input):
    structs = parse(input)

    makeup_file = open("makeup.h", "w")

    def emit(text=""):
        makeup_file.write(text)
        makeup_file.write("\n")

    def gen_printer(type):
        if isinstance(type, NamedType):
            if isinstance(type, StructType):
                emit(f"makeup_dump_struct_{type.name}(value, indent);")
                emit(f"value = (void*)((char*)value + sizeof(struct {type.name}));")
            else:
                emit(f"makeup_dump_{type.name}(value, indent + MAKEUP_INDENT);")
                emit(f"value = (void*)((char*)value + sizeof({type.name}));")
                return
        elif isinstance(type, Array):
            emit("{")
            emit("int i;")
            emit("int tmp_indent = indent; int indent = tmp_indent + MAKEUP_INDENT;")
            emit('MAKEUP_PRINTER("[\\n");')
            emit(f"for(i = 0; i < {type.n}; i++) {{")
            emit('MAKEUP_PRINTER("%*s", indent, "");')
            gen_printer(type.t)
            emit('MAKEUP_PRINTER(",\\n");')
            emit("}")
            emit("}")
            emit('MAKEUP_PRINTER("%*s]", indent, "");')
        elif isinstance(type, Pointer):
            emit('MAKEUP_PRINTER("%#p", value);')
        else:
            emit('MAKEUP_PRINTER("not handled");')

    def gen_struct_printer(struct):
        emit('MAKEUP_PRINTER("{\\n");')
        for name, type in struct.items():
            emit("{")
            emit(f"void *tmp_value = (void*)(&value->{name}); void *value = tmp_value;")
            emit("int tmp_indent = indent; int indent = tmp_indent + MAKEUP_INDENT;")
            emit(f'MAKEUP_PRINTER("%*s{name} = ", indent, "");')
            gen_printer(type)
            emit('MAKEUP_PRINTER("\\n");')
            emit("}")
        emit('MAKEUP_PRINTER("%*s}", indent, "");')

    emit("#include <stdio.h>")
    emit()
    emit("#ifndef MAKEUP_PRINTER")
    emit("#define MAKEUP_PRINTER printf")
    emit("#endif")
    emit()
    emit("#ifndef MAKEUP_INDENT")
    emit("#define MAKEUP_INDENT 2")
    emit("#endif")
    emit()
    emit("void makeup_dump_int(int *value, int indent);")
    emit("void makeup_dump_char(char *value, int indent);")
    emit("void makeup_dump_float(float *value, int indent);")
    emit()

    for name in structs:
        emit(f"void makeup_dump_{name}(struct {name} *value, int indent);")
    emit()

    emit("#ifdef MAKEUP_IMPLEMENTATION")
    emit()

    emit('void makeup_dump_int(int *value, int indent) { MAKEUP_PRINTER("%d", *value); }')
    emit('void makeup_dump_char(char *value, int indent) { MAKEUP_PRINTER("%d", *value); }')
    emit('void makeup_dump_float(float *value, int indent) { MAKEUP_PRINTER("%f", *value); }')
    emit()

    for name, type in structs.items():
        emit(f"void makeup_dump_struct_{name}(struct {name} *value, int indent) {{")
        gen_struct_printer(type)
        emit("}")
        emit()

    emit("#endif")

    makeup_file.close()
