# Py Data Processor Service

> **定位**：这是一个可直接落地的生产级数据处理服务（FastAPI + Uvicorn），支持 CSV / JSON / 图片 输入的统一处理与摘要分析，内置严格校验、统一错误码、结构化日志、完整测试与 Docker 一键部署。

## 目录
- [项目背景与适用场景](#项目背景与适用场景)
- [5 分钟跑起来](#5-分钟跑起来)
- [功能清单](#功能清单)
- [架构设计](#架构设计)
- [环境要求](#环境要求)
- [环境配置方法](#环境配置方法)
- [本地运行](#本地运行)
- [Docker 运行](#docker-运行)
- [Docker Compose 运行](#docker-compose-运行)
- [API 使用指南](#api-使用指南)
- [输出字段解释](#输出字段解释)
- [CLI 使用](#cli-使用)
- [错误码表](#错误码表)
- [限制阈值说明](#限制阈值说明)
- [测试说明](#测试说明)
- [代码规范与贡献](#代码规范与贡献)
- [安全与合规说明](#安全与合规说明)
- [性能注意事项](#性能注意事项)
- [自检与验收](#自检与验收)
- [FAQ / 排错](#faq--排错)
- [目录索引](#目录索引)

---

## 项目背景与适用场景
在数据处理链路中，经常需要对不同类型输入（CSV、JSON、图片）做统一的快速校验与摘要分析。本项目提供：
- **统一输入规范**（multipart 文件上传/JSON 直传）
- **统一输出结构**（含 trace_id、错误码）
- **可观测性**（结构化日志 + trace_id 贯穿）
- **易部署**（Docker、docker-compose）

适合场景：
- 数据治理/数据平台的前置校验服务
- 文件上传后的快速预检与内容摘要
- ETL 前数据质量概览与健康检查

---

## 5 分钟跑起来
> 以下三选一，复制粘贴即可运行。

### 方案 A：本地运行（推荐）
```bash
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
cp .env.example .env
./scripts/run_local.sh
```
访问：
- 服务健康检查：`http://127.0.0.1:8000/health`
- 接口文档：`http://127.0.0.1:8000/docs`

### 方案 B：Docker
```bash
sudo docker build -t data-processor .
sudo docker run -p 8000:8000 --env-file .env.example data-processor
```

### 方案 C：Docker Compose
```bash
sudo docker compose up -d
```

---

## 功能清单
- **输入类型支持**
  - CSV：编码探测（utf-8/utf-8-sig/gbk）、分隔符探测（`,`/`\t`/`;`）
  - JSON：支持 API 直传或 `.json` 文件上传
  - 图片：PNG/JPG/WEBP 基础元信息提取（Pillow）
- **输出摘要**
  - CSV：行数、列数、列名、缺失值统计、粗略类型推断
  - JSON：顶层键、估算深度、节点数、类型分布
  - 图片：格式、宽高、模式、大小
- **工程化能力**
  - 统一响应结构与错误码
  - trace_id 贯穿请求、日志与响应
  - 完整 pytest 测试
  - CLI 离线处理能力
  - Docker/Docker Compose 部署
  - 一键 verify 自检脚本

---

## 架构设计
### 模块职责
```
app/
  main.py              FastAPI 入口、异常处理与中间件
  config.py            配置管理
  core/
    errors.py          错误码与异常类型
    logging.py         结构化日志与 trace_id 中间件
    response.py        统一响应封装
  api/routes.py        /health 与 /process 路由
  cli.py             命令行入口（离线处理）
  services/processor.py  识别输入类型、校验、处理逻辑
  utils/               各类输入处理工具
```

### 调用链（/process）
1. **API 层**接收请求并进行基础校验（JSON 直传或文件上传）
2. **Service 层**统一建模为 `InputObject`，执行 identify → validate → parse → process
3. **Utils 层**完成解析与摘要生成（CSV/JSON/Image）
4. **统一响应**返回稳定的 `code/message/data/trace_id`

### 错误处理策略
- 业务错误：抛出 `AppError`，由统一异常处理器映射为统一响应
- 未预期异常：捕获为 `internal_error`（错误码 2001）

### trace_id 流程
- 中间件生成/复用 `X-Trace-Id`
- 写入日志上下文
- 返回响应字段 `trace_id` 和响应头 `X-Trace-Id`

---

## 环境要求
- **Python**：3.10
- **操作系统**：Linux / macOS / Windows（WSL 推荐）
- **依赖工具**：
  - Git
  - curl
  - Docker / docker compose（可选）

> Windows 用户建议使用 WSL2 或 Git Bash，避免脚本兼容问题。

---

## 环境配置方法
### 1) 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate
```

### 2) 安装依赖
```bash
pip install -e .[dev]
```

### 3) 环境变量配置
复制 `.env.example` 到 `.env` 并根据需要修改（不创建也可运行，默认值内置）：
```bash
cp .env.example .env
```

常见问题：
- 如遇公司代理/证书问题，请配置 `PIP_INDEX_URL` 或系统 CA。

---

## 本地运行
```bash
python -m venv venv
source venv/bin/activate
pip install -e .
./scripts/run_local.sh
```

常见失败原因与解决：
- 端口占用：修改 `--port` 或 `.env` 中 `PORT`
- 依赖安装失败：确认 Python 版本与网络代理

---

## Docker 运行
```bash
sudo docker build -t data-processor .
sudo docker run -p 8000:8000 --env-file .env data-processor
```

常见失败原因与解决：
- `permission denied`：确保当前用户具备 Docker 权限或使用 `sudo`
- 构建超时：检查网络或镜像源配置

---

## Docker Compose 运行
```bash
sudo docker compose up -d
```

常见失败原因与解决：
- 端口冲突：修改 `docker-compose.yml` 中的端口映射

---

## API 使用指南
### 统一响应格式
```json
{
  "code": 0,
  "message": "success",
  "data": {"...": "..."},
  "trace_id": "..."
}
```

### GET /health
```bash
curl http://127.0.0.1:8000/health
```
示例响应：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "ok",
    "version": "0.1.0",
    "uptime_seconds": 12
  },
  "trace_id": "..."
}
```

### POST /process (JSON 直传)
```bash
curl -X POST http://127.0.0.1:8000/process \
  -H "Content-Type: application/json" \
  -d '{"hello":"world","items":[1,2,3]}'
```

示例响应：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "input_type": "json",
    "source": "json_body",
    "summary": {
      "top_level_keys": ["hello", "items"],
      "estimated_depth": 3,
      "estimated_nodes_count": 5,
      "type_summary": {"dict": 2, "list": 1, "str": 1, "int": 1}
    },
    "warnings": [],
    "timings_ms": {"parse": 1, "validate": 2, "process": 2, "total": 3},
    "limits": {"max_bytes": 5242880, "json_max_depth": 20, "json_max_nodes": 20000}
  },
  "trace_id": "..."
}
```

### POST /process (CSV 上传)
```bash
curl -X POST http://127.0.0.1:8000/process \
  -F "file=@data/sample.csv"
```

### POST /process (JSON 文件上传)
```bash
curl -X POST http://127.0.0.1:8000/process \
  -F "file=@data/sample.json"
```

### POST /process (图片上传)
```bash
base64 -d data/sample_image_base64.txt > /tmp/sample.png
curl -X POST http://127.0.0.1:8000/process \
  -F "file=@/tmp/sample.png"
```

### 错误响应示例
```json
{
  "code": 1002,
  "message": "Unsupported file type.",
  "data": {
    "error_type": "unsupported_type",
    "details": {"filename": "sample.txt", "content_type": "text/plain"}
  },
  "trace_id": "..."
}
```

---

## 输出字段解释
统一响应 `data` 的固定结构如下（各类型的 `summary` 字段不同，但结构稳定）：
```json
{
  "input_type": "csv|json|image",
  "source": "json_body|file_upload",
  "summary": { "...": "..." },
  "warnings": [],
  "timings_ms": {"parse": 0, "validate": 0, "process": 0, "total": 0},
  "limits": {"max_bytes": 5242880, "json_max_depth": 20, "json_max_nodes": 20000}
}
```
字段说明：
- **input_type**：识别到的输入类型
- **source**：输入来源（JSON 直传或文件上传）
- **summary**：各类型的统计摘要（不包含原始内容）
- **warnings**：非致命问题提示（如编码/分隔符探测）
- **timings_ms**：解析/校验/处理/总耗时
- **limits**：本次生效的限制阈值（`max_bytes` 为字节）

顶层字段说明：
- **trace_id**：请求链路追踪 ID（日志与响应一致）

---

## CLI 使用
CLI 与 API 输出结构一致，适合离线调试与排错：
```bash
python -m app.cli process --json '{"hello":"world","items":[1,2,3]}'
```

```bash
python -m app.cli process --file data/sample.csv
```

---

## 错误码表
| code | 类型 | 触发条件 | 排查建议 |
|------|------|----------|----------|
| 0 | success | 成功 | - |
| 1001 | invalid_request | 请求体不合法/参数冲突 | 检查是否同时传 file + json |
| 1002 | unsupported_type | 不支持的文件类型 | 检查后缀/MIME 是否在支持列表 |
| 1003 | payload_too_large | 超过上传限制 | 调整 `MAX_UPLOAD_SIZE_MB` |
| 1004 | parse_error | CSV/JSON/图片解析失败 | 检查文件内容/编码 |
| 1005 | validation_error | 内容校验失败 | 检查必需字段/数据结构 |
| 2001 | internal_error | 未预期异常 | 查看日志与 trace_id |

---

## 限制阈值说明
默认限制可在 `.env` 中调整（见 `.env.example`）：
- **MAX_UPLOAD_SIZE_MB**：上传最大大小（MB）
- **JSON_MAX_DEPTH**：JSON 最大深度
- **JSON_MAX_NODES**：JSON 最大节点数

调整方式：
```bash
cp .env.example .env
${EDITOR:-vi} .env
```

---

## 测试说明
```bash
pytest -q
```

覆盖内容：
- `/health` 成功
- `/process` JSON 直传成功
- `/process` CSV 上传成功
- `/process` 图片上传成功
- 不支持类型返回 1002

新增测试建议：
- 针对边界输入（大文件、嵌套 JSON）编写测试
- 保持响应结构一致性验证

---

## 代码规范与贡献
- 代码风格：`ruff`
- 类型标注：核心模块必须标注
- 提交规范：`feat/fix/docs/chore` 前缀

贡献流程：
1. fork + branch
2. 本地通过 `scripts/verify.sh`
3. 提交 PR

更多请参考 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 安全与合规说明
- 配置与密钥通过环境变量与 `.env` 管理
- 日志仅记录摘要信息，不记录原始文件内容
- 提供最大文件大小、JSON 深度与节点数限制

---

## 性能注意事项
- JSON 遍历设置 `JSON_MAX_DEPTH` 与 `JSON_MAX_NODES`
- CSV 解析对大文件建议增加流式策略（当前版本为内存解析）
- 上传大小通过 `MAX_UPLOAD_SIZE_MB` 控制

---

## 自检与验收
### 本地自检
```bash
./scripts/verify.sh
```
预期输出：
```
/health ok
/process json ok
verify.sh completed successfully
```

### Docker 自检
```bash
sudo ./scripts/docker_verify.sh
```
预期输出：
```
/health ok
/process ok
docker_verify.sh completed successfully
```

---

## FAQ / 排错
1. **无法启动服务**：检查端口占用、Python 版本
2. **pip 安装失败**：确认网络/代理/证书配置
3. **CSV 解析失败**：检查编码与分隔符（UTF-8/GBK）
4. **JSON 深度/节点限制触发**：调整 `JSON_MAX_DEPTH` / `JSON_MAX_NODES`
5. **响应 code 非 0**：查看 message 与 trace_id，结合日志定位
6. **Docker build 超时**：配置镜像源或重试
7. **Windows 脚本不可执行**：使用 Git Bash 或 WSL
8. **图片解析失败**：确认图片格式是否支持（PNG/JPG/WEBP）
9. **上传太大**：调整 `MAX_UPLOAD_SIZE_MB`
10. **curl 上传图片失败**：确认已用 base64 生成临时 PNG（见示例）
11. **CLI 返回 parse_error**：检查 JSON 字符串格式是否正确
12. **测试失败**：确保依赖完整安装并使用 `.venv`

---

## 目录索引
```
project-root/
  app/
    main.py
    cli.py
    config.py
    core/
    api/
    services/
    utils/
  tests/
  scripts/
  data/
  Dockerfile
  docker-compose.yml
  pyproject.toml
  README.md
  CONTRIBUTING.md
  LICENSE
```

---

如需扩展更多处理能力（如 Parquet/Excel），可在 `app/utils` 内添加解析工具，并在 `services/processor.py` 中统一接入。
