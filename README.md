# 花卉识别与科普系统

这是一个面向花卉图片识别、花卉资料浏览、收藏历史记录和智能问答的完整应用。项目由前端、后端和模型推理模块组成：

- 前端使用 Vue 3 + Vite，提供图片上传、识别结果展示、花卉科普库、用户登录、收藏、历史记录和问答界面。
- 后端使用 FastAPI，负责接口服务、用户认证、SQLite 数据存储、识别历史、收藏记录和问答会话管理。
- 模型模块使用 PyTorch / torchvision，加载训练好的 EfficientNet-B0 权重完成花卉分类推理。

## 项目结构

```text
Flower_Project/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── core/            # 配置与安全相关工具
│   │   ├── data/            # 花卉中文资料 JSON
│   │   ├── db/              # SQLAlchemy 模型、会话和数据访问
│   │   ├── routers/         # API 路由
│   │   ├── services/        # 业务逻辑
│   │   └── main.py          # 后端入口
│   ├── data/                # 本地 SQLite 数据库目录
│   └── requirements.txt
├── frontend/                # Vue 前端
│   ├── public/              # 静态资源
│   ├── src/
│   │   ├── components/      # 页面组件
│   │   ├── lib/             # API 与本地存储工具
│   │   ├── styles/          # 样式
│   │   └── App.vue          # 主应用
│   ├── package.json
│   └── vite.config.js
├── model_service/           # 模型训练与推理模块
│   ├── checkpoints/         # 模型权重，需本地准备
│   ├── utils/               # 数据集、模型和训练工具
│   ├── config.py
│   └── inference.py
├── AGENTS.md
└── README.md
```

## 环境准备

建议使用 Python 3.10 或更新版本，以及 Node.js 18 或更新版本。

后端依赖：

```powershell
cd E:\Flower_Project\backend
pip install -r requirements.txt
```

前端依赖：

```powershell
cd E:\Flower_Project\frontend
npm install
```

模型权重需要放在：

```text
E:\Flower_Project\model_service\checkpoints\efficientnet_b0_flowers102_final.pth
```

如果缺少该文件，识别接口会返回模型权重不存在的错误。

## 启动项目

先启动后端：

```powershell
cd E:\Flower_Project
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

再启动前端：

```powershell
cd E:\Flower_Project\frontend
npm run dev
```

浏览器访问：

```text
http://127.0.0.1:5173
```

后端接口文档：

```text
http://127.0.0.1:8000/docs
```

## 主要功能

- 图片识别：上传花卉图片，后端调用 PyTorch 模型返回 Top-3 分类结果。
- 花卉科普库：从后端 SQLite 中读取 102 类花卉中文资料，支持关键词搜索。
- 用户系统：支持注册、登录和 JWT 鉴权。
- 收藏与历史：登录用户可以保存识别历史和收藏花卉。
- 智能问答：围绕当前花卉资料进行问答，支持流式返回；未配置外部模型时会使用本地兜底回答。

## 常用接口

接口统一以 `/api` 为前缀：

```text
GET  /api/health
GET  /api/plants
GET  /api/plants/{class_id}
POST /api/recognition/predict
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
GET  /api/favorites
POST /api/favorites/{plant_id}
GET  /api/history
POST /api/rag/chat
POST /api/rag/chat/stream
GET  /api/rag/sessions
```

## 环境变量

后端支持以下环境变量：

```text
FLOWER_SECRET_KEY        JWT 签名密钥，正式环境必须设置
DASHSCOPE_API_KEY       DashScope / 百炼 API Key
DASHSCOPE_BASE_URL      DashScope 兼容接口地址
DASHSCOPE_MODEL_NAME    问答使用的模型名称，默认 qwen3-max
DASHSCOPE_TIMEOUT_SECONDS
RAG_RECENT_TURNS
```

前端支持：

```text
VITE_API_BASE_URL       后端 API 地址，默认 http://127.0.0.1:8000/api
```

## 数据与生成文件

以下内容属于本地依赖、构建产物、数据库或训练产物，不建议提交到版本库：

- `frontend/node_modules/`
- `frontend/dist/`
- `backend/data/*.sqlite3`
- `model_service/data/`
- `model_service/checkpoints/`
- `model_service/log/`
- `__pycache__/`
- `.env`

如果需要在新机器上运行，需要重新安装依赖，并准备模型权重文件。

## 说明

当前问答模块主要基于花卉资料和会话上下文构造 prompt，并在可用时调用 DashScope / 百炼接口；如果需要严格意义上的 RAG，可以继续补充向量化、分块检索、相似度召回和引用来源展示。
