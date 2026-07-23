"""API endpoints for Excel rendering.

POST /api/render - Upload Excel and start rendering job
GET /api/job/{id} - Check job status
GET /api/download/{id} - Download ZIP file
"""

import os
import uuid
import json
import asyncio
import zipfile
from datetime import datetime
from typing import Optional, Literal

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from app.services.excel_parser import parse_excel
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


async def _process_render_job(
    job_id: str,
    file_path: str,
    header_rows: int,
    page_size: int,
    format: str,
    quality: Optional[int],
    sheet_index: int = 0,
):
    """Background task to process the render job."""
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
        sheet = workbook.sheets[sheet_index] if workbook.sheets else None

        if not sheet or not sheet.rows:
            _save_job(job_id, {
                "job_id": job_id,
                "status": "error",
                "message": "Excel文件为空或无法解析",
                "created_at": datetime.now().isoformat(),
            })
            return

        # Update status: paginating
        _save_job(job_id, {
            "job_id": job_id,
            "status": "paginating",
            "message": "正在分页处理...",
            "total_rows": len(sheet.rows),
            "header_rows": header_rows,
            "page_size": page_size,
            "created_at": datetime.now().isoformat(),
        })

        # Step 2: Paginate
        pages = paginate(sheet, header_rows, page_size)

        if not pages:
            _save_job(job_id, {
                "job_id": job_id,
                "status": "error",
                "message": "分页后无数据",
                "created_at": datetime.now().isoformat(),
            })
            return

        total_pages = len(pages)

        # Update status: rendering
        _save_job(job_id, {
            "job_id": job_id,
            "status": "rendering",
            "message": f"正在生成HTML... (共{total_pages}页)",
            "total_pages": total_pages,
            "created_at": datetime.now().isoformat(),
        })

        # Step 3: Render HTML for each page
        html_pages = []
        for page in pages:
            html = render_page_html(page, sheet.column_widths)
            html_pages.append(html)

        # Update status: screenshotting
        _save_job(job_id, {
            "job_id": job_id,
            "status": "screenshotting",
            "message": f"正在截图... (共{total_pages}页)",
            "total_pages": total_pages,
            "created_at": datetime.now().isoformat(),
        })

        # Step 4: Capture screenshots
        output_dir = os.path.join(OUTPUTS_DIR, job_id)
        os.makedirs(output_dir, exist_ok=True)

        image_paths = await batch_capture(
            html_pages=html_pages,
            output_dir=output_dir,
            format=format,
            quality=quality,
            filename_prefix="",
        )

        # Update status: zipping
        _save_job(job_id, {
            "job_id": job_id,
            "status": "zipping",
            "message": "正在打包ZIP...",
            "total_pages": total_pages,
            "created_at": datetime.now().isoformat(),
        })

        # Step 5: Create ZIP
        zip_path = os.path.join(OUTPUTS_DIR, f"{job_id}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for img_path in image_paths:
                zf.write(img_path, os.path.basename(img_path))

        # Update status: completed
        _save_job(job_id, {
            "job_id": job_id,
            "status": "completed",
            "message": f"完成！共生成{total_pages}张图片",
            "total_pages": total_pages,
            "download_url": f"/api/download/{job_id}",
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
        })

    except Exception as e:
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


@router.post("/render")
async def create_render_job(
    file: UploadFile = File(...),
    header_rows: int = Form(1, ge=0, le=100),
    page_size: int = Form(10, ge=1, le=1000),
    format: Literal['png', 'jpg'] = Form('png'),
    quality: Optional[int] = Form(None, ge=1, le=100),
    sheet_index: int = Form(0, ge=0),
):
    """Create a new render job.

    Upload an Excel file with pagination parameters to generate images.
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

    # Save initial job status
    _save_job(job_id, {
        "job_id": job_id,
        "status": "queued",
        "message": "任务已创建，等待处理...",
        "filename": file.filename,
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
        sheet_index=sheet_index,
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

    filename = job.get("filename", "result.xlsx").replace('.xlsx', '')
    return FileResponse(
        path=zip_path,
        filename=f"{filename}_images.zip",
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
