# EVO-ASM 项目上下文

## 项目目标

构建一个演化 Agent-Based 金融市场，研究核心问题：

> **市场中的 Alpha（超额收益）是否会因为策略竞争而消失？**

通过四组递进实验（E1 无演化基线 → E2 资本扩张 → E3 复制机制 → E4 复制+突变）逐步激活演化机制，独立识别每个机制的因果贡献。

## 当前状态（2026-06-11）

| 组件 | 状态 |
|------|------|
| 数学模型（MODEL_SPEC.md） | ✅ 完成 |
| 代码实现（20 个模块） | ✅ 完成 |
| 单元测试（155 passed） | ✅ 完成 |
| 四组实验（512 次运行） | ✅ 完成 |
| 全部图表（5,055 PNGs） | ✅ 生成 |
| 论文 LaTeX（61 页） | ✅ 完成 |
| 中文编码修复 | ✅ UTF-8 无 BOM |
| 文字润色（消除 AI 感） | ✅ 完成 |

## 关键文件

| 文件 | 路径 | 用途 |
|------|------|------|
| 研究方案 | `docs/REASEARCH_PLAN.md` | 文献综述、研究问题、假设 |
| 模型规格 | `docs/MODEL_SPEC.md` | 数学符号定义 |
| 软件架构 | `docs/ARCHITECTURE.md` | 类设计、模块职责 |
| 实验设计 | `docs/EXPERIMENTS.md` | 四组实验详细方案 |
| 图表规格 | `docs/PLOT_SPEC.md` | 所有图表的生成脚本规格 |
| 论文主文件 | `paper/thesis/main.tex` | LaTeX 入口 |
| 论文 PDF | `paper/thesis/main.pdf` | 61 页终稿 |

## 工作原则

1. **研究目标优先于软件工程目标。** 代码整洁是手段，回答研究问题是目的。
2. **所有代码必须对应论文中的模型。** 代码中的每一步操作应在 `MODEL_SPEC.md` 中找到数学定义。
3. **不允许添加与研究问题无关的功能。** 别写"可能有用"的代码——只写"回答问题需要"的代码。
4. **每次开发前先阅读：** `docs/` 中的相关文档。
5. **每完成一个模块：** 编写测试 → 更新文档 → 输出实验影响。
6. **如发现设计问题：** 不要直接修改代码。先提出设计建议，经审查后再实施。

## 编译与运行

```bash
# 安装依赖
pip install mesa numpy pandas matplotlib pytest scipy

# 运行测试
pytest tests/ -v

# 编译论文
cd paper/thesis
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

> **注意：** 编译前需关闭 PDF 预览器（福昕/Adobe），否则 `main.pdf` 被锁定导致 `dvipdfmx:fatal: Unable to open` 错误。

## 编码注意事项

- 所有 `.tex` 文件统一使用 **UTF-8 无 BOM** 编码
- 论文编译需要 **SimSun（宋体）** 字体（Windows 自带）
- PowerShell 写入中文文件使用 `[System.IO.File]::WriteAllText(path, content, $utf8)` 而非 `Set-Content` 或 `Out-File`
- `@"..."@`（双引号 here-string）会解析 `$` 破坏 LaTeX 数学模式——使用 `@'...'@`（单引号 here-string）

## Git 工作流

- 分支前缀：`codex/`
- 当前开发分支：`codex/evo-asm-full`
- 原始仓库：`C:\seelf\大三下\主修毕设`（`main` 分支）
- 同步命令：从 GitHub pull → merge