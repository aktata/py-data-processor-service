# Contributing

感谢你的贡献！

## 开发流程
1. Fork 并创建分支
2. 安装依赖：`pip install -e .[dev]`
3. 本地自检：`./scripts/verify.sh`
4. 提交 PR，描述清晰、附带测试结果

## 代码规范
- 使用 `ruff` 进行代码检查
- 核心逻辑必须包含类型标注
- 不允许在日志中输出原始敏感数据

## 提交信息建议
- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `chore:` 工具/构建变更
