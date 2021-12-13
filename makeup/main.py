from typing import Optional

import typer

from .generator import generate
from .parser import parse


app = typer.Typer()


@app.command()
def main(
    input: typer.FileText = typer.Argument(..., allow_dash=True),
    output: Optional[typer.FileTextWrite] = typer.Argument(None),
    indent_size: int = typer.Option(2),
    max_array_size: int = typer.Option(10),
    max_depth: int = typer.Option(4),
    follow_pointers: bool = typer.Option(True),
):
    """
    Generate a pretty-printer for C structs
    """
    input_text = typer.open_file(str(input)).read()
    output_text = generate(
        parse(input_text),
        indent_size=indent_size,
        max_array_size=max_array_size,
        max_depth=max_depth,
        follow_pointers=follow_pointers,
    )
    typer.echo(output_text, output)
