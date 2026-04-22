---
name: project-memory-bootstrap
description: 为仓库创建或对齐一套适配 Codex 的项目记忆系统，包含 `memory/session`、`memory/project`、`memory/long_term` 三层结构，以及接入 `AGENTS.md` 的工作流。适用于仓库需要初始化可复用的 AI memory 体系、现有 `memory/` 目录不完整或规则不一致，或希望让 Codex 为后续任务沉淀会话记录、稳定项目知识和长期协作偏好时使用。
---

# 项目记忆初始化

使用这个 skill 为仓库创建或修复一套受治理的 `memory/` 系统。

当你需要查看文件结构、晋升规则，或参考本仓库抽取出的 memory 模式时，读取 `references/memory-pattern.md`。

## 工作流

### 1. 写入前先检查仓库

先读取仓库上下文：

- 如果存在，先读 `AGENTS.md`
- `README.md`
- 包管理、构建相关文件和顶层目录
- 任何已有的 `memory/` 文件

重点识别：

- 项目类型，以及启动/构建命令
- 主要目录与运行入口
- 稳定的技术约束
- 仓库是否已有 `memory/`，以及缺了哪些部分

不要凭空编造仓库事实。如果检查后仍不确定，就保持通用占位，或标记为后续补充。

### 2. 先搭骨架

运行 bootstrap 脚本，创建标准目录树和模板文件。

示例：

```powershell
python "C:\Users\ws\.codex\skills\project-memory-bootstrap\scripts\bootstrap_memory.py" "D:\path\to\repo"
```

默认行为：

- 只创建缺失文件
- 保留已有文件内容不变
- 使用 UTF-8 编码写入 Markdown
- 默认生成中文模板

常用参数：

```powershell
python "...\\bootstrap_memory.py" "D:\path\to\repo" --language en
python "...\\bootstrap_memory.py" "D:\path\to\repo" --overwrite
python "...\\bootstrap_memory.py" "D:\path\to\repo" --project-name my-repo
```

### 3. 用真实仓库事实补齐项目层

骨架搭完后，再基于仓库检查结果填写这些文件：

- `memory/project/project.md`：项目概览、命令、关键目录、已知约束
- `memory/project/architecture.md`：入口、模块关系、运行链路
- `memory/project/decisions.md`：确认过的策略和长期有效的约束
- `memory/project/debugging.md`：常见故障模式和排查清单
- `memory/project/glossary.md`：项目术语

项目层只记录稳定知识。

### 4. 谨慎填写长期层

`memory/long_term/` 只保留协作偏好和可复用的工作模式。

- 只有在用户明确提出，或被多次稳定验证后，才写入 `user_preferences.md`
- 只有确实跨任务复用有效的方法，才写入 `collaboration_patterns.md`

不要把页面实现细节或一次性排查信息写进长期层。

### 5. 把工作流接到 `AGENTS.md`

如果仓库存在 `AGENTS.md`，就补充或更新 memory 工作流说明，让后续 Codex 知道：

- 实现前应读取哪些 memory 文件
- 任务过程中要维护会话记录
- 任务结束后应把哪些稳定结论晋升到哪里
- 如何处理敏感信息和过期结论

如果 `AGENTS.md` 里已经有类似内容，优先做最小合并，不要重复堆叠章节。

### 6. 安全处理已有 memory

当仓库已经存在 `memory/` 时：

- 保留已有有效内容
- 补齐缺失文件
- 合并重复规则
- 对过期结论做更新或替换，而不是继续追加互相矛盾的内容

优先小改，不要整块重写。

## 编写规则

- 以摘要为主，不直接粘贴大段对话
- 不写入密钥、凭证或其他敏感信息
- 临时判断放在 `memory/session/`
- 稳定的仓库知识放在 `memory/project/`
- 跨项目的协作偏好放在 `memory/long_term/`

## 交付检查清单

结束前确认：

- `memory/` 已具备预期的三层结构
- `session/templates/session-template.md` 已存在
- 项目层内容来自真实仓库事实
- 如有需要，`AGENTS.md` 已接入 memory 工作流
- 没有写入敏感信息或未经验证的推测
