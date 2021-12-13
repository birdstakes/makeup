from typing import Optional

import typer

from .generator import generate
from .parser import parse


app = typer.Typer()


@app.command()
def main(
    input: typer.FileText = typer.Argument(..., allow_dash=True),
    output: Optional[typer.FileTextWrite] = typer.Argument(None),
    follow_pointers: bool = typer.Option(True),
):
    """
    Generate a pretty-printer for C structs
    """
    input_text = typer.open_file(str(input)).read()
    output_text = generate(parse(input_text), follow_pointers=follow_pointers)
    typer.echo(output_text, output)
