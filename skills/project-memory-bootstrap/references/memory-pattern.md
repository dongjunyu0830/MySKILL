# 项目记忆模式

本参考文档总结自 `d:\fx_operation_frontend\fx_operation_frontend` 当前使用的 memory 方案。

## 核心设计

把项目记忆构建成一套受治理的三层系统，而不是随意堆放的笔记目录：

- `memory/session/`：短期任务记忆，用来记录进行中的任务和最近完成的工作
- `memory/project/`：稳定的仓库知识，供后续任务优先读取
- `memory/long_term/`：跨任务复用的协作偏好与工作模式

## 必需行为

把 memory 同时当作“目录结构”和“协作工作流”来设计：

1. 实现前先读取 `project/` 和 `long_term/`
2. 任务进行中在 `session/active/` 维护简短记录
3. 任务结束后晋升稳定结论：
   - 项目专属事实 -> `project/`
   - 跨项目偏好 -> `long_term/`
4. 在合适的时候归档已完成的会话记录

## 推荐文件集合

### `memory/`

- `README.md`：说明三层模型、使用顺序、晋升规则和维护建议

### `memory/project/`

- `README.md`：定义项目层职责
- `project.md`：项目概览、启动命令、关键目录、已知约束
- `architecture.md`：入口、模块关系、运行链路、环境行为
- `decisions.md`：已确认的策略、约束和长期有效的实现选择
- `debugging.md`：排查清单、常见故障模式、环境或代理问题
- `glossary.md`：项目术语和关键对象

### `memory/session/`

- `README.md`：说明 active 与 archive 的使用方式
- `templates/session-template.md`：会话记录模板
- `active/README.md`：说明进行中的任务记录
- `archive/README.md`：说明已归档的任务记录

### `memory/long_term/`

- `README.md`：定义长期协作记忆
- `user_preferences.md`：响应风格、交付风格、格式偏好
- `collaboration_patterns.md`：被证明有效的可复用工作方式

## 编写规则

- 以摘要代替大段对话拷贝
- 不写入 secrets、tokens、passwords、private keys 或其他敏感个人信息
- 不要把临时猜测直接晋升到稳定层
- 过期结论要更新或删除，不要继续追加互相矛盾的说明
- 优先更新已有 memory 文件，避免相同结论散落多处

## `AGENTS.md` 接入方式

如果仓库存在 `AGENTS.md`，应把 memory 工作流接进去：

- 实现前：读取关键的项目层和长期层文件
- 执行中：基于会话模板维护任务记录
- 结束后：晋升稳定知识并归档完成的会话记录
- 同时写入晋升规则和敏感信息安全规则

## 创建策略

建议分两步初始化 memory：

1. 先创建目录结构和模板文件
2. 再通过检查仓库实际情况来补齐项目专属内容，而不是靠猜测填写

如果仓库已经有 `memory/` 目录，优先最小化更新，而不是整套覆盖。
