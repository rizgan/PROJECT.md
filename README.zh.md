# PROJECT.md

![PROJECT.md](project.md.png)

**Language / Язык / 语言 / 言語 / 언어:**
[English](README.md) · [中文](README.zh.md) · [हिंदी](README.hi.md) · [Русский](README.ru.md) · [Português](README.pt.md) · [Español](README.es.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

---

**多智能体管道**的开放文件格式。

一个 Markdown 文件描述整个项目：哪些智能体运行、以何种顺序、使用哪些模型、允许它们做什么，以及失败时会发生什么。编排器读取文件并执行管道——无需粘合代码。

如果 [AGENTS.md](https://agents.md) 告诉**一个智能体**如何在仓库中运行，PROJECT.md 则告诉**编排器**如何运行整个项目。

---

## 最简示例

```markdown
---
spec_version: 0.5
id: PROJECT-01
name: Hello pipeline
---

## Agents

### writer
wave: 1
Write a one-paragraph summary of: {{ topic }}.

### reviewer
wave: 2
after: writer
Check the summary for factual errors. Return `approved` or `rejected`.
```

这是一个有效的 PROJECT.md。其余内容均为可选项。

---

## 为什么

如今，定义多智能体管道意味着编写编排代码。每个新项目都需要新的类、新的连接、新的配置文件。管道定义是数据，而非代码——它属于一个文件。

PROJECT.md 就是那个文件。

---

## 设计原则

1. **Markdown + YAML 前置信息。** 无需学习新语言。
2. **核心保持精简。** 如果某功能不被 80% 的管道所需，它就归入扩展，而非核心。
3. **声明式，而非命令式。** 文件描述*是什么*；编排器决定*如何做*。
4. **框架无关。** 任何编排器都可以实现它。

---

## 对比分析

| 功能                               | AGENTS.md | SKILL.md  | CrewAI yaml   | LangGraph     | Google ADK    | PROJECT.md    |
| ---------------------------------- | :-------: | :-------: | :-----------: | :-----------: | :-----------: | :-----------: |
| 格式                               | Markdown  | Markdown  | 2× YAML       | Python 代码   | Python 代码   | Markdown+YAML |
| 作者类型                           | 任何人    | 任何人    | 开发者        | 开发者        | 开发者        | 任何人        |
| 范围                               | 1 个智能体| 1 个技能  | 管道          | 管道          | 管道          | 管道          |
| 单文件                             | ✅        | ✅        | ❌ (2 个文件) | ❌ (代码)     | ❌ (代码)     | ✅            |
| 多智能体管道                       | ❌        | ❌        | ✅            | ✅            | ✅            | ✅            |
| 顺序执行                           | —         | —         | ✅            | ✅            | ✅            | ✅            |
| 并行执行                           | —         | —         | ✅            | ✅            | ✅            | ✅ (`wave`)   |
| 显式数据依赖                       | —         | —         | 隐式          | ✅ (边)       | 隐式          | ✅ (`after`)  |
| 循环 / 裁判重试                    | —         | —         | 部分          | ✅            | ✅            | ✅ (扩展)     |
| 层次化智能体                       | —         | —         | ✅            | ✅            | ✅            | ✅ (扩展)     |
| 每智能体模型和提供商               | —         | —         | ✅            | ✅            | ✅            | ✅ (扩展)     |
| 工具声明                           | 部分      | 部分      | ✅            | ✅            | ✅            | ✅ (扩展)     |
| 类型化 I/O（模式）                 | —         | —         | 部分          | ✅            | ✅ (Pydantic) | ✅ (扩展)     |
| 密钥引用                           | —         | —         | 代码层        | 代码层        | 代码层        | ✅ (扩展)     |
| 跨运行记忆                         | —         | —         | 代码层        | ✅            | 代码层        | ✅ (扩展)     |
| 生命周期钩子                       | —         | —         | 代码层        | 代码层        | 代码层        | ✅ (扩展)     |
| 成本 / 预算护栏                    | —         | —         | ❌            | ❌            | ❌            | ✅ (扩展)     |
| 操作约束（允许/拒绝）              | —         | —         | ❌            | ❌            | ❌            | ✅ (扩展)     |
| 调度（cron）                       | —         | —         | ❌            | ❌            | ❌            | ✅ (扩展)     |
| 运行模式（干运行/测试/生产）       | —         | —         | ❌            | ❌            | ❌            | ✅ (扩展)     |
| 框架无关                           | ✅        | ✅        | ❌ (CrewAI)   | ❌ (LangGraph)| ❌ (ADK)      | ✅            |
| PR 审查中人类可读的差异            | ✅        | ✅        | ✅            | ❌            | ❌            | ✅            |

**解读：** AGENTS.md 和 SKILL.md 描述*一个*单元（一个智能体、一项技能）。CrewAI、LangGraph 和 ADK 以代码或框架特定模式描述*管道*。PROJECT.md 是唯一既**声明式 Markdown** 又**框架无关**的管道层格式。

PROJECT.md 可以通过扩展可选地引用现有的 AGENTS.md 和 SKILL.md 文件，同时也可以完全不使用它们。

> IDE 特定文件如 `CLAUDE.md`、`GEMINI.md`、`.cursorrules`、`.github/copilot-instructions.md`、`.windsurfrules`、`.clinerules` 被有意省略——它们与 AGENTS.md 的范围相同（单一智能体，一个仓库），只是读取工具不同。

---

## 规范

- [SPEC.md](SPEC.md) — 完整规范（核心 + 扩展）
- [examples/PROJECT-minimal.md](examples/PROJECT-minimal.md) — 仅核心管道
- [examples/PROJECT-news.md](examples/PROJECT-news.md) — 完整的真实世界示例
- [validator/](validator/) — 参考 Python 验证器

---

## 状态

`v0.5` — 草案。在 `v1.0` 之前可能有重大变更。请在文件中固定 `spec_version`。

---

## 贡献

欢迎提交 Issue 和 PR，特别是：
- 揭示缺口的真实用例
- 编排器实现
- 对于不应包含在规范中的内容的反馈

## 许可证

Apache-2.0 — 参见 [LICENSE](LICENSE)。
