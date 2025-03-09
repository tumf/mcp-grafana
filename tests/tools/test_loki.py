import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from mcp_grafana.tools.loki import (
    query_loki,
    list_loki_label_names,
    list_loki_label_values,
    query_loki_logs,
    query_loki_metrics,
    query_loki_instant,
)


@pytest.fixture
def mock_grafana_client():
    with patch("mcp_grafana.tools.loki.grafana_client") as mock_client:
        mock_client.query = AsyncMock()
        mock_client.get = AsyncMock()
        yield mock_client


@pytest.mark.asyncio
async def test_query_loki(mock_grafana_client):
    # Setup
    mock_grafana_client.query.return_value = json.dumps(
        {
            "results": {
                "A": {
                    "frames": [
                        {
                            "schema": {
                                "fields": [
                                    {"name": "Time", "type": "time"},
                                    {"name": "Value", "type": "number"},
                                ]
                            },
                            "data": {"values": [[1000, 2000], [1.5, 2.5]]},
                        }
                    ]
                }
            }
        }
    )

    # Execute
    start = datetime.now() - timedelta(hours=1)
    end = datetime.now()
    result = await query_loki(
        datasource_uid="loki",
        expr='{app="test"}',
        start_rfc3339=start.isoformat(),
        end_rfc3339=end.isoformat(),
        step_seconds=60,
    )

    # Verify
    mock_grafana_client.query.assert_called_once()
    assert "A" in result.results
    assert len(result.results["A"].frames) == 1


@pytest.mark.asyncio
async def test_list_loki_label_names(mock_grafana_client):
    # Setup
    mock_grafana_client.get.return_value = json.dumps(
        {"status": "success", "data": ["app", "instance", "job"]}
    )

    # Execute
    result = await list_loki_label_names(datasource_uid="loki")

    # Verify
    mock_grafana_client.get.assert_called_once()
    assert isinstance(result, list)
    assert "app" in result
    assert "instance" in result
    assert "job" in result


@pytest.mark.asyncio
async def test_list_loki_label_values(mock_grafana_client):
    # Setup
    mock_grafana_client.get.return_value = json.dumps(
        {"status": "success", "data": ["app1", "app2", "app3"]}
    )

    # Execute
    result = await list_loki_label_values(datasource_uid="loki", label_name="app")

    # Verify
    mock_grafana_client.get.assert_called_once()
    assert isinstance(result, list)
    assert "app1" in result
    assert "app2" in result
    assert "app3" in result


@pytest.mark.asyncio
async def test_query_loki_logs(mock_grafana_client):
    # Setup
    mock_grafana_client.query.return_value = json.dumps(
        {
            "results": {
                "A": {
                    "frames": [
                        {
                            "schema": {
                                "fields": [
                                    {"name": "Time", "type": "time"},
                                    {"name": "Line", "type": "string"},
                                ]
                            },
                            "data": {
                                "values": [
                                    [1000, 2000],
                                    ["log line 1", "log line 2"],
                                ]
                            },
                        }
                    ]
                }
            }
        }
    )

    # Execute
    start = datetime.now() - timedelta(hours=1)
    end = datetime.now()
    result = await query_loki_logs(
        datasource_uid="loki",
        query='{app="test"}',
        start_rfc3339=start.isoformat(),
        end_rfc3339=end.isoformat(),
    )

    # Verify
    mock_grafana_client.query.assert_called_once()
    assert "A" in result.results
    assert len(result.results["A"].frames) == 1


@pytest.mark.asyncio
async def test_query_loki_metrics(mock_grafana_client):
    # Setup
    mock_grafana_client.query.return_value = json.dumps(
        {
            "results": {
                "A": {
                    "frames": [
                        {
                            "schema": {
                                "fields": [
                                    {"name": "Time", "type": "time"},
                                    {"name": "Value", "type": "number"},
                                ]
                            },
                            "data": {"values": [[1000, 2000], [1.5, 2.5]]},
                        }
                    ]
                }
            }
        }
    )

    # Execute
    start = datetime.now() - timedelta(hours=1)
    end = datetime.now()
    result = await query_loki_metrics(
        datasource_uid="loki",
        query='rate({app="test"}[5m])',
        start_rfc3339=start.isoformat(),
        end_rfc3339=end.isoformat(),
    )

    # Verify
    mock_grafana_client.query.assert_called_once()
    assert "A" in result.results
    assert len(result.results["A"].frames) == 1


@pytest.mark.asyncio
async def test_query_loki_instant(mock_grafana_client):
    # Setup
    mock_grafana_client.query.return_value = json.dumps(
        {
            "results": {
                "A": {
                    "frames": [
                        {
                            "schema": {
                                "fields": [
                                    {"name": "Time", "type": "time"},
                                    {"name": "Value", "type": "number"},
                                ]
                            },
                            "data": {"values": [[1000], [1.5]]},
                        }
                    ]
                }
            }
        }
    )

    # Execute
    time = datetime.now()
    result = await query_loki_instant(
        datasource_uid="loki",
        query='rate({app="test"}[5m])',
        time_rfc3339=time.isoformat(),
    )

    # Verify
    mock_grafana_client.query.assert_called_once()
    assert "A" in result.results
    assert len(result.results["A"].frames) == 1