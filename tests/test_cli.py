import pytest
from unittest.mock import patch, MagicMock

from mcp_grafana.cli import run, Transport
from mcp_grafana.settings import grafana_settings


@pytest.mark.parametrize(
    "url,api_key,expected_url,expected_api_key",
    [
        (None, None, "http://localhost:3000", None),  # Default values
        ("http://grafana.example.com", None, "http://grafana.example.com", None),  # Custom URL
        (None, "api-key-123", "http://localhost:3000", "api-key-123"),  # Custom API key
        ("http://grafana.example.com", "api-key-123", "http://grafana.example.com", "api-key-123"),  # Both custom
    ],
)
def test_cli_options(url, api_key, expected_url, expected_api_key):
    # Reset settings to default values
    grafana_settings.url = "http://localhost:3000"
    grafana_settings.api_key = None
    
    # Mock the mcp.run function to prevent actual execution
    with patch("mcp_grafana.cli.mcp.run") as mock_run:
        # Call the CLI function with the test parameters
        run(transport=Transport.stdio, grafana_url=url, grafana_api_key=api_key)
        
        # Verify settings were updated correctly
        assert grafana_settings.url == expected_url
        assert grafana_settings.api_key == expected_api_key
        
        # Verify mcp.run was called with the correct transport
        mock_run.assert_called_once_with("stdio")