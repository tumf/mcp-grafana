import itertools
import re
from datetime import datetime
from typing import Literal, Any

from mcp.server import FastMCP

from ..client import grafana_client
from ..grafana_types import (
    DatasourceRef,
    DSQueryResponse,
    Query,
    ResponseWrapper,
    Selector,
)


LokiQueryType = Literal["range", "instant"]


async def query_loki(
    datasource_uid: str,
    expr: str,
    start_rfc3339: str,
    end_rfc3339: str | None = None,
    step_seconds: int | None = None,
    query_type: LokiQueryType = "range",
) -> DSQueryResponse:
    """
    Query Loki using a range or instant request.

    # Parameters.

    datasource_uid: The uid of the datasource to query.
    expr: The LogQL expression to query.
    start_rfc3339: The start time in RFC3339 format.
    end_rfc3339: The end time in RFC3339 format. Ignored if `query_type` is 'instant'.
    step_seconds: The time series step size in seconds. Ignored if `query_type` is 'instant'.
    query_type: The type of query to use. Either 'range' or 'instant'.
    """
    if query_type == "range" and (end_rfc3339 is None or step_seconds is None):
        raise ValueError(
            "end_rfc3339 and step_seconds must be provided when query_type is 'range'"
        )
    start = datetime.fromisoformat(start_rfc3339)
    end = datetime.fromisoformat(end_rfc3339) if end_rfc3339 is not None else start
    interval_ms = step_seconds * 1000 if step_seconds is not None else None
    query = Query(
        refId="A",
        datasource=DatasourceRef(
            uid=datasource_uid,
            type="loki",
        ),
        queryType=query_type,
        expr=expr,  # type: ignore
        intervalMs=interval_ms,
    )
    response = await grafana_client.query(start, end, [query])
    return DSQueryResponse.model_validate_json(response)


async def list_loki_label_names(
    datasource_uid: str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[str]:
    """
    List the label names in a Loki datasource, optionally within the given time range.

    # Parameters.

    datasource_uid: The uid of the Grafana datasource to query.
    start: Optionally, the start time of the time range to filter the results by.
    end: Optionally, the end time of the time range to filter the results by.
    """
    params = {}
    if start is not None:
        params["start"] = start.isoformat()
    if end is not None:
        params["end"] = end.isoformat()

    response = await grafana_client.get(
        f"/api/datasources/proxy/uid/{datasource_uid}/loki/api/v1/labels",
        params,
    )
    return ResponseWrapper[list[str]].model_validate_json(response).data


async def list_loki_label_values(
    datasource_uid: str,
    label_name: str,
    start: datetime | None = None,
    end: datetime | None = None,
):
    """
    Get the values of a label in Loki.

    # Parameters.

    datasource_uid: The uid of the Grafana datasource to query.
    label_name: The name of the label to query.
    start: Optionally, the start time of the query.
    end: Optionally, the end time of the query.
    """
    params = {}
    if start is not None:
        params["start"] = start.isoformat()
    if end is not None:
        params["end"] = end.isoformat()

    response = await grafana_client.get(
        f"/api/datasources/proxy/uid/{datasource_uid}/loki/api/v1/label/{label_name}/values",
        params,
    )
    return ResponseWrapper[list[str]].model_validate_json(response).data


async def query_loki_logs(
    datasource_uid: str,
    query: str,
    start_rfc3339: str,
    end_rfc3339: str,
    limit: int = 100,
    direction: Literal["BACKWARD", "FORWARD"] = "BACKWARD",
) -> DSQueryResponse:
    """
    Query Loki for logs.

    # Parameters.

    datasource_uid: The uid of the datasource to query.
    query: The LogQL query to execute.
    start_rfc3339: The start time in RFC3339 format.
    end_rfc3339: The end time in RFC3339 format.
    limit: The maximum number of log lines to return.
    direction: The direction to query logs in. Either 'BACKWARD' (newest first) or 'FORWARD' (oldest first).
    """
    start = datetime.fromisoformat(start_rfc3339)
    end = datetime.fromisoformat(end_rfc3339)
    
    # We can use either the generic query method or the Loki-specific method
    # Using the generic query method for consistency with other tools
    query_obj = Query(
        refId="A",
        datasource=DatasourceRef(
            uid=datasource_uid,
            type="loki",
        ),
        queryType="range",
        expr=query,  # type: ignore
        limit=limit,  # type: ignore
        direction=direction,  # type: ignore
    )
    response = await grafana_client.query(start, end, [query_obj])
    return DSQueryResponse.model_validate_json(response)


async def query_loki_metrics(
    datasource_uid: str,
    query: str,
    start_rfc3339: str,
    end_rfc3339: str,
    step_seconds: int = 60,
) -> DSQueryResponse:
    """
    Query Loki for metrics using a LogQL metric query.

    # Parameters.

    datasource_uid: The uid of the datasource to query.
    query: The LogQL metric query to execute (e.g., 'rate({app="foo"}[5m])').
    start_rfc3339: The start time in RFC3339 format.
    end_rfc3339: The end time in RFC3339 format.
    step_seconds: The step size in seconds for the query resolution.
    """
    start = datetime.fromisoformat(start_rfc3339)
    end = datetime.fromisoformat(end_rfc3339)
    
    # For metric queries, we use the same pattern as Prometheus queries
    query_obj = Query(
        refId="A",
        datasource=DatasourceRef(
            uid=datasource_uid,
            type="loki",
        ),
        queryType="range",
        expr=query,  # type: ignore
        intervalMs=step_seconds * 1000,
    )
    response = await grafana_client.query(start, end, [query_obj])
    return DSQueryResponse.model_validate_json(response)


async def query_loki_instant(
    datasource_uid: str,
    query: str,
    time_rfc3339: str | None = None,
) -> DSQueryResponse:
    """
    Query Loki for an instant metric query at a specific time.

    # Parameters.

    datasource_uid: The uid of the datasource to query.
    query: The LogQL metric query to execute.
    time_rfc3339: The time in RFC3339 format to query at. If not provided, the current time is used.
    """
    time = datetime.fromisoformat(time_rfc3339) if time_rfc3339 else datetime.now()
    
    query_obj = Query(
        refId="A",
        datasource=DatasourceRef(
            uid=datasource_uid,
            type="loki",
        ),
        queryType="instant",
        expr=query,  # type: ignore
    )
    response = await grafana_client.query(time, time, [query_obj])
    return DSQueryResponse.model_validate_json(response)


def add_tools(mcp: FastMCP):
    mcp.add_tool(query_loki)
    mcp.add_tool(list_loki_label_names)
    mcp.add_tool(list_loki_label_values)
    mcp.add_tool(query_loki_logs)
    mcp.add_tool(query_loki_metrics)
    mcp.add_tool(query_loki_instant)