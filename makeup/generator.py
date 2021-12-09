from io import StringIO

from .parser import (
    Type,
    Types,
    ArrayType,
    BuiltinType,
    EnumType,
    PointerType,
    StructType,
    UnhandledType,
)


def generate(types: Types, indent_size: int = 4, max_array_size: int = 10) -> str:
    output = StringIO()

    def emit(text: str = "") -> None:
        output.write(text)
        output.write("\n")

    def gen_indent(indent: int) -> None:
        spaces = " " * indent
        emit(f'MAKEUP_PRINT("{spaces}");')

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

    for name, type in types.enums.items():
        emit(f"void makeup_dump_enum_{name}(enum {name} *value);")

    for name, type in types.structs.items():
        emit(f"void makeup_dump_struct_{name}(struct {name} *value);")

    for name, type in types.typedefs.items():
        emit(f"void makeup_dump_{name}({name} *value);")

    emit("#ifdef MAKEUP_IMPLEMENTATION")

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

    emit("#endif")

    return output.getvalue()
