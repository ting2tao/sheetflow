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
- 🌐 Chinese and English localized entry points

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

# Visit http://localhost/zh/ or http://localhost/en/
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

# Run the frontend test suite
npm test

# Start the development server with an explicit local public origin
VITE_PUBLIC_SITE_URL=http://localhost:3000 npm run dev
```

Visit http://localhost:3000/zh/ or http://localhost:3000/en/. The Vite
development server proxies `/api` requests to the backend on port 8000.
`npm run dev` also works without this variable; the explicit form above keeps
the development metadata URLs tied to the local server.

To verify a production build, set `VITE_PUBLIC_SITE_URL` to the site's public
HTTPS origin. The build normalizes a trailing slash, but omitting it is
recommended:

```bash
cd frontend

# Reserved example domain; use the real public origin for a deployment.
VITE_PUBLIC_SITE_URL=https://sheetflow.example npm run build
```

The value is embedded at build time in the site's SEO metadata and generated
crawler files.

### One-Click Start

```bash
./start-dev.sh
```

## 🌐 Language URLs and Selection

- `/zh/` is the Chinese entry point and `/en/` is the English entry point.
  `/zh` and `/en` are canonicalized to their trailing-slash URLs in production.
- Opening `/` chooses a language from the saved `sheetflow.locale` preference
  first, then the browser's first preferred language. A Chinese browser language
  selects Chinese; any other browser language selects English. If no browser
  language is available, Chinese is the final fallback.
- An explicit localized URL always determines the displayed language.
- The language switcher updates the localized URL without reloading the app, so
  an uploaded file, selected sheets, settings, and in-progress job state are
  preserved.

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
             ┌──────────────────┐
             │ Vue 3 + vue-i18n │
             │  /zh/ and /en/   │
             └────────┬─────────┘
                      │ /api
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
│   │   ├── components/          # UI components, including language switcher
│   │   ├── i18n/                # Locale selection and translations
│   │   └── App.vue              # Main application component
│   ├── en/index.html            # English SEO entry point
│   ├── zh/index.html            # Chinese SEO entry point
│   ├── public/                  # Crawler files and social sharing asset
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

### Upload a Workbook

```http
POST /api/upload
Content-Type: multipart/form-data
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | Excel file (`.xlsx`) |

**Response:**
```json
{
  "job_id": "abc123",
  "filename": "report.xlsx",
  "sheets": [
    {"index": 0, "name": "Sheet1", "rows": 25, "columns": 6}
  ]
}
```

### Create Render Job

```http
POST /api/render
Content-Type: multipart/form-data
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| job_id | string | Yes | - | Job ID returned by `/api/upload` |
| header_rows | int | No | 1 | Number of header rows |
| page_size | int | No | 10 | Data rows per page |
| format | string | No | png | Output format (`png`/`jpg`) |
| quality | int | No | - | JPG quality (1-100) |
| sheet_indices | string | No | all | Comma-separated sheet indexes or `all` |

**Response:**
```json
{
  "job_id": "abc123",
  "status": "queued",
  "message_code": "job.queued",
  "message_params": {}
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
  "message_code": "job.completed",
  "message_params": {"sheets": 1, "pages": 10},
  "total_pages": 10,
  "download_url": "/api/download/abc123"
}
```

**Status Values:**

| Status | Description |
|--------|-------------|
| queued | Waiting to process |
| uploaded | Workbook uploaded |
| parsing | Parsing Excel file |
| processing | Paginating and generating images |
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
