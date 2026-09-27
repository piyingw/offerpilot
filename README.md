# OfferPilot · 秋招求职助手

把 **AI 模拟面试 + 半自动投递 + 求职进度看板** 做成闭环的秋招 Web 应用。

> ⚠️ 项目处于开发初期（M0 已完成，M1 模拟面试开发中）。自动投递模块设计为**半自动**（AI 打分 → 人工确认 → 执行），仅供学习交流，请遵守各招聘平台用户协议。

## 功能规划

| 模块 | 说明 | 状态 |
|---|---|---|
| 🎯 模拟面试（MVP） | 上传简历，AI 面试官文字对话（简历深挖 / 技术面），SSE 流式输出，评分复盘报告 | ✅ 已完成 |
| 📊 进度看板 | 投递漏斗图、状态时间线、周投递量与转化率统计 | 规划中 |
| 🤖 半自动投递 | 岗位抓取（Boss/智联/前程无忧/猎聘）→ LLM 匹配打分 → 确认队列 → Playwright 执行 | 规划中 |
| 🎙️ 语音面试 | TTS + ASR 实时语音对话 | 规划中 |

详细需求与技术选型见 [docs/项目规划.md](docs/项目规划.md)。

## 技术栈

- **前端**：React 18 + TypeScript + Vite · Ant Design 5 · Zustand · TanStack Query · ECharts
- **后端**：FastAPI · SQLAlchemy 2.0 + Alembic · Celery + Redis · LangChain（GLM/DeepSeek/Qwen 可配置）
- **数据与部署**：MySQL 8 · Redis 7 · Docker Compose + Nginx
- **质量**：pytest · ruff · ESLint · Prettier · GitHub Actions

## 目录结构

```
├── backend/          # FastAPI 后端（app/ 包 + alembic 迁移 + tests）
├── frontend/         # React SPA（Vite）
├── docs/             # 项目规划文档
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
docker compose up --build
# 前端 http://localhost:5173 · 后端 API 文档 http://localhost:8000/docs
```

### 方式二：本地开发

1. 启动数据库（需已安装 Docker；或自备 MySQL 8 + Redis）：

   ```bash
   docker compose up -d mysql redis
   ```

2. 后端（Python 3.11+）：

   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate            # Windows；macOS/Linux 用 source .venv/bin/activate
   pip install -e ".[dev]"
   copy .env.example .env            # macOS/Linux 用 cp
   alembic upgrade head
   uvicorn app.main:app --reload
   ```

3. 前端（Node 20+）：

   ```bash
   cd frontend
   npm install
   npm run dev                       # http://localhost:5173，已配置 /api 代理到 8000
   ```

4. 配置 LLM（模拟面试必需）：编辑 `backend/.env`，任选一家并填入 API Key：

   ```ini
   LLM_PROVIDER=glm        # glm | deepseek | qwen（base_url 与默认模型已预设）
   LLM_API_KEY=你的Key
   # LLM_MODEL=glm-4-flash # 可选，覆盖默认模型
   ```

   未配置 Key 时应用仍可运行：简历上传会降级为"仅原文"模式，发起面试时给出明确提示。

## 常用命令

| 位置 | 命令 | 说明 |
|---|---|---|
| backend | `pytest` | 运行测试（SQLite，无需 MySQL） |
| backend | `ruff check .` | 代码检查 |
| backend | `alembic revision --autogenerate -m "xxx"` | 生成迁移 |
| frontend | `npm run dev` / `npm run build` / `npm run lint` | 开发 / 构建 / 检查 |

## 开发路线

- [x] M0 项目脚手架（monorepo · Compose · CI · JWT 认证）
- [x] M1 模拟面试 MVP（简历解析 · AI 面试官 · 复盘报告）
- [ ] M2 进度看板
- [ ] M3 半自动投递
- [ ] M4 语音面试
- [ ] M5 开源打磨

## License

MIT（发布时补充）
