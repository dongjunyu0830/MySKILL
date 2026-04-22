#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def zh_templates(project_name: str) -> dict[str, str]:
    return {
        "memory/README.md": """# AI 三层记忆

本目录用于给当前仓库提供可持久化、可治理的 AI 外部记忆，配合 Codex 使用。

## 目录结构

- `session/`：当前任务的短期记忆，记录目标、涉及文件、临时结论和待确认问题。
- `project/`：当前仓库的中期记忆，沉淀项目结构、技术约束、稳定决策和排障经验。
- `long_term/`：偏长期的协作记忆，记录用户偏好和可跨任务复用的协作模式。

## 使用顺序

1. 开始任务前，先读 `project/` 和 `long_term/`。
2. 执行任务时，在 `session/active/` 创建或更新会话记录。
3. 任务结束后，把稳定信息从 `session/` 晋升到 `project/` 或 `long_term/`。

## 晋升原则

- 只对当前任务有用的信息：留在 `session/`
- 对当前仓库未来任务仍有价值的信息：写入 `project/`
- 跨项目仍然适用的偏好和方法：写入 `long_term/`

## 维护建议

- 优先更新已有记忆文件，避免相同结论散落在多个位置。
- 记忆内容以摘要为主，不直接复制大量对话。
- 每月或在关键版本迭代后复核一次 `project/` 中的稳定结论。
""",
        "memory/project/README.md": """# 项目记忆说明

`project/` 保存当前仓库的稳定知识，是 Codex 进入本项目后应优先读取的记忆层。

## 文件分工

- `project.md`：项目概览、启动方式、目录职责。
- `architecture.md`：页面入口、模块关系、运行链路。
- `decisions.md`：已确认的实现策略和技术约束。
- `debugging.md`：常见问题、排障入口、检查清单。
- `glossary.md`：项目术语和关键对象说明。
""",
        "memory/project/project.md": f"""# 项目概览

## 基本信息

- 项目名称：`{project_name}`
- 项目类型：`[待补充]`
- 包管理：`[待补充]`
- 启动命令：`[待补充]`
- 构建命令：`[待补充]`
- 预览/测试命令：`[待补充]`

## 当前目标定位

- `[待补充：该仓库的主要用途与当前阶段目标]`

## 关键目录

- `[待补充：目录 -> 职责]`

## 当前已知约束

- `[待补充：稳定约束、边界、迁移策略等]`
""",
        "memory/project/architecture.md": """# 架构与运行链路

## 总体结构

- `[待补充：应用形态、入口模式、核心模块关系]`

## 关键入口

- `[待补充：主入口、子入口、页面入口]`

## 数据或调用链路

- `[待补充：接口代理、状态流转、关键依赖]`

## 实现含义

- `[待补充：后续修改时必须留意的结构性事实]`
""",
        "memory/project/decisions.md": """# 项目决策

## 已确认决策

### 1. [待补充：决策标题]
- 结论：
- 原因：

## 当前应关注的实现事实

### 1. [待补充：实现事实标题]
- 现状：
- 含义：

## 更新规则

- 只有被验证过、未来仍可能复用的结论才写入本文件。
- 临时排查结论不要直接写入这里，应先留在 `memory/session/`。
""",
        "memory/project/debugging.md": """# 排障与检查清单

## 常见问题 1

优先检查：

- `[待补充]`

## 常见问题 2

优先检查：

- `[待补充]`

## 维护建议

- 修改实现后，如结论具有复用价值，同步更新本文件。
""",
        "memory/project/glossary.md": """# 项目术语表

## 术语 1

`[待补充]`：`[待补充说明]`

## 术语 2

`[待补充]`：`[待补充说明]`
""",
        "memory/session/README.md": """# 会话记忆说明

`session/` 用于保存当前任务或最近任务的临时记忆，不直接作为长期规则来源。

## 子目录

- `active/`：进行中的任务记录。
- `archive/`：已完成任务的归档记录。
- `templates/`：会话模板。

## 文件命名建议

- 推荐格式：`YYYY-MM-DD-任务简称.md`
- 示例：`2026-03-31-fix-proxy-config.md`

## 记录重点

- 当前目标
- 涉及文件
- 已确认结论
- 待确认问题
- 下一步动作
""",
        "memory/session/active/README.md": """# 进行中的会话记录

把当前任务或尚未关闭的问题记录放在这里。

建议每个任务单独成文，便于后续晋升和归档。
""",
        "memory/session/archive/README.md": """# 会话归档

已完成或暂时关闭的任务记录可移到这里，便于后续追溯实现过程与历史判断。

归档前建议先把稳定结论晋升到 `memory/project/` 或 `memory/long_term/`。
""",
        "memory/session/templates/session-template.md": """# 会话记录模板

## 当前目标

## 背景

## 涉及文件
- 

## 执行计划
1. 
2. 
3. 

## 已确认结论
- 

## 待确认问题
- 

## 操作记录
- 

## 最终结果

## 是否需要晋升
- 项目记忆：
- 长期记忆：
""",
        "memory/long_term/README.md": """# 长期记忆说明

`long_term/` 保存跨任务仍稳定成立的协作偏好与工作模式。

这里的内容不应绑定某个具体页面实现细节，而应偏向：

- 用户交流偏好
- 交付风格
- 多次验证有效的协作方法
""",
        "memory/long_term/user_preferences.md": """# 用户协作偏好

以下内容基于当前对话与协作习惯整理，后续如有新的明确偏好，应更新本文件：

- 默认使用中文输出。
- 优先给出可执行的实操步骤，而不是只讲概念。
- 当方案涉及落地时，尽量直接映射到当前项目结构和文件路径。
- 回答里优先说明“怎么做”，再补充“为什么这样做”。
- 如需修改仓库，优先采用小步、可验证的改动方式。
""",
        "memory/long_term/collaboration_patterns.md": """# 协作模式沉淀

## 当前适用模式

- 先读取项目记忆，再开始实现。
- 对非一次性问题，优先建立可复用模板或目录结构。
- 修改完成后，把稳定结论回填到项目记忆，而不是只停留在当前会话。

## 记忆分层规则

- 会话层：记录当前任务状态和临时判断。
- 项目层：记录当前仓库的稳定结构、约束和经验。
- 长期层：记录跨任务可复用的偏好和协作习惯。

## 禁止项

- 不把敏感信息写进记忆文件。
- 不把未经验证的猜测直接晋升到项目层或长期层。
""",
    }


def en_templates(project_name: str) -> dict[str, str]:
    return {
        "memory/README.md": """# AI Memory

This directory stores governed external memory for the repository so Codex can retain task context, project knowledge, and long-term collaboration preferences.

## Structure

- `session/`: short-term task memory for goals, touched files, temporary conclusions, and open questions
- `project/`: stable repository knowledge such as structure, constraints, decisions, and debugging notes
- `long_term/`: collaboration preferences and reusable working patterns that stay useful across tasks

## Recommended workflow

1. Read `project/` and `long_term/` before implementation.
2. Create or update a task note in `session/active/` during the task.
3. Promote stable conclusions after the task.

## Promotion rules

- task-only information stays in `session/`
- stable repository knowledge goes to `project/`
- cross-project preferences and methods go to `long_term/`
""",
        "memory/project/README.md": """# Project Memory

`project/` stores stable repository knowledge that Codex should read before working.

## Files

- `project.md`: overview, commands, directory roles
- `architecture.md`: entry points, module relationships, runtime flow
- `decisions.md`: confirmed strategies and durable constraints
- `debugging.md`: troubleshooting checklists and common failure modes
- `glossary.md`: project terms and key objects
""",
        "memory/project/project.md": f"""# Project Overview

## Basics

- Project name: `{project_name}`
- Project type: `[TODO]`
- Package manager: `[TODO]`
- Start command: `[TODO]`
- Build command: `[TODO]`
- Preview or test command: `[TODO]`

## Current goal

- `[TODO: summarize the repository purpose and current focus]`

## Key directories

- `[TODO: directory -> responsibility]`

## Known constraints

- `[TODO: stable constraints, migration rules, or boundaries]`
""",
        "memory/project/architecture.md": """# Architecture And Runtime Flow

## Overall structure

- `[TODO: app shape, entry model, major module relationships]`

## Key entry points

- `[TODO: app entry, page entry, build/runtime entry]`

## Data and call flow

- `[TODO: API flow, state flow, proxy or environment behavior]`

## Implementation implications

- `[TODO: structural facts future edits must respect]`
""",
        "memory/project/decisions.md": """# Project Decisions

## Confirmed decisions

### 1. [TODO: decision title]
- Decision:
- Why:

## Important implementation facts

### 1. [TODO: fact title]
- Current state:
- Implication:

## Update rules

- Only write validated conclusions that are likely to help future tasks.
- Keep temporary debugging conclusions in `memory/session/` first.
""",
        "memory/project/debugging.md": """# Debugging Checklist

## Common issue 1

Check first:

- `[TODO]`

## Common issue 2

Check first:

- `[TODO]`

## Maintenance notes

- Update this file when a debugging conclusion becomes broadly reusable.
""",
        "memory/project/glossary.md": """# Glossary

## Term 1

`[TODO]`: `[TODO description]`

## Term 2

`[TODO]`: `[TODO description]`
""",
        "memory/session/README.md": """# Session Memory

`session/` stores short-term notes for the current task or recently completed tasks. It should not be treated as a long-term rule source.

## Subdirectories

- `active/`: ongoing task notes
- `archive/`: completed task notes
- `templates/`: note templates
""",
        "memory/session/active/README.md": """# Active Session Notes

Keep notes for in-progress tasks here.
""",
        "memory/session/archive/README.md": """# Archived Session Notes

Move completed or paused task notes here after promoting stable conclusions to `project/` or `long_term/`.
""",
        "memory/session/templates/session-template.md": """# Session Note Template

## Goal

## Background

## Touched Files
- 

## Plan
1. 
2. 
3. 

## Confirmed Conclusions
- 

## Open Questions
- 

## Work Log
- 

## Final Result

## Promotion Needed
- Project memory:
- Long-term memory:
""",
        "memory/long_term/README.md": """# Long-Term Memory

`long_term/` stores collaboration preferences and reusable working patterns that stay valid across tasks.
""",
        "memory/long_term/user_preferences.md": """# User Preferences

Update this file only when the user states a clear preference or the same preference is repeatedly confirmed.

- Preferred response language: `[TODO]`
- Preferred explanation style: `[TODO]`
- Preferred delivery style: `[TODO]`
""",
        "memory/long_term/collaboration_patterns.md": """# Collaboration Patterns

## Effective patterns

- Read project memory before implementation.
- Record reusable conclusions in durable layers after the task.

## Layering rules

- Session layer: task status and temporary judgments
- Project layer: stable repository knowledge
- Long-term layer: cross-project preferences and habits

## Never do

- Do not store secrets in memory files.
- Do not promote unverified guesses into durable layers.
""",
    }


TEMPLATE_FACTORIES = {
    "zh": zh_templates,
    "en": en_templates,
}

DIRECTORIES = [
    "memory",
    "memory/project",
    "memory/session",
    "memory/session/active",
    "memory/session/archive",
    "memory/session/templates",
    "memory/long_term",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="在仓库中初始化一套受治理的三层 Codex memory 结构。"
    )
    parser.add_argument("target", help="目标仓库根目录。")
    parser.add_argument(
        "--language",
        choices=sorted(TEMPLATE_FACTORIES.keys()),
        default="zh",
        help="模板语言，默认 `zh`。",
    )
    parser.add_argument(
        "--project-name",
        help="模板占位中使用的项目名，默认取目标目录名。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已有文件，而不是只创建缺失文件。",
    )
    return parser.parse_args()


def ensure_directories(root: Path) -> None:
    for rel_dir in DIRECTORIES:
        (root / rel_dir).mkdir(parents=True, exist_ok=True)


def write_templates(root: Path, templates: dict[str, str], overwrite: bool) -> tuple[list[Path], list[Path]]:
    created: list[Path] = []
    skipped: list[Path] = []
    for rel_path, content in templates.items():
        abs_path = root / rel_path
        if abs_path.exists() and not overwrite:
            skipped.append(abs_path)
            continue
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content.rstrip() + "\n", encoding="utf-8")
        created.append(abs_path)
    return created, skipped


def main() -> int:
    args = parse_args()
    root = Path(args.target).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    project_name = args.project_name or root.name
    templates = TEMPLATE_FACTORIES[args.language](project_name)

    ensure_directories(root)
    created, skipped = write_templates(root, templates, args.overwrite)

    print(f"目标目录：{root}")
    print(f"模板语言：{args.language}")
    print(f"项目名称：{project_name}")
    print(f"创建/更新文件数：{len(created)}")
    for path in created:
        print(f"  CREATE {path}")
    print(f"跳过已有文件数：{len(skipped)}")
    for path in skipped:
        print(f"  SKIP   {path}")

    print("下一步：检查仓库实际情况，并补齐 `memory/project/*.md` 中的项目专属事实。")
    print("下一步：如果仓库使用 `AGENTS.md`，把 memory 工作流接入其中。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
