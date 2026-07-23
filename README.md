# SheetFlow

**表格分页图片生成器**

上传 Excel 表格，根据固定表头和分页规则，自动生成多张图片，并打包 ZIP 下载。

## ✨ 功能特性

- 📁 支持 .xlsx 格式 Excel 文件
- 🔧 可设置表头行数和每页数据行数
- 🖼️ 生成 PNG/JPG 格式图片
- 📦 自动打包 ZIP 下载
- 🎨 保留表格样式（字体、颜色、边框、合并单元格）
- 📱 响应式 Web 界面

## 🚀 快速开始

### 使用 Docker（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd sheetflow

# 启动服务
docker-compose up -d

# 访问 http://localhost
```

### 本地开发

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 启动后端
uvicorn app.main:app --reload --port 8000
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:3000

## 📖 使用说明

1. 上传 Excel 文件（.xlsx 格式）
2. 设置表头行数（默认为 1）
3. 设置每页数据行数（默认为 10）
4. 选择输出格式（PNG 或 JPG）
5. 点击"开始生成"
6. 等待处理完成
7. 下载 ZIP 文件

## 🏗️ 技术架构

```
浏览器
   │
   ▼
FastAPI Server
   │
   ├── Excel Parser (openpyxl)
   │       │
   │       ▼
   │    HTML Template (Jinja2)
   │
   └── Image Worker (Playwright)
           │
           ▼
        PNG/JPG
           │
           ▼
         ZIP
```

## 📁 项目结构

```
sheetflow/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI 应用入口
│   │   ├── api/
│   │   │   └── render.py     # API 路由
│   │   ├── services/
│   │   │   ├── excel_parser.py   # Excel 解析
│   │   │   ├── paginator.py      # 分页逻辑
│   │   │   ├── html_renderer.py  # HTML 渲染
│   │   │   └── screenshot.py     # 截图服务
│   │   └── templates/
│   │       └── table.html    # 表格模板
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   └── App.vue          # 主应用组件
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── storage/
│   ├── uploads/             # 上传的 Excel 文件
│   ├── jobs/                # 任务状态文件
│   └── outputs/             # 生成的图片和 ZIP
├── docker-compose.yml
└── README.md
```

## 🔌 API 接口

### 创建渲染任务

```http
POST /api/render
Content-Type: multipart/form-data

Parameters:
- file: Excel 文件
- header_rows: 表头行数 (默认: 1)
- page_size: 每页数据行数 (默认: 10)
- format: 输出格式 png/jpg (默认: png)
- quality: JPG 质量 1-100 (可选)
- sheet_index: Sheet 索引 (默认: 0)

Response:
{
  "job_id": "abc123",
  "status": "queued",
  "message": "任务已创建"
}
```

### 查询任务状态

```http
GET /api/job/{job_id}

Response:
{
  "job_id": "abc123",
  "status": "completed",
  "message": "完成！共生成 10 张图片",
  "total_pages": 10,
  "download_url": "/api/download/abc123"
}
```

### 下载结果

```http
GET /api/download/{job_id}

Response: ZIP 文件
```

## ⚠️ V1 限制

### 支持

✅ 普通表格
✅ 固定表头
✅ 分页
✅ 图片生成
✅ ZIP 下载
✅ 基础样式保留

### 暂不支持

❌ 复杂公式计算
❌ 图表
❌ Excel 图片对象
❌ 宏文件
❌ 条件格式

## 📝 开发计划

### V1.0（当前）
- Excel 解析与分页
- HTML 模板渲染
- Playwright 截图
- ZIP 打包下载

### V2.0
- PDF 输出
- 长图模式
- 自动文件命名
- Logo/水印

### V3.0
- 模板保存
- API 接口
- 批量任务
- 企业微信/飞书机器人

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
