"""API endpoints for Excel rendering.

POST /api/render - Upload Excel and start rendering job
GET /api/sheets/{job_id} - Get sheet list
GET /api/job/{id} - Check job status
GET /api/download/{id} - Download ZIP file
"""

import os
import re
import uuid
import json
import shutil
import asyncio
import zipfile
from datetime import datetime, timedelta
from typing import Optional, Literal, List

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse

from app.api.messages import api_error, job_message
from app.services.excel_parser import parse_excel, get_sheet_list, WorkbookModel
from app.services.paginator import paginate
from app.services.html_renderer import render_page_html
from app.services.screenshot import batch_capture, close_browser

router = APIRouter()

# Storage paths
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage")
UPLOADS_DIR = os.path.join(STORAGE_DIR, "uploads")
JOBS_DIR = os.path.join(STORAGE_DIR, "jobs")
OUTPUTS_DIR = os.path.join(STORAGE_DIR, "outputs")

# Ensure directories exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(JOBS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# Auto-cleanup: remove files older than 7 days
RETENTION = timedelta(days=7)


def cleanup_storage():
    """Remove expired uploads, jobs, and outputs on startup."""
    cutoff = datetime.now() - RETENTION
    for d in (UPLOADS_DIR, JOBS_DIR, OUTPUTS_DIR):
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            path = os.path.join(d, name)
            try:
                if datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
            except OSError:
                pass


def _save_job(job_id: str, job_data: dict):
    """Save job status to JSON file."""
    job_path = os.path.join(JOBS_DIR, f"{job_id}.json")
    with open(job_path, 'w', encoding='utf-8') as f:
        json.dump(job_data, f, ensure_ascii=False, indent=2)


def _load_job(job_id: str) -> Optional[dict]:
    """Load job status from JSON file."""
    job_path = os.path.join(JOBS_DIR, f"{job_id}.json")
    if not os.path.exists(job_path):
        return None
    with open(job_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _sanitize_filename(name: str) -> str:
    """Sanitize sheet name for use as filename."""
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Trim whitespace and dots
    name = name.strip('. ')
    # Limit length
    if len(name) > 50:
        name = name[:50]
    return name or 'Sheet'


async def _process_single_sheet(
    sheet,
    sheet_name: str,
    output_dir: str,
    header_rows: int,
    page_size: int,
    format: str,
    quality: Optional[int],
    progress_callback=None,
) -> tuple[int, List[str]]:
    """Process a single sheet and return (page_count, image_paths)."""
    # Create subdirectory for this sheet
    safe_name = _sanitize_filename(sheet_name)
    sheet_dir = os.path.join(output_dir, safe_name)
    os.makedirs(sheet_dir, exist_ok=True)

    # Paginate
    pages = paginate(sheet, header_rows, page_size)
    if not pages:
        return 0, []

    # Render HTML for each page
    html_pages = []
    for page in pages:
        html = render_page_html(page, sheet.column_widths)
        html_pages.append(html)

    # Capture screenshots with progress callback
    image_paths = await batch_capture(
        html_pages=html_pages,
        output_dir=sheet_dir,
        format=format,
        quality=quality,
        filename_prefix="",
        progress_callback=progress_callback,
    )

    return len(pages), image_paths


async def _process_render_job(
    job_id: str,
    file_path: str,
    header_rows: int,
    page_size: int,
    format: str,
    quality: Optional[int],
    sheet_indices: Optional[List[int]] = None,
):
    """Background task to process the render job.

    Args:
        sheet_indices: List of sheet indices to process. None means all sheets.
    """
    try:
        # Update status: parsing
        _save_job(job_id, {
            "job_id": job_id,
            "status": "parsing",
            **job_message("job.parsing"),
            "created_at": datetime.now().isoformat(),
        })

        # Step 1: Parse Excel
        workbook = parse_excel(file_path)

        if not workbook.sheets:
            _save_job(job_id, {
                "job_id": job_id,
                "status": "error",
                **job_message("job.empty_workbook"),
                "created_at": datetime.now().isoformat(),
            })
            return

        # Determine which sheets to process
        if sheet_indices is None:
            # Process all sheets
            sheets_to_process = list(enumerate(workbook.sheets))
        else:
            # Process selected sheets
            sheets_to_process = [
                (i, workbook.sheets[i])
                for i in sheet_indices
                if 0 <= i < len(workbook.sheets)
            ]

        if not sheets_to_process:
            _save_job(job_id, {
                "job_id": job_id,
                "status": "error",
                **job_message("job.no_sheets"),
                "created_at": datetime.now().isoformat(),
            })
            return

        # Update status: processing
        total_sheets = len(sheets_to_process)

        # Pre-calculate total pages estimate
        estimated_total_pages = 0
        for _, sheet in sheets_to_process:
            if sheet.rows:
                data_rows = len(sheet.rows) - header_rows
                if data_rows > 0:
                    estimated_total_pages += (data_rows + page_size - 1) // page_size

        _save_job(job_id, {
            "job_id": job_id,
            "status": "processing",
            **job_message("job.preparing", sheets=total_sheets),
            "total_sheets": total_sheets,
            "sheets_processed": 0,
            "current_sheet": "",
            "current_page": 0,
            "total_pages": estimated_total_pages,
            "progress": 0,
            "created_at": datetime.now().isoformat(),
        })

        # Step 2: Process each sheet
        output_dir = os.path.join(OUTPUTS_DIR, job_id)
        os.makedirs(output_dir, exist_ok=True)

        total_pages = 0
        pages_processed = 0
        all_image_paths = []
        sheets_info = []

        for sheet_idx, sheet in sheets_to_process:
            if not sheet.rows:
                continue

            sheet_name = sheet.name
            sheets_processed = len(sheets_info)

            # Calculate pages for this sheet
            data_rows = len(sheet.rows) - header_rows
            sheet_pages = (data_rows + page_size - 1) // page_size if data_rows > 0 else 0

            # Update status for current sheet
            progress = int((pages_processed / max(estimated_total_pages, 1)) * 100)
            _save_job(job_id, {
                "job_id": job_id,
                "status": "processing",
                **job_message(
                    "job.processing_sheet",
                    sheet_name=sheet_name,
                    current=sheets_processed + 1,
                    total=total_sheets,
                ),
                "total_sheets": total_sheets,
                "sheets_processed": sheets_processed,
                "current_sheet": sheet_name,
                "current_page": 0,
                "sheet_pages": sheet_pages,
                "total_pages": estimated_total_pages,
                "pages_processed": pages_processed,
                "progress": progress,
                "created_at": datetime.now().isoformat(),
            })

            # Progress callback for this sheet
            async def sheet_progress_callback(current, total):
                nonlocal pages_processed
                current_progress = int(((pages_processed + current) / max(estimated_total_pages, 1)) * 100)
                _save_job(job_id, {
                    "job_id": job_id,
                    "status": "processing",
                    **job_message(
                        "job.processing_sheet_page",
                        sheet_name=sheet_name,
                        current=current,
                        total=total,
                    ),
                    "total_sheets": total_sheets,
                    "sheets_processed": sheets_processed,
                    "current_sheet": sheet_name,
                    "current_page": current,
                    "sheet_pages": total,
                    "total_pages": estimated_total_pages,
                    "pages_processed": pages_processed + current,
                    "progress": min(current_progress, 99),
                    "created_at": datetime.now().isoformat(),
                })

            # Process the sheet
            page_count, image_paths = await _process_single_sheet(
                sheet=sheet,
                sheet_name=sheet_name,
                output_dir=output_dir,
                header_rows=header_rows,
                page_size=page_size,
                format=format,
                quality=quality,
                progress_callback=sheet_progress_callback,
            )

            if page_count > 0:
                total_pages += page_count
                pages_processed += page_count
                all_image_paths.extend(image_paths)
                sheets_info.append({
                    "index": sheet_idx,
                    "name": sheet_name,
                    "pages": page_count,
                    "rows": len(sheet.rows),
                })

        if total_pages == 0:
            _save_job(job_id, {
                "job_id": job_id,
                "status": "error",
                **job_message("job.empty_sheets"),
                "created_at": datetime.now().isoformat(),
            })
            return

        # Update status: zipping
        _save_job(job_id, {
            "job_id": job_id,
            "status": "zipping",
            **job_message("job.zipping"),
            "total_pages": total_pages,
            "created_at": datetime.now().isoformat(),
        })

        # Step 3: Create ZIP with sheet subdirectories
        zip_path = os.path.join(OUTPUTS_DIR, f"{job_id}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for sheet_info in sheets_info:
                safe_name = _sanitize_filename(sheet_info["name"])
                sheet_dir = os.path.join(output_dir, safe_name)
                if os.path.exists(sheet_dir):
                    for img_file in sorted(os.listdir(sheet_dir)):
                        img_path = os.path.join(sheet_dir, img_file)
                        # Add with sheet folder prefix
                        arcname = f"{safe_name}/{img_file}"
                        zf.write(img_path, arcname)

        # Update status: completed
        _save_job(job_id, {
            "job_id": job_id,
            "status": "completed",
            **job_message(
                "job.completed",
                sheets=len(sheets_info),
                pages=total_pages,
            ),
            "total_pages": total_pages,
            "total_sheets": len(sheets_info),
            "sheets": sheets_info,
            "download_url": f"/api/download/{job_id}",
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
        })

    except Exception:
        import traceback
        traceback.print_exc()
        _save_job(job_id, {
            "job_id": job_id,
            "status": "error",
            **job_message("job.failed"),
            "created_at": datetime.now().isoformat(),
        })
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


@router.get("/sheets/{job_id}")
async def get_sheets_for_job(job_id: str):
    """Get list of sheets in the uploaded Excel file."""
    job = _load_job(job_id)
    if not job:
        raise api_error(404, "job.not_found")

    file_path = job.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise api_error(400, "file.not_found")

    try:
        sheets = get_sheet_list(file_path)
        return {"sheets": sheets}
    except Exception:
        raise api_error(500, "file.parse_failed")


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload Excel file and get sheet list.

    Returns job_id and sheet list for selection.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.xlsx'):
        raise api_error(400, "file.unsupported_type", supported=".xlsx")

    # Generate job ID
    job_id = str(uuid.uuid4())[:8]

    # Save uploaded file
    upload_path = os.path.join(UPLOADS_DIR, f"{job_id}_{file.filename}")
    content = await file.read()
    with open(upload_path, 'wb') as f:
        f.write(content)

    # Quick parse to get sheet list (without parsing all data)
    try:
        sheets = get_sheet_list(upload_path)
    except Exception:
        os.remove(upload_path)
        raise api_error(400, "file.parse_failed")

    # Save job info
    _save_job(job_id, {
        "job_id": job_id,
        "status": "uploaded",
        **job_message("job.uploaded"),
        "filename": file.filename,
        "file_path": upload_path,
        "sheets": sheets,
        "created_at": datetime.now().isoformat(),
    })

    return {
        "job_id": job_id,
        "filename": file.filename,
        "sheets": sheets,
    }


@router.post("/render")
async def create_render_job(
    job_id: str = Form(...),
    header_rows: int = Form(1, ge=0, le=100),
    page_size: int = Form(10, ge=1, le=1000),
    format: Literal['png', 'jpg'] = Form('png'),
    quality: Optional[int] = Form(None, ge=1, le=100),
    sheet_indices: str = Form("all"),
):
    """Create a new render job.

    Args:
        job_id: Job ID from upload endpoint
        sheet_indices: Comma-separated indices or "all"
    """
    # Load job info
    job = _load_job(job_id)
    if not job:
        raise api_error(404, "job.not_found")

    file_path = job.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise api_error(400, "file.not_found")

    # Parse sheet indices
    if sheet_indices == "all":
        indices = None  # Process all sheets
    else:
        try:
            indices = [int(x.strip()) for x in sheet_indices.split(",")]
        except ValueError:
            raise api_error(400, "job.invalid_sheet_indices")

    # Update job status
    _save_job(job_id, {
        **job,
        "status": "queued",
        **job_message("job.queued"),
        "header_rows": header_rows,
        "page_size": page_size,
        "format": format,
        "sheet_indices": sheet_indices,
    })

    # Start background processing
    asyncio.create_task(_process_render_job(
        job_id=job_id,
        file_path=file_path,
        header_rows=header_rows,
        page_size=page_size,
        format=format,
        quality=quality,
        sheet_indices=indices,
    ))

    return {
        "job_id": job_id,
        "status": "queued",
        **job_message("job.queued"),
    }


@router.post("/render-direct")
async def create_render_job_direct(
    file: UploadFile = File(...),
    header_rows: int = Form(1, ge=0, le=100),
    page_size: int = Form(10, ge=1, le=1000),
    format: Literal['png', 'jpg'] = Form('png'),
    quality: Optional[int] = Form(None, ge=1, le=100),
    sheet_indices: str = Form("all"),
):
    """Direct render without sheet selection (legacy endpoint)."""
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.xlsx'):
        raise api_error(400, "file.unsupported_type", supported=".xlsx")

    # Generate job ID
    job_id = str(uuid.uuid4())[:8]

    # Save uploaded file
    upload_path = os.path.join(UPLOADS_DIR, f"{job_id}_{file.filename}")
    content = await file.read()
    with open(upload_path, 'wb') as f:
        f.write(content)

    # Parse sheet indices
    if sheet_indices == "all":
        indices = None
    else:
        try:
            indices = [int(x.strip()) for x in sheet_indices.split(",")]
        except ValueError:
            raise api_error(400, "job.invalid_sheet_indices")

    # Save initial job status
    _save_job(job_id, {
        "job_id": job_id,
        "status": "queued",
        **job_message("job.queued"),
        "filename": file.filename,
        "file_path": upload_path,
        "header_rows": header_rows,
        "page_size": page_size,
        "format": format,
        "created_at": datetime.now().isoformat(),
    })

    # Start background processing
    asyncio.create_task(_process_render_job(
        job_id=job_id,
        file_path=upload_path,
        header_rows=header_rows,
        page_size=page_size,
        format=format,
        quality=quality,
        sheet_indices=indices,
    ))

    return {
        "job_id": job_id,
        "status": "queued",
        **job_message("job.queued"),
    }


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a render job."""
    job = _load_job(job_id)
    if not job:
        raise api_error(404, "job.not_found")
    return job


@router.get("/download/{job_id}")
async def download_result(job_id: str):
    """Download the ZIP file for a completed job."""
    job = _load_job(job_id)
    if not job:
        raise api_error(404, "job.not_found")

    if job.get("status") != "completed":
        raise api_error(400, "job.not_completed")

    zip_path = os.path.join(OUTPUTS_DIR, f"{job_id}.zip")
    if not os.path.exists(zip_path):
        raise api_error(404, "output.not_found")

    # Generate filename based on sheets processed
    sheets = job.get("sheets", [])
    original_filename = job.get("filename", "result.xlsx").replace('.xlsx', '')

    if len(sheets) == 1:
        # Single sheet: use sheet name
        download_name = f"{sheets[0]['name']}.zip"
    elif len(sheets) > 1:
        # Multiple sheets: use original filename
        download_name = f"{original_filename}_sheets.zip"
    else:
        download_name = f"{original_filename}_images.zip"

    return FileResponse(
        path=zip_path,
        filename=download_name,
        media_type="application/zip",
    )


@router.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its associated files."""
    job = _load_job(job_id)
    if not job:
        raise api_error(404, "job.not_found")

    # Delete job file
    job_path = os.path.join(JOBS_DIR, f"{job_id}.json")
    if os.path.exists(job_path):
        os.remove(job_path)

    # Delete uploaded file
    file_path = job.get("file_path")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    # Delete output directory
    output_dir = os.path.join(OUTPUTS_DIR, job_id)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    # Delete ZIP
    zip_path = os.path.join(OUTPUTS_DIR, f"{job_id}.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    return {"status": "deleted"}


@router.get("/formats")
async def get_supported_formats():
    """Get list of supported output formats."""
    return {
        "formats": [
            {"id": "png", "name": "PNG", "description_code": "format.png"},
            {"id": "jpg", "name": "JPG", "description_code": "format.jpg"},
        ]
    }
