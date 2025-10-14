# CLAUDE.md

**Project**: MCP OpenProject Integration Platform

## 🏗️ Project Structure
```
mcp-open-project2/
├── mcp_server/           # MCP服务器 (FastMCP)
├── mcp_client/           # AI网站后端 (FastAPI + LangChain)
├── openproject_client/   # OpenProject API客户端
├── docs/                 # 文档网络
├── scripts/              # 工具脚本
├── QUALITY_*.md         # 质量体系文档
└── TASK_*.md            # 任务管理文档
```

## 🔴 Critical Rules

### Virtual Environment (REQUIRED)
```bash
# 每次Python命令前必须激活
source venv/bin/activate && python <script>

# 禁止的操作
❌ python <script>           # 直接使用系统Python
❌ pip install --user      # 安装到用户系统
❌ sudo pip install       # 系统级安装
```

### Required Documents by Task
- **Start any task**: `DESIGN_COMPLIANCE_CHECKLIST.md`, `TASK_PLANNING_TEMPLATE.md`
- **Code implementation**: `docs/architecture/PROJECT_STRUCTURE.md`
- **Security operations**: `docs/analysis/python_code_review.md`
- **Database operations**: `docs/architecture/database_design.md`
- **Testing**: `QUALITY_GATE_SYSTEM.md`

### Component-Specific Docs
- **mcp-server/**: `mcp-server/CLAUDE.md`
- **mcp-client/**: `mcp-client/CLAUDE.md`
- **openproject_client/**: `openproject_client/CLAUDE.md`

## 🚨 Workflow Compliance

### 3-Step Process
1. **Before starting**: Read required docs, check design compliance
2. **During implementation**: Validate progress continuously
3. **After completion**: Pass quality gates

### Red Light Violations (STOP IMMEDIATELY)
- Starting without reading design docs
- Skipping quality gates
- Manually modifying no-code generated code
- Deviating from design without approval

## 📊 Key Documentation


### Architecture
- `docs/architecture/PROJECT_STRUCTURE.md` - Complete architecture
- `docs/architecture/database_design.md` - Database schema
- `docs/analysis/python_code_review.md` - Python expert review

### Development Guides
- `docs/guides/configuration-guide.md` - Setup and configuration
- `docs/requirements/business-requirements.md` - Business needs (中文)

---
**Version**: v2.0
**Last updated**: 2025-10-13