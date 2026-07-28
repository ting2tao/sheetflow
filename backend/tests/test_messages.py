import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException
from fastapi import UploadFile

from app.api.messages import api_error, job_message
from app.api import render
from app.services.excel_parser import SheetModel, WorkbookModel


def test_job_message_returns_exact_payload_without_params():
    assert job_message("job.parsing") == {
        "message_code": "job.parsing",
        "message_params": {},
    }


def test_job_message_returns_exact_payload_with_params():
    assert job_message("job.completed", sheets=2, pages=7) == {
        "message_code": "job.completed",
        "message_params": {"sheets": 2, "pages": 7},
    }


def test_api_error_returns_http_exception_with_structured_detail():
    error = api_error(400, "file.unsupported_type", supported=".xlsx")

    assert isinstance(error, HTTPException)
    assert error.status_code == 400
    assert error.detail == {
        "code": "file.unsupported_type",
        "params": {"supported": ".xlsx"},
    }


def _run(coro):
    return asyncio.run(coro)


def _assert_error(coro, status_code, code, params=None, server_text=None):
    with pytest.raises(HTTPException) as caught:
        _run(coro)

    assert caught.value.status_code == status_code
    assert caught.value.detail == {"code": code, "params": params or {}}
    if server_text:
        assert server_text not in repr(caught.value.detail)


def _capture_jobs(monkeypatch):
    saved = []
    monkeypatch.setattr(render, "_save_job", lambda job_id, data: saved.append(data))
    return saved


def test_render_job_emits_localizable_lifecycle_messages(monkeypatch, tmp_path):
    upload = tmp_path / "book.xlsx"
    upload.write_bytes(b"workbook")
    sheet = SheetModel(name="Revenue", rows=[[], []])
    saved = _capture_jobs(monkeypatch)

    monkeypatch.setattr(
        render, "parse_excel", lambda path: WorkbookModel(sheets=[sheet])
    )
    monkeypatch.setattr(render, "OUTPUTS_DIR", str(tmp_path / "outputs"))

    async def process_sheet(**kwargs):
        await kwargs["progress_callback"](1, 1)
        return 1, []

    monkeypatch.setattr(render, "_process_single_sheet", process_sheet)

    _run(
        render._process_render_job(
            job_id="job-1",
            file_path=str(upload),
            header_rows=1,
            page_size=10,
            format="png",
            quality=None,
        )
    )

    assert [(job["status"], job["message_code"]) for job in saved] == [
        ("parsing", "job.parsing"),
        ("processing", "job.preparing"),
        ("processing", "job.processing_sheet"),
        ("processing", "job.processing_sheet_page"),
        ("zipping", "job.zipping"),
        ("completed", "job.completed"),
    ]
    assert saved[1]["message_params"] == {"sheets": 1}
    assert saved[2]["message_params"] == {
        "sheet_name": "Revenue",
        "current": 1,
        "total": 1,
    }
    assert saved[3]["message_params"] == {
        "sheet_name": "Revenue",
        "current": 1,
        "total": 1,
    }
    assert saved[-1]["message_params"] == {"sheets": 1, "pages": 1}
    assert all("message" not in job for job in saved)


@pytest.mark.parametrize(
    ("workbook", "sheet_indices", "expected_code"),
    [
        (WorkbookModel(), None, "job.empty_workbook"),
        (
            WorkbookModel(sheets=[SheetModel(name="Only", rows=[[]])]),
            [4],
            "job.no_sheets",
        ),
        (
            WorkbookModel(sheets=[SheetModel(name="Empty", rows=[])]),
            None,
            "job.empty_sheets",
        ),
    ],
)
def test_render_job_maps_empty_states(
    monkeypatch, tmp_path, workbook, sheet_indices, expected_code
):
    upload = tmp_path / f"{expected_code}.xlsx"
    upload.write_bytes(b"workbook")
    saved = _capture_jobs(monkeypatch)
    monkeypatch.setattr(render, "parse_excel", lambda path: workbook)
    monkeypatch.setattr(render, "OUTPUTS_DIR", str(tmp_path / "outputs"))

    _run(
        render._process_render_job(
            job_id="job-empty",
            file_path=str(upload),
            header_rows=1,
            page_size=10,
            format="png",
            quality=None,
            sheet_indices=sheet_indices,
        )
    )

    assert saved[-1]["status"] == "error"
    assert saved[-1]["message_code"] == expected_code
    assert saved[-1]["message_params"] == {}
    assert "message" not in saved[-1]


def test_render_job_failure_does_not_persist_exception_text(monkeypatch, tmp_path):
    upload = tmp_path / "secret.xlsx"
    upload.write_bytes(b"workbook")
    saved = _capture_jobs(monkeypatch)
    monkeypatch.setattr(
        render,
        "parse_excel",
        lambda path: (_ for _ in ()).throw(RuntimeError("sensitive server path")),
    )

    _run(
        render._process_render_job(
            job_id="job-failed",
            file_path=str(upload),
            header_rows=1,
            page_size=10,
            format="png",
            quality=None,
        )
    )

    assert saved[-1] == {
        "job_id": "job-failed",
        "status": "error",
        "message_code": "job.failed",
        "message_params": {},
        "created_at": saved[-1]["created_at"],
    }
    assert "sensitive server path" not in repr(saved[-1])


@pytest.mark.parametrize(
    "endpoint",
    [
        render.get_sheets_for_job,
        render.create_render_job,
        render.get_job_status,
        render.download_result,
        render.delete_job,
    ],
)
def test_job_endpoints_map_missing_job_error(monkeypatch, endpoint):
    monkeypatch.setattr(render, "_load_job", lambda job_id: None)

    _assert_error(endpoint("missing"), 404, "job.not_found")


@pytest.mark.parametrize(
    "endpoint",
    [render.get_sheets_for_job, render.create_render_job],
)
def test_job_endpoints_map_missing_upload_file_error(monkeypatch, endpoint):
    monkeypatch.setattr(
        render, "_load_job", lambda job_id: {"file_path": "/does/not/exist"}
    )

    _assert_error(endpoint("missing-file"), 400, "file.not_found")


@pytest.mark.parametrize(
    ("endpoint_name", "status_code"),
    [("get_sheets", 500), ("upload", 400)],
)
def test_parse_errors_are_structured_and_sanitized(
    monkeypatch, tmp_path, endpoint_name, status_code
):
    upload = tmp_path / "book.xlsx"
    upload.write_bytes(b"workbook")
    server_text = f"sensitive parser text from {endpoint_name}"
    monkeypatch.setattr(
        render,
        "get_sheet_list",
        lambda path: (_ for _ in ()).throw(RuntimeError(server_text)),
    )

    if endpoint_name == "get_sheets":
        monkeypatch.setattr(
            render, "_load_job", lambda job_id: {"file_path": str(upload)}
        )
        request = render.get_sheets_for_job("job-1")
    else:
        monkeypatch.setattr(render, "UPLOADS_DIR", str(tmp_path))
        request = render.upload_file(
            UploadFile(file=BytesIO(b"broken"), filename="invalid.xlsx")
        )

    _assert_error(
        request,
        status_code,
        "file.parse_failed",
        server_text=server_text,
    )


@pytest.mark.parametrize(
    "endpoint",
    [render.upload_file, render.create_render_job_direct],
)
def test_upload_endpoints_map_unsupported_file_type(endpoint):
    _assert_error(
        endpoint(UploadFile(file=BytesIO(b"csv"), filename="book.csv")),
        400,
        "file.unsupported_type",
        {"supported": ".xlsx"},
    )


def test_upload_persists_uploaded_message(monkeypatch, tmp_path):
    saved = _capture_jobs(monkeypatch)
    monkeypatch.setattr(render, "UPLOADS_DIR", str(tmp_path))
    monkeypatch.setattr(render.uuid, "uuid4", lambda: "upload-job")
    monkeypatch.setattr(
        render,
        "get_sheet_list",
        lambda path: [{"index": 0, "name": "Sheet1", "rows": 2, "columns": 1}],
    )
    upload = UploadFile(file=BytesIO(b"workbook"), filename="book.xlsx")

    response = _run(render.upload_file(upload))

    assert saved[0]["message_code"] == "job.uploaded"
    assert saved[0]["message_params"] == {}
    assert "message" not in saved[0]
    assert response == {
        "job_id": "upload-j",
        "filename": "book.xlsx",
        "sheets": [{"index": 0, "name": "Sheet1", "rows": 2, "columns": 1}],
    }


@pytest.mark.parametrize("endpoint_name", ["create", "direct"])
def test_render_endpoints_map_invalid_sheet_indices(
    monkeypatch, tmp_path, endpoint_name
):
    monkeypatch.setattr(render, "UPLOADS_DIR", str(tmp_path))
    upload_path = tmp_path / "book.xlsx"
    upload_path.write_bytes(b"workbook")

    if endpoint_name == "create":
        monkeypatch.setattr(
            render,
            "_load_job",
            lambda job_id: {"job_id": job_id, "file_path": str(upload_path)},
        )
        request = render.create_render_job(
            job_id="job-1", sheet_indices="wrong"
        )
    else:
        request = render.create_render_job_direct(
            UploadFile(file=BytesIO(b"workbook"), filename="book.xlsx"),
            sheet_indices="wrong",
        )

    _assert_error(request, 400, "job.invalid_sheet_indices")


def test_create_render_job_persists_and_returns_queued_payload(
    monkeypatch, tmp_path
):
    upload = tmp_path / "book.xlsx"
    upload.write_bytes(b"workbook")
    job = {"job_id": "job-1", "file_path": str(upload)}
    monkeypatch.setattr(render, "_load_job", lambda job_id: job)

    saved = _capture_jobs(monkeypatch)

    def discard_task(coro):
        coro.close()

    monkeypatch.setattr(render.asyncio, "create_task", discard_task)
    response = _run(
        render.create_render_job(
            job_id="job-1",
            header_rows=1,
            page_size=10,
            format="png",
            quality=None,
            sheet_indices="all",
        )
    )

    assert saved[0]["message_code"] == "job.queued"
    assert saved[0]["message_params"] == {}
    assert "message" not in saved[0]
    assert response == {
        "job_id": "job-1",
        "status": "queued",
        "message_code": "job.queued",
        "message_params": {},
    }


def test_render_direct_persists_and_returns_queued_payload(monkeypatch, tmp_path):
    monkeypatch.setattr(render, "UPLOADS_DIR", str(tmp_path))
    monkeypatch.setattr(render.uuid, "uuid4", lambda: "direct-job")

    saved = _capture_jobs(monkeypatch)

    def discard_task(coro):
        coro.close()

    monkeypatch.setattr(render.asyncio, "create_task", discard_task)
    upload = UploadFile(file=BytesIO(b"xlsx"), filename="book.xlsx")
    response = _run(
        render.create_render_job_direct(
            upload,
            header_rows=1,
            page_size=10,
            format="png",
            quality=None,
            sheet_indices="all",
        )
    )

    assert saved[0]["message_code"] == "job.queued"
    assert saved[0]["message_params"] == {}
    assert "message" not in saved[0]
    assert response == {
        "job_id": "direct-j",
        "status": "queued",
        "message_code": "job.queued",
        "message_params": {},
    }


@pytest.mark.parametrize(
    ("job", "code"),
    [
        ({"status": "queued"}, "job.not_completed"),
        ({"status": "completed", "sheets": []}, "output.not_found"),
    ],
)
def test_download_maps_job_state_errors(
    monkeypatch, tmp_path, job, code
):
    monkeypatch.setattr(render, "_load_job", lambda job_id: job)
    monkeypatch.setattr(render, "OUTPUTS_DIR", str(tmp_path))
    status_code = 400 if code == "job.not_completed" else 404

    _assert_error(render.download_result("job-1"), status_code, code)


def test_delete_returns_status_payload(monkeypatch, tmp_path):
    monkeypatch.setattr(render, "JOBS_DIR", str(tmp_path / "jobs"))
    monkeypatch.setattr(render, "OUTPUTS_DIR", str(tmp_path / "outputs"))
    monkeypatch.setattr(render, "_load_job", lambda job_id: {"job_id": job_id})

    assert _run(render.delete_job("job-1")) == {"status": "deleted"}


def test_formats_return_localizable_description_codes():
    assert _run(render.get_supported_formats()) == {
        "formats": [
            {"id": "png", "name": "PNG", "description_code": "format.png"},
            {"id": "jpg", "name": "JPG", "description_code": "format.jpg"},
        ]
    }
