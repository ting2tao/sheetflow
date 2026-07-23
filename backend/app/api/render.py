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
import asyncio
import zipfile
from datetime import datetime
from typing import Optional, Literal, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from app.services.excel_parser import parse_excel, WorkbookModel
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

    # Capture screenshots
    image_paths = await batch_capture(
        html_pages=html_pages,
        output_dir=sheet_dir,
        format=format,
        quality=quality,
        filename_prefix="",
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
            "message": "正在解析Excel文件...",
            "created_at": datetime.now().isoformat(),
        })

        # Step 1: Parse Excel
        workbook = parse_excel(file_path)

        if not workbook.sheets:
            _save_job(job_id, {
                "job_id": job_id,
                "status": "error",
                "message": "Excel文件为空或无法解析",
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
                "message": "没有找到要处理的Sheet",
                "created_at": datetime.now().isoformat(),
            })
            return

        # Update status: processing
        total_sheets = len(sheets_to_process)
        _save_job(job_id, {
            "job_id": job_id,
            "status": "processing",
            "message": f"正在处理 {total_sheets} 个Sheet...",
            "total_sheets": total_sheets,
            "sheets_processed": 0,
            "created_at": datetime.now().isoformat(),
        })

        # Step 2: Process each sheet
        output_dir = os.path.join(OUTPUTS_DIR, job_id)
        os.makedirs(output_dir, exist_ok=True)

        total_pages = 0
        all_image_paths = []
        sheets_info = []

        for sheet_idx, sheet in sheets_to_process:
            if not sheet.rows:
                continue

            # Update status for current sheet
            _save_job(job_id, {
                "job_id": job_id,
                "status": "processing",
                "message": f"正在处理: {sheet.name} ({len(sheets_info) + 1}/{total_sheets})",
                "total_sheets": total_sheets,
                "sheets_processed": len(sheets_info),
                "current_sheet": sheet.name,
                "created_at": datetime.now().isoformat(),
            })

            # Process the sheet
            page_count, image_paths = await _process_single_sheet(
                sheet=sheet,
                sheet_name=sheet.name,
                output_dir=output_dir,
                header_rows=header_rows,
                page_size=page_size,
                format=format,
                quality=quality,
            )

            if page_count > 0:
                total_pages += page_count
                all_image_paths.extend(image_paths)
                sheets_info.append({
                    "index": sheet_idx,
                    "name": sheet.name,
                    "pages": page_count,
                    "rows": len(sheet.rows),
                })

        if total_pages == 0:
            _save_job(job_id, {
                "job_id": job_id,
                "status": "error",
                "message": "所有Sheet都没有数据",
                "created_at": datetime.now().isoformat(),
            })
            return

        # Update status: zipping
        _save_job(job_id, {
            "job_id": job_id,
            "status": "zipping",
            "message": "正在打包ZIP...",
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
            "message": f"完成！共处理 {len(sheets_info)} 个Sheet，生成 {total_pages} 张图片",
            "total_pages": total_pages,
            "total_sheets": len(sheets_info),
            "sheets": sheets_info,
            "download_url": f"/api/download/{job_id}",
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        _save_job(job_id, {
            "job_id": job_id,
            "status": "error",
            "message": f"处理失败: {str(e)}",
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
async def get_sheet_list(job_id: str):
    """Get list of sheets in the uploaded Excel file."""
    job = _load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    file_path = job.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="文件不存在，请重新上传")

    try:
        workbook = parse_excel(file_path)
        sheets = []
        for i, sheet in enumerate(workbook.sheets):
            sheets.append({
                "index": i,
                "name": sheet.name,
                "rows": len(sheet.rows),
                "columns": sheet.max_col,
            })
        return {"sheets": sheets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload Excel file and get sheet list.

    Returns job_id and sheet list for selection.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(
            status_code=400,
            detail="仅支持 .xlsx 格式的Excel文件"
        )

    # Generate job ID
    job_id = str(uuid.uuid4())[:8]

    # Save uploaded file
    upload_path = os.path.join(UPLOADS_DIR, f"{job_id}_{file.filename}")
    content = await file.read()
    with open(upload_path, 'wb') as f:
        f.write(content)

    # Parse to get sheet list
    try:
        workbook = parse_excel(upload_path)
        sheets = []
        for i, sheet in enumerate(workbook.sheets):
            sheets.append({
                "index": i,
                "name": sheet.name,
                "rows": len(sheet.rows),
                "columns": sheet.max_col,
            })
    except Exception as e:
        os.remove(upload_path)
        raise HTTPException(status_code=400, detail=f"Excel解析失败: {str(e)}")

    # Save job info
    _save_job(job_id, {
        "job_id": job_id,
        "status": "uploaded",
        "message": "文件已上传，请选择要处理的Sheet",
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
        raise HTTPException(status_code=404, detail="任务不存在，请重新上传文件")

    file_path = job.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="文件不存在，请重新上传")

    # Parse sheet indices
    if sheet_indices == "all":
        indices = None  # Process all sheets
    else:
        try:
            indices = [int(x.strip()) for x in sheet_indices.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="sheet_indices 格式错误")

    # Update job status
    _save_job(job_id, {
        **job,
        "status": "queued",
        "message": "任务已创建，等待处理...",
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
        "message": "任务已创建",
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
        raise HTTPException(
            status_code=400,
            detail="仅支持 .xlsx 格式的Excel文件"
        )

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
            raise HTTPException(status_code=400, detail="sheet_indices 格式错误")

    # Save initial job status
    _save_job(job_id, {
        "job_id": job_id,
        "status": "queued",
        "message": "任务已创建，等待处理...",
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
        "message": "任务已创建",
    }


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a render job."""
    job = _load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    return job


@router.get("/download/{job_id}")
async def download_result(job_id: str):
    """Download the ZIP file for a completed job."""
    job = _load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    if job.get("status") != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    zip_path = os.path.join(OUTPUTS_DIR, f"{job_id}.zip")
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="ZIP文件不存在")

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
        raise HTTPException(status_code=404, detail="任务不存在")

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
        import shutil
        shutil.rmtree(output_dir)

    # Delete ZIP
    zip_path = os.path.join(OUTPUTS_DIR, f"{job_id}.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    return {"message": "任务已删除"}


@router.get("/formats")
async def get_supported_formats():
    """Get list of supported output formats."""
    return {
        "formats": [
            {"id": "png", "name": "PNG", "description": "无损压缩，质量最好"},
            {"id": "jpg", "name": "JPG", "description": "有损压缩，文件更小"},
        ]
    }
