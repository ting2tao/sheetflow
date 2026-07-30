# SheetFlow

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="version">
  <img src="https://img.shields.io/badge/python-3.11+-green.svg" alt="python">
  <img src="https://img.shields.io/badge/vue-3.x-brightgreen.svg" alt="vue">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="license">
</p>

**表格分页图片生成器**

上传 Excel 表格，根据固定表头和分页规则，自动生成多张图片，并打包 ZIP 下载。

[English](./README.md) | 中文

---

## ✨ 功能特性

- 📁 支持 `.xlsx` 格式 Excel 文件
- 🔧 可设置表头行数和每页数据行数
- 🖼️ 生成 PNG/JPG 格式图片
- 📦 自动打包 ZIP 下载
- 🎨 保留表格样式（字体、颜色、边框、合并单元格）
- 📱 响应式 Web 界面
- 🌐 提供中文和英文独立入口

## 📸 界面预览

```
┌─────────────────────────────────────┐
│         📊 SheetFlow                │
│       表格分页图片生成器              │
├─────────────────────────────────────┤
│                                     │
│    ┌───────────────────────────┐    │
│    │      📁 拖拽上传文件       │    │
│    │      或点击选择            │    │
│    └───────────────────────────┘    │
│                                     │
│    表头行数: [  3  ]                 │
│    每页数据: [ 10  ]                 │
│    输出格式: ○ PNG  ○ JPG           │
│                                     │
│    [      🚀 开始生成      ]        │
│                                     │
└─────────────────────────────────────┘
```

## 🚀 快速开始

### 使用 Docker（推荐）

```bash
# 克隆项目
git clone https://github.com/ting2tao/sheetflow.git
cd sheetflow

# 启动服务
docker-compose up -d

# 访问 http://localhost/zh/ 或 http://localhost/en/
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

# 运行前端测试
npm test

# 使用明确的本地公开地址启动开发服务器
VITE_PUBLIC_SITE_URL=http://localhost:3000 npm run dev
```

访问 http://localhost:3000/zh/ 或 http://localhost:3000/en/。Vite 开发服务器会将
`/api` 请求代理到 8000 端口的后端。不设置该变量时也可以直接运行
`npm run dev`；上面的明确写法可确保开发环境的元数据 URL 指向本地服务器。

验证生产构建时，将 `VITE_PUBLIC_SITE_URL` 设置为网站对外公开的 HTTPS 源站地址。
构建会自动规范化末尾斜杠，但建议配置时省略：

```bash
cd frontend

# 这是保留的示例域名；实际部署请使用真实的公开源站地址。
VITE_PUBLIC_SITE_URL=https://sheetflow.example npm run build
```

该值会在构建时写入站点的 SEO 元数据和生成的爬虫文件。

### 一键启动

```bash
./start-dev.sh
```

## 🌐 语言 URL 与选择规则

- `/zh/` 是中文入口，`/en/` 是英文入口；生产环境会将 `/zh` 和 `/en`
  规范重定向到末尾带斜杠的 URL。
- 访问 `/` 时，首先读取已保存的 `sheetflow.locale` 语言偏好，然后读取浏览器
  第一偏好语言。浏览器语言以中文开头时选择中文，否则选择英文；浏览器语言也
  不可用时，最终回退到中文。
- 显式访问本地化 URL 时，URL 始终决定页面所用语言。
- 语言切换器不会刷新应用，只会更新本地化 URL，因此已上传文件、已选工作表、
  参数设置和正在处理的任务状态都会保留。

## 📖 使用说明

1. 上传 Excel 文件（`.xlsx` 格式）
2. 设置表头行数（默认为 1）
3. 设置每页数据行数（默认为 10）
4. 选择输出格式（PNG 或 JPG）
5. 点击"开始生成"
6. 等待处理完成
7. 下载 ZIP 文件

### 示例

**输入 Excel:**

| 用户退款申请单 | | | |
|---|---|---|---|
| 申请时间 | 申请人 | 金额 | 原因 |
| 2024-01-15 | 张三 | 100 | 质量问题 |
| 2024-01-16 | 李四 | 200 | 发错商品 |
| ... | ... | ... | ... |

**配置:** 表头行数 = 2, 每页数据 = 1

**输出:**
```
001.png  →  表头 + 张三的数据
002.png  →  表头 + 李四的数据
003.png  →  表头 + 王五的数据
...
result.zip  →  所有图片打包
```

## 🏗️ 技术架构

```
                    浏览器
                       │
                       ▼
             ┌──────────────────┐
             │ Vue 3 + vue-i18n │
             │  /zh/ 和 /en/    │
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

## 📁 项目结构

```
sheetflow/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 应用入口
│   │   ├── api/
│   │   │   └── render.py        # API 路由
│   │   ├── services/
│   │   │   ├── excel_parser.py  # Excel 解析
│   │   │   ├── paginator.py     # 分页逻辑
│   │   │   ├── html_renderer.py # HTML 渲染
│   │   │   └── screenshot.py    # 截图服务
│   │   └── templates/
│   │       └── table.html       # 表格模板
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # UI 组件（含语言切换器）
│   │   ├── i18n/                # 语言选择与翻译
│   │   └── App.vue              # 主应用组件
│   ├── en/index.html            # 英文 SEO 入口
│   ├── zh/index.html            # 中文 SEO 入口
│   ├── public/                  # 爬虫文件和社交分享图片
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── storage/
│   ├── uploads/                 # 上传的 Excel 文件
│   ├── jobs/                    # 任务状态文件
│   └── outputs/                 # 生成的图片和 ZIP
├── docker-compose.yml
├── start-dev.sh                 # 开发启动脚本
└── README.md
```

## 🔌 API 接口

### 上传工作簿

```http
POST /api/upload
Content-Type: multipart/form-data
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | Excel 文件（`.xlsx`） |

**响应:**
```json
{
  "job_id": "abc123",
  "filename": "report.xlsx",
  "sheets": [
    {"index": 0, "name": "Sheet1", "rows": 25, "columns": 6}
  ]
}
```

### 创建渲染任务

```http
POST /api/render
Content-Type: multipart/form-data
```

**参数:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| job_id | string | 是 | - | `/api/upload` 返回的任务 ID |
| header_rows | int | 否 | 1 | 表头行数 |
| page_size | int | 否 | 10 | 每页数据行数 |
| format | string | 否 | png | 输出格式（`png`/`jpg`） |
| quality | int | 否 | - | JPG 质量（1-100） |
| sheet_indices | string | 否 | all | 逗号分隔的工作表索引或 `all` |

**响应:**
```json
{
  "job_id": "abc123",
  "status": "queued",
  "message_code": "job.queued",
  "message_params": {}
}
```

### 查询任务状态

```http
GET /api/job/{job_id}
```

**响应:**
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

**状态说明:**

| 状态 | 说明 |
|------|------|
| queued | 等待处理 |
| uploaded | 工作簿已上传 |
| parsing | 解析 Excel |
| processing | 分页并生成图片 |
| zipping | 打包 ZIP |
| completed | 完成 |
| error | 失败 |

### 下载结果

```http
GET /api/download/{job_id}
```

**响应:** ZIP 文件下载

## ⚠️ V1 限制

### ✅ 支持

- 普通表格
- 固定表头
- 自动分页
- PNG/JPG 图片生成
- ZIP 打包下载
- 基础样式保留（字体、颜色、边框）
- 合并单元格
- 列宽自适应

### ❌ 暂不支持

- 复杂公式计算
- 图表
- Excel 图片对象
- 宏文件
- 条件格式
- 数据验证

## 🛠️ 技术栈

| 模块 | 技术 | 说明 |
|------|------|------|
| 后端 | FastAPI | 高性能异步框架 |
| Excel 解析 | openpyxl | 读取 xlsx 文件 |
| HTML 模板 | Jinja2 | 模板渲染 |
| 浏览器截图 | Playwright | Chromium 截图 |
| 前端 | Vue 3 | 响应式 UI |
| 构建工具 | Vite | 快速开发 |
| 部署 | Docker | 容器化部署 |

## 📝 开发计划

### V1.0（当前版本）
- [x] Excel 解析与分页
- [x] HTML 模板渲染
- [x] Playwright 截图
- [x] ZIP 打包下载
- [x] Web 界面

### V2.0（计划中）
- [ ] PDF 输出
- [ ] 长图模式
- [ ] 自动文件命名
- [ ] Logo/水印

### V3.0（计划中）
- [ ] 模板保存
- [ ] API 密钥认证
- [ ] 批量任务
- [ ] 企业微信/飞书机器人

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](./LICENSE) 文件

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [openpyxl](https://openpyxl.readthedocs.io/)
- [Playwright](https://playwright.dev/)
- [Vue.js](https://vuejs.org/)
- [Vite](https://vitejs.dev/)
