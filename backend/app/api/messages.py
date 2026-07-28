"""Structured, localizable API message helpers."""

from typing import Any

from fastapi import HTTPException


def job_message(code: str, **params: Any) -> dict:
    """Build the message fields persisted with and returned for a render job."""
    return {
        "message_code": code,
        "message_params": params,
    }


def api_error(status_code: int, code: str, **params: Any) -> HTTPException:
    """Build an HTTP error whose detail can be localized by the client."""
    return HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "params": params,
        },
    )
