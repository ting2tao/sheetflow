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

### 一键启动

```bash
./start-dev.sh
```

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
│   │   └── App.vue              # 主应用组件
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

### 创建渲染任务

```http
POST /api/render
Content-Type: multipart/form-data
```

**参数:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| file | File | 是 | - | Excel 文件 (.xlsx) |
| header_rows | int | 否 | 1 | 表头行数 |
| page_size | int | 否 | 10 | 每页数据行数 |
| format | string | 否 | png | 输出格式 (png/jpg) |
| quality | int | 否 | 90 | JPG 质量 (1-100) |
| sheet_index | int | 否 | 0 | Sheet 索引 |

**响应:**
```json
{
  "job_id": "abc123",
  "status": "queued",
  "message": "任务已创建"
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
  "message": "完成！共生成 10 张图片",
  "total_pages": 10,
  "download_url": "/api/download/abc123"
}
```

**状态说明:**

| 状态 | 说明 |
|------|------|
| queued | 等待处理 |
| parsing | 解析 Excel |
| paginating | 分页处理 |
| rendering | 生成 HTML |
| screenshotting | 截图中 |
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
