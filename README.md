# SheetFlow

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="version">
  <img src="https://img.shields.io/badge/python-3.11+-green.svg" alt="python">
  <img src="https://img.shields.io/badge/vue-3.x-brightgreen.svg" alt="vue">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="license">
</p>

**Excel Pagination Image Generator**

Upload Excel spreadsheets, automatically generate paginated images based on fixed headers and pagination rules, then download as ZIP.

English | [中文](./README_CN.md)

---

## ✨ Features

- 📁 Support `.xlsx` Excel files
- 🔧 Configurable header rows and data rows per page
- 🖼️ Generate PNG/JPG format images
- 📦 Automatic ZIP packaging for download
- 🎨 Preserve table styles (fonts, colors, borders, merged cells)
- 📱 Responsive web interface

## 📸 Preview

```
┌─────────────────────────────────────┐
│         📊 SheetFlow                │
│    Excel Pagination Image Generator │
├─────────────────────────────────────┤
│                                     │
│    ┌───────────────────────────┐    │
│    │    📁 Drag & Drop File    │    │
│    │    or Click to Select     │    │
│    └───────────────────────────┘    │
│                                     │
│    Header Rows: [  3  ]             │
│    Data Rows:   [ 10  ]             │
│    Format:      ○ PNG  ○ JPG        │
│                                     │
│    [      🚀 Generate      ]        │
│                                     │
└─────────────────────────────────────┘
```

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/ting2tao/sheetflow.git
cd sheetflow

# Start services
docker-compose up -d

# Visit http://localhost
```

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Start backend server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Visit http://localhost:3000

### One-Click Start

```bash
./start-dev.sh
```

## 📖 Usage

1. Upload Excel file (`.xlsx` format)
2. Set header rows (default: 1)
3. Set data rows per page (default: 10)
4. Select output format (PNG or JPG)
5. Click "Generate"
6. Wait for processing to complete
7. Download ZIP file

### Example

**Input Excel:**

| User Refund Application | | | |
|---|---|---|---|
| Date | Applicant | Amount | Reason |
| 2024-01-15 | John | 100 | Quality issue |
| 2024-01-16 | Jane | 200 | Wrong item |
| ... | ... | ... | ... |

**Config:** Header rows = 2, Data rows per page = 1

**Output:**
```
001.png  →  Header + John's data
002.png  →  Header + Jane's data
003.png  →  Header + Bob's data
...
result.zip  →  All images packaged
```

## 🏗️ Architecture

```
                    Browser
                       │
                       ▼
               ┌──────────────┐
               │   FastAPI    │
               │    Server    │
               └──────┬───────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌───────────────┐          ┌───────────────┐
│ Excel Parser  │          │ Image Worker  │
│   (openpyxl)  │          │ (Playwright)  │
└───────┬───────┘          └───────┬───────┘
        │                          │
        ▼                          ▼
┌───────────────┐          ┌───────────────┐
│ HTML Template │          │   Chromium    │
│   (Jinja2)    │──────────│   Browser     │
└───────────────┘          └───────┬───────┘
                                  │
                                  ▼
                           ┌───────────────┐
                           │   PNG/JPG     │
                           └───────┬───────┘
                                   │
                                   ▼
                           ┌───────────────┐
                           │      ZIP      │
                           └───────────────┘
```

## 📁 Project Structure

```
sheetflow/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry
│   │   ├── api/
│   │   │   └── render.py        # API routes
│   │   ├── services/
│   │   │   ├── excel_parser.py  # Excel parsing
│   │   │   ├── paginator.py     # Pagination logic
│   │   │   ├── html_renderer.py # HTML rendering
│   │   │   └── screenshot.py    # Screenshot service
│   │   └── templates/
│   │       └── table.html       # Table template
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   └── App.vue              # Main application component
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── storage/
│   ├── uploads/                 # Uploaded Excel files
│   ├── jobs/                    # Job status files
│   └── outputs/                 # Generated images and ZIP
├── docker-compose.yml
├── start-dev.sh                 # Development startup script
└── README.md
```

## 🔌 API Reference

### Create Render Job

```http
POST /api/render
Content-Type: multipart/form-data
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| file | File | Yes | - | Excel file (.xlsx) |
| header_rows | int | No | 1 | Number of header rows |
| page_size | int | No | 10 | Data rows per page |
| format | string | No | png | Output format (png/jpg) |
| quality | int | No | 90 | JPG quality (1-100) |
| sheet_index | int | No | 0 | Sheet index |

**Response:**
```json
{
  "job_id": "abc123",
  "status": "queued",
  "message": "任务已创建"
}
```

### Get Job Status

```http
GET /api/job/{job_id}
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "completed",
  "message": "完成！共生成 10 张图片",
  "total_pages": 10,
  "download_url": "/api/download/abc123"
}
```

**Status Values:**

| Status | Description |
|--------|-------------|
| queued | Waiting to process |
| parsing | Parsing Excel file |
| paginating | Processing pagination |
| rendering | Generating HTML |
| screenshotting | Capturing screenshots |
| zipping | Creating ZIP file |
| completed | Processing complete |
| error | Processing failed |

### Download Result

```http
GET /api/download/{job_id}
```

**Response:** ZIP file download

## ⚠️ V1 Limitations

### ✅ Supported

- Standard tables
- Fixed headers
- Automatic pagination
- PNG/JPG image generation
- ZIP packaging
- Basic style preservation (fonts, colors, borders)
- Merged cells
- Column width adaptation

### ❌ Not Supported Yet

- Complex formulas
- Charts
- Excel image objects
- Macro files
- Conditional formatting
- Data validation

## 🛠️ Tech Stack

| Module | Technology | Description |
|--------|------------|-------------|
| Backend | FastAPI | High-performance async framework |
| Excel Parsing | openpyxl | Read xlsx files |
| HTML Template | Jinja2 | Template rendering |
| Screenshot | Playwright | Chromium screenshots |
| Frontend | Vue 3 | Reactive UI |
| Build Tool | Vite | Fast development |
| Deployment | Docker | Containerized deployment |

## 📝 Roadmap

### V1.0 (Current)
- [x] Excel parsing and pagination
- [x] HTML template rendering
- [x] Playwright screenshots
- [x] ZIP packaging
- [x] Web interface

### V2.0 (Planned)
- [ ] PDF output
- [ ] Long image mode
- [ ] Automatic file naming
- [ ] Logo/Watermark

### V3.0 (Planned)
- [ ] Template management
- [ ] API key authentication
- [ ] Batch processing
- [ ] WeChat/Feishu bot integration

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [openpyxl](https://openpyxl.readthedocs.io/)
- [Playwright](https://playwright.dev/)
- [Vue.js](https://vuejs.org/)
- [Vite](https://vitejs.dev/)
