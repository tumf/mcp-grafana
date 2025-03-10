import enum
import os
from typing import Optional

import typer

from . import mcp
from .settings import grafana_settings

app = typer.Typer()


class Transport(enum.StrEnum):
    stdio = "stdio"
    sse = "sse"


@app.command()
def run(
    transport: Transport = Transport.stdio,
    grafana_url: Optional[str] = typer.Option(
        None, 
        "--grafana-url", 
        "-u", 
        help="The URL of the Grafana instance. Overrides GRAFANA_URL environment variable."
    ),
    grafana_api_key: Optional[str] = typer.Option(
        None, 
        "--grafana-api-key", 
        "-k", 
        help="A Grafana API key or service account token. Overrides GRAFANA_API_KEY environment variable."
    ),
):
    # Update settings if command line options are provided
    if grafana_url:
        grafana_settings.url = grafana_url
    if grafana_api_key:
        grafana_settings.api_key = grafana_api_key
        
    mcp.run(transport.value)
