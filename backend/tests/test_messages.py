import asyncio
import inspect
import re
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


def _assert_error(coro, status_code, code, params=None):
    with pytest.raises(HTTPException) as caught:
        _run(coro)

    assert caught.value.status_code == status_code
    assert caught.value.detail == {"code": code, "params": params or {}}


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


def test_get_sheets_maps_missing_job_and_file_errors(monkeypatch):
    monkeypatch.setattr(render, "_load_job", lambda job_id: None)
    _assert_error(
        render.get_sheets_for_job("missing"), 404, "job.not_found"
    )

    monkeypatch.setattr(
        render, "_load_job", lambda job_id: {"file_path": "/does/not/exist"}
    )
    _assert_error(
        render.get_sheets_for_job("missing-file"), 400, "file.not_found"
    )


def test_get_sheets_parse_error_is_structured_and_sanitized(monkeypatch, tmp_path):
    upload = tmp_path / "book.xlsx"
    upload.write_bytes(b"workbook")
    monkeypatch.setattr(
        render, "_load_job", lambda job_id: {"file_path": str(upload)}
    )
    monkeypatch.setattr(
        render,
        "get_sheet_list",
        lambda path: (_ for _ in ()).throw(RuntimeError("sensitive parser text")),
    )

    _assert_error(
        render.get_sheets_for_job("job-1"), 500, "file.parse_failed"
    )


def test_upload_maps_file_type_and_parse_errors(monkeypatch, tmp_path):
    unsupported = UploadFile(file=BytesIO(b"csv"), filename="book.csv")
    _assert_error(
        render.upload_file(unsupported),
        400,
        "file.unsupported_type",
        {"supported": ".xlsx"},
    )

    monkeypatch.setattr(render, "UPLOADS_DIR", str(tmp_path))
    monkeypatch.setattr(render.uuid, "uuid4", lambda: "upload-job")
    monkeypatch.setattr(
        render,
        "get_sheet_list",
        lambda path: (_ for _ in ()).throw(RuntimeError("private parse failure")),
    )
    invalid = UploadFile(file=BytesIO(b"broken"), filename="book.xlsx")
    _assert_error(render.upload_file(invalid), 400, "file.parse_failed")


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


def test_create_render_job_maps_errors_and_queued_payloads(monkeypatch, tmp_path):
    monkeypatch.setattr(render, "_load_job", lambda job_id: None)
    _assert_error(
        render.create_render_job(job_id="missing"),
        404,
        "job.not_found",
    )

    monkeypatch.setattr(
        render, "_load_job", lambda job_id: {"file_path": "/does/not/exist"}
    )
    _assert_error(
        render.create_render_job(job_id="missing-file"),
        400,
        "file.not_found",
    )

    upload = tmp_path / "book.xlsx"
    upload.write_bytes(b"workbook")
    job = {"job_id": "job-1", "file_path": str(upload)}
    monkeypatch.setattr(render, "_load_job", lambda job_id: job)
    _assert_error(
        render.create_render_job(job_id="job-1", sheet_indices="wrong"),
        400,
        "job.invalid_sheet_indices",
    )

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


def test_render_direct_maps_errors_and_queued_payloads(monkeypatch, tmp_path):
    unsupported = UploadFile(file=BytesIO(b"csv"), filename="book.csv")
    _assert_error(
        render.create_render_job_direct(unsupported),
        400,
        "file.unsupported_type",
        {"supported": ".xlsx"},
    )

    monkeypatch.setattr(render, "UPLOADS_DIR", str(tmp_path))
    monkeypatch.setattr(render.uuid, "uuid4", lambda: "direct-job")
    invalid_indices = UploadFile(file=BytesIO(b"xlsx"), filename="book.xlsx")
    _assert_error(
        render.create_render_job_direct(
            invalid_indices, sheet_indices="wrong"
        ),
        400,
        "job.invalid_sheet_indices",
    )

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


def test_get_job_download_and_delete_map_errors(monkeypatch, tmp_path):
    monkeypatch.setattr(render, "_load_job", lambda job_id: None)

    _assert_error(render.get_job_status("missing"), 404, "job.not_found")
    _assert_error(render.download_result("missing"), 404, "job.not_found")
    _assert_error(render.delete_job("missing"), 404, "job.not_found")

    monkeypatch.setattr(render, "_load_job", lambda job_id: {"status": "queued"})
    _assert_error(
        render.download_result("job-1"), 400, "job.not_completed"
    )

    monkeypatch.setattr(
        render,
        "_load_job",
        lambda job_id: {"status": "completed", "sheets": []},
    )
    monkeypatch.setattr(render, "OUTPUTS_DIR", str(tmp_path))
    _assert_error(
        render.download_result("job-1"), 404, "output.not_found"
    )


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


def test_render_module_contains_no_localized_business_payloads():
    source = inspect.getsource(render)

    assert re.search(r"[\u4e00-\u9fff]", source) is None
    assert '"message"' not in source
    assert "HTTPException" not in source
    assert "str(e)" not in source
