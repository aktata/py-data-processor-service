# 批量财务数据处理与风险分析系统（Python）

> **定位**：面向多公司、多年份财务 Excel 的批量入库、指标计算、风险评分与报告自动生成系统。支持 CLI 一键流水线、可选 FastAPI 查询接口，并提供 Excel/PPT 报告输出与可配置风险规则。

## 目录
- [项目背景/适用场景](#项目背景适用场景)
- [5 分钟快速开始](#5-分钟快速开始)
- [环境准备与依赖说明](#环境准备与依赖说明)
- [工程结构](#工程结构)
- [数据模板与层级识别策略](#数据模板与层级识别策略)
- [统一数据 Schema](#统一数据-schema)
- [指标口径与风险规则](#指标口径与风险规则)
- [CLI 命令说明](#cli-命令说明)
- [API 使用说明](#api-使用说明)
- [报告说明（Excel/PPT）](#报告说明excelppt)
- [自检与验收](#自检与验收)
- [FAQ / 排错（>=12）](#faq--排错12)
- [开发扩展指南](#开发扩展指南)

---

## 项目背景/适用场景
财务分析常见痛点：
- 多公司、多年份 Excel 分散且格式不统一
- 科目层级不一致导致无法统一对比
- 指标口径难以统一、风险评估缺乏标准化

本系统提供：
- **批量 Excel 入库**（资产负债表/利润表/现金流量表）
- **科目层级自动识别**（缩进/分隔符/多列）
- **指标计算与风险评分**（净利润率、流动比率、ROE）
- **报告自动化输出**（Excel 标色 + PPT 图表）
- **统一错误码与输出结构**（CLI/API 一致）

适合场景：
- 财务共享中心的批量监控
- 审计/风控部门的多公司横向对比
- 数据中台的标准化财务数据入库

---

## 5 分钟快速开始
```bash
# 1) 创建虚拟环境并安装依赖
python -m venv venv
source venv/bin/activate
pip install -e .[dev]

# 2) 生成演示数据（三家公司、三张表、三年数据）
python scripts/generate_demo_data.py

# 3) 入库（SQLite）
python -m app.cli ingest --input-dir data/input --db-path data/output/finance.db --reset --json

# 4) 计算指标与风险评分
python -m app.cli calc --db-path data/output/finance.db --json

# 5) 排名
python -m app.cli rank --db-path data/output/finance.db --indicator net_profit_margin --year 2023 --n 3 --json

# 6) 输出报告
python -m app.cli export_excel --db-path data/output/finance.db --year 2023 --output-path data/output/report.xlsx --json
python -m app.cli export_ppt --db-path data/output/finance.db --year 2023 --output-path data/output/report.pptx --json
```

---

## 环境准备与依赖说明
- Python 3.10
- pandas + openpyxl（Excel 读取/写入）
- matplotlib（图表生成，默认 Agg 后端）
- python-pptx（PPT 输出）
- SQLite（内置，无需额外安装）

### 常见依赖坑
- **openpyxl**：建议使用最新版本，避免旧版本读写失败
- **matplotlib**：在极简 Linux 环境可能缺少字体；Docker 已内置 `libfreetype6` 和 `libpng`
- **PPT 输出**：需要 `python-pptx`，已加入依赖

---

## 工程结构
```
app/
  api/                 FastAPI 路由（query/rank/drilldown）
  analytics/           指标计算、评分、排名、下钻
  core/                错误码/响应/日志
  ingest/              Excel 读取与科目层级解析
  reporting/           图表、Excel/PPT 报告
  risk/                风险规则配置
  storage/             SQLite 数据访问
  cli.py               统一 CLI
scripts/
  generate_demo_data.py
  verify.sh
  docker_verify.sh
```

---

## 数据模板与层级识别策略
### Excel 要求
每家公司一个 Excel 文件，包含三个 sheet：
- 资产负债表（资产负债表 或 balance_sheet）
- 利润表（利润表 或 income_statement）
- 现金流量表（现金流量表 或 cash_flow）

### 科目层级识别（支持 3 种形式）
1. **缩进层级（形式 A）**：
   - 科目列用空格缩进，例如：
     - `资产`
     - `  流动资产`
     - `    货币资金`
2. **分隔符（形式 B）**：
   - `资产-流动资产-货币资金` 或 `资产/流动资产/货币资金`
3. **多列科目（形式 C）**：
   - `subject_l1/subject_l2/subject_l3` 三列或 `一级科目/二级科目/三级科目`

### 标准模板建议
- 推荐使用 **多列科目形式 C**（最稳定）
- 年份列使用 4 位数字，如 `2022`, `2023`

无法识别时会触发 `parse_error`，并在 README 提示调整模板。

---

## 统一数据 Schema
### financial_facts（事实表）
| 字段 | 说明 |
|---|---|
| company_name | 公司名称 |
| statement_type | balance_sheet / income_statement / cash_flow |
| category | 大类（通常取 subject_l1） |
| subject_path | 科目路径（如 资产>流动资产>货币资金） |
| subject_l1 | 一级科目 |
| subject_l2 | 二级科目 |
| subject_l3 | 三级科目 |
| year | 年份（int） |
| amount | 金额（float） |

### metrics_table（指标表）
| 字段 | 说明 |
|---|---|
| company_name | 公司名称 |
| year | 年份 |
| indicator_name | 指标名 |
| indicator_value | 指标值 |
| risk_level | low/medium/high/unknown |
| risk_score | 0-100 风险分数 |
| details | 口径详情（JSON） |

---

## 指标口径与风险规则
### 指标口径
- 净利润率 = 净利润 / 营业收入
- 流动比率 = 流动资产 / 流动负债
- ROE = 净利润 / 所有者权益（若缺少平均权益，使用期末近似）

> 若缺失字段：默认返回 NaN 并记录 warnings，可通过 `.env` 设置 `MISSING_VALUE_STRATEGY=error` 强制报错。

### 风险规则（默认）
| 指标 | 低风险 | 中风险 | 高风险 |
|---|---|---|---|
| 净利润率 | >=0.2 | >=0.1 | <0.1 |
| 流动比率 | >=1.5 | >=1.0 | <1.0 |
| ROE | >=0.15 | >=0.08 | <0.08 |

规则集中于 `app/risk/rules.py`，可自行修改阈值与分数映射。

---

## CLI 命令说明
统一输出结构：
```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "trace_id": "..."
}
```

### 1) ingest
```bash
python -m app.cli ingest --input-dir data/input --db-path data/output/finance.db --reset --json
```

### 2) calc
```bash
python -m app.cli calc --db-path data/output/finance.db --json
```

### 3) query
```bash
python -m app.cli query --db-path data/output/finance.db --company 星河科技 --year 2023 --indicator net_profit_margin --json
```

### 4) rank
```bash
python -m app.cli rank --db-path data/output/finance.db --indicator net_profit_margin --year 2023 --n 5 --json
```

### 5) drilldown
```bash
python -m app.cli drilldown --db-path data/output/finance.db --company 星河科技 --year 2023 \
  --statement-type balance_sheet --subject-prefix 资产>流动资产 --json
```

### 6) export_excel
```bash
python -m app.cli export_excel --db-path data/output/finance.db --year 2023 --output-path data/output/report.xlsx --json
```

### 7) export_ppt
```bash
python -m app.cli export_ppt --db-path data/output/finance.db --year 2023 --output-path data/output/report.pptx --json
```

---

## API 使用说明
保留 FastAPI 以供二次开发，当前提供：
- `/health`
- `/query`
- `/rank`
- `/drilldown`

### 启动
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 示例
```bash
curl -s -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"company": "星河科技", "year": 2023, "indicator": "net_profit_margin"}'
```

---

## 报告说明（Excel/PPT）
### Excel
- Sheet1 指标表：含风险等级标色（低=绿，中=橙，高=红）
- Sheet2 排名表：指标 TopN 排名
- 可选 Sheet3：明细下钻

### PPT
- 每公司至少 2 页
  - 页1：公司概览 + 总体风险分数 + 关键指标表
  - 页2：趋势图（净利润率/流动比率/ROE） + 排名摘要
- 图表先保存 PNG，再插入 PPT
- 模板文件：`app/reporting/templates/report_template.pptx`（若不存在会在导出时自动生成）

---

## 自检与验收
### 本地一键自检
```bash
bash scripts/verify.sh
```
- 创建 venv
- 安装依赖
- ruff + pytest
- 生成 demo 数据
- 完整 pipeline：ingest/calc/rank/export
- 校验 Excel/PPT 产物与页数

### Docker 自检
```bash
bash scripts/docker_verify.sh
```
> Docker 命令已使用 sudo

---

## FAQ / 排错（>=12）
1. **Q：为什么提示 parse_error？**
   - A：科目列格式不兼容，建议使用多列科目形式（subject_l1/subject_l2/subject_l3）。
2. **Q：提示 missing_required_subject？**
   - A：缺少净利润/营业收入/流动资产/流动负债/所有者权益等科目。
3. **Q：报告里显示 NaN？**
   - A：分母为 0 或缺失数据，默认策略为警告。
4. **Q：怎么调整风险阈值？**
   - A：修改 `app/risk/rules.py`。
5. **Q：PPT 生成失败？**
   - A：检查 python-pptx 是否安装，或模板文件是否存在。
6. **Q：matplotlib 报错字体缺失？**
   - A：安装系统字体或在 Docker 使用内置依赖。
7. **Q：Excel 无法读取？**
   - A：确保为 xlsx 格式，并存在三个 sheet。
8. **Q：如何新增指标？**
   - A：参见开发扩展指南。
9. **Q：为什么排名结果为空？**
   - A：未执行 calc 或指标名称不匹配。
10. **Q：怎么导出下钻明细？**
   - A：使用 `export_excel` 时传入 company/statement_type/subject_prefix。
11. **Q：CLI 失败没有 JSON？**
   - A：加 `--json` 参数输出结构化错误。
12. **Q：Docker verify 输出失败？**
   - A：检查宿主机是否具有 sudo 权限与 Docker 正常运行。

---

## 开发扩展指南
### 新增指标
1. 在 `app/analytics/indicators.py` 增加字段映射与计算逻辑
2. 在 `app/risk/rules.py` 添加风险规则
3. 在 README 更新口径说明

### 新增科目/报表
1. 在 `app/ingest/excel_reader.py` 增加 sheet 映射
2. 在 `app/ingest/normalizer.py` 调整解析逻辑

### 新增评分规则
- 修改 `app/risk/rules.py` 中阈值与 score 即可

---

如需 Streamlit/Dash UI，可直接调用 CLI 或 API 的 query/rank/drilldown 结果作为数据源。
