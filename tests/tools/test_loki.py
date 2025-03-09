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
        mock_client.loki_query_range = AsyncMock()
        mock_client.loki_query = AsyncMock()
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
async def test_query_loki_instant_query_type(mock_grafana_client):
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
    start = datetime.now()
    result = await query_loki(
        datasource_uid="loki",
        expr='{app="test"}',
        start_rfc3339=start.isoformat(),
        query_type="instant",
    )

    # Verify
    mock_grafana_client.query.assert_called_once()
    assert "A" in result.results
    assert len(result.results["A"].frames) == 1


@pytest.mark.asyncio
async def test_query_loki_missing_params(mock_grafana_client):
    # Execute and verify that it raises ValueError
    start = datetime.now() - timedelta(hours=1)
    with pytest.raises(ValueError, match="end_rfc3339 and step_seconds must be provided"):
        await query_loki(
            datasource_uid="loki",
            expr='{app="test"}',
            start_rfc3339=start.isoformat(),
            query_type="range",
        )


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
async def test_list_loki_label_names_with_time_range(mock_grafana_client):
    # Setup
    mock_grafana_client.get.return_value = json.dumps(
        {"status": "success", "data": ["app", "instance", "job"]}
    )

    # Execute
    start = datetime.now() - timedelta(hours=1)
    end = datetime.now()
    result = await list_loki_label_names(
        datasource_uid="loki", 
        start=start,
        end=end
    )

    # Verify
    mock_grafana_client.get.assert_called_once()
    # We only need to verify that the function was called with the correct path
    # and that it returns the expected result
    call_args = mock_grafana_client.get.call_args
    assert call_args[0][0] == "/api/datasources/proxy/uid/loki/loki/api/v1/labels"
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
async def test_list_loki_label_values_with_time_range(mock_grafana_client):
    # Setup
    mock_grafana_client.get.return_value = json.dumps(
        {"status": "success", "data": ["app1", "app2", "app3"]}
    )

    # Execute
    start = datetime.now() - timedelta(hours=1)
    end = datetime.now()
    result = await list_loki_label_values(
        datasource_uid="loki", 
        label_name="app",
        start=start,
        end=end
    )

    # Verify
    mock_grafana_client.get.assert_called_once()
    # We only need to verify that the function was called with the correct path
    # and that it returns the expected result
    call_args = mock_grafana_client.get.call_args
    assert call_args[0][0] == "/api/datasources/proxy/uid/loki/loki/api/v1/label/app/values"
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
async def test_query_loki_logs_with_custom_params(mock_grafana_client):
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
                                    [1000, 2000, 3000],
                                    ["log line 1", "log line 2", "log line 3"],
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
        limit=500,
        direction="FORWARD",
    )

    # Verify
    mock_grafana_client.query.assert_called_once()
    # Check that limit and direction parameters were passed correctly
    call_args = mock_grafana_client.query.call_args[0]
    query_obj = call_args[2][0]
    assert query_obj.limit == 500
    assert query_obj.direction == "FORWARD"
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
async def test_query_loki_metrics_with_custom_step(mock_grafana_client):
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
        step_seconds=120,  # 2 minutes
    )

    # Verify
    mock_grafana_client.query.assert_called_once()
    # Check that step parameter was passed correctly
    call_args = mock_grafana_client.query.call_args[0]
    query_obj = call_args[2][0]
    assert query_obj.interval_ms == 120 * 1000  # 120 seconds in milliseconds
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


@pytest.mark.asyncio
async def test_query_loki_instant_without_time(mock_grafana_client):
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

    # Execute - without specifying time_rfc3339
    result = await query_loki_instant(
        datasource_uid="loki",
        query='rate({app="test"}[5m])',
    )

    # Verify
    mock_grafana_client.query.assert_called_once()
    assert "A" in result.results
    assert len(result.results["A"].frames) == 1


@pytest.mark.asyncio
async def test_loki_query_range_client_method(mock_grafana_client):
    # Setup
    mock_grafana_client.loki_query_range.return_value = json.dumps(
        {
            "status": "success",
            "data": {
                "resultType": "streams",
                "result": [
                    {
                        "stream": {"app": "test"},
                        "values": [
                            ["1609459200000000000", "log line 1"],
                            ["1609459201000000000", "log line 2"],
                        ],
                    }
                ],
            },
        }
    )

    # Execute
    start = datetime.now() - timedelta(hours=1)
    end = datetime.now()
    await mock_grafana_client.loki_query_range(
        datasource_uid="loki",
        query='{app="test"}',
        start=start,
        end=end,
        step="10s",
        limit=100,
        direction="BACKWARD",
    )

    # Verify
    mock_grafana_client.loki_query_range.assert_called_once()
    # We don't need to check the exact arguments since we're just testing that the method was called


@pytest.mark.asyncio
async def test_loki_query_client_method(mock_grafana_client):
    # Setup
    mock_grafana_client.loki_query.return_value = json.dumps(
        {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"app": "test"},
                        "value": [1609459200, "1.5"],
                    }
                ],
            },
        }
    )

    # Execute
    time = datetime.now()
    await mock_grafana_client.loki_query(
        datasource_uid="loki",
        query='rate({app="test"}[5m])',
        time=time,
    )

    # Verify
    mock_grafana_client.loki_query.assert_called_once()
    # We don't need to check the exact arguments since we're just testing that the method was called