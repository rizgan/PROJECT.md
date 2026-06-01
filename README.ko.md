# PROJECT.md

**Language / Язык / 语言 / 言語 / 언어:**
[English](README.md) · [中文](README.zh.md) · [हिंदी](README.hi.md) · [Русский](README.ru.md) · [Português](README.pt.md) · [Español](README.es.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

---

**멀티 에이전트 파이프라인**을 위한 개방형 파일 형식.

하나의 Markdown 파일이 전체 프로젝트를 설명합니다: 어떤 에이전트가 실행되는지, 어떤 순서로, 어떤 모델을 사용하여, 무엇을 허용하는지, 그리고 실패 시 무슨 일이 발생하는지. 오케스트레이터가 파일을 읽고 파이프라인을 실행합니다 — 글루 코드 없이.

[AGENTS.md](https://agents.md)가 **하나의 에이전트**에게 저장소에서 어떻게 행동할지 알려준다면, PROJECT.md는 **오케스트레이터**에게 전체 프로젝트를 어떻게 실행할지 알려줍니다.

---

## 최소 예시

```markdown
---
spec_version: 0.1
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

이것이 유효한 PROJECT.md입니다. 나머지는 모두 선택 사항입니다.

---

## 왜

오늘날, 멀티 에이전트 파이프라인을 정의하는 것은 오케스트레이션 코드를 작성하는 것을 의미합니다. 새 프로젝트마다 새 클래스, 새 배선, 새 설정 파일이 필요합니다. 파이프라인 정의는 코드가 아닌 데이터입니다 — 파일에 속합니다.

PROJECT.md가 바로 그 파일입니다.

---

## 설계 원칙

1. **Markdown + YAML 프론트매터.** 새로운 언어를 배울 필요가 없습니다.
2. **코어는 작게 유지.** 80%의 파이프라인에 필요하지 않은 기능은 Extensions로, Core에는 넣지 않습니다.
3. **선언적, 명령적이지 않음.** 파일은 *무엇을* 설명하고; 오케스트레이터는 *어떻게*를 결정합니다.
4. **프레임워크 독립적.** 어떤 오케스트레이터도 구현할 수 있습니다.

---

## 비교

| 기능                                  | AGENTS.md | SKILL.md  | CrewAI yaml   | LangGraph     | Google ADK    | PROJECT.md    |
| ------------------------------------- | :-------: | :-------: | :-----------: | :-----------: | :-----------: | :-----------: |
| 형식                                  | Markdown  | Markdown  | 2× YAML       | Python 코드   | Python 코드   | Markdown+YAML |
| 작성자 프로필                         | 누구든지  | 누구든지  | 개발자        | 개발자        | 개발자        | 누구든지      |
| 범위                                  | 에이전트1개| 스킬 1개  | 파이프라인    | 파이프라인    | 파이프라인    | 파이프라인    |
| 단일 파일                             | ✅        | ✅        | ❌ (2개 파일) | ❌ (코드)     | ❌ (코드)     | ✅            |
| 멀티 에이전트 파이프라인              | ❌        | ❌        | ✅            | ✅            | ✅            | ✅            |
| 순차 실행                             | —         | —         | ✅            | ✅            | ✅            | ✅            |
| 병렬 실행                             | —         | —         | ✅            | ✅            | ✅            | ✅ (`wave`)   |
| 명시적 데이터 의존성                  | —         | —         | 암시적        | ✅ (엣지)     | 암시적        | ✅ (`after`)  |
| 루프 / 판정자 재시도                  | —         | —         | 부분적        | ✅            | ✅            | ✅ (ext)      |
| 계층형 에이전트                       | —         | —         | ✅            | ✅            | ✅            | ❌ (v0.1)     |
| 에이전트별 모델 및 공급자             | —         | —         | ✅            | ✅            | ✅            | ✅ (ext)      |
| 도구 선언                             | 부분적    | 부분적    | ✅            | ✅            | ✅            | ✅ (ext)      |
| 타입드 I/O (스키마)                   | —         | —         | 부분적        | ✅            | ✅ (Pydantic) | ✅ (ext)      |
| 시크릿 참조                           | —         | —         | 코드 수준     | 코드 수준     | 코드 수준     | ✅ (ext)      |
| 실행 간 메모리                        | —         | —         | 코드 수준     | ✅            | 코드 수준     | ✅ (ext)      |
| 라이프사이클 훅                       | —         | —         | 코드 수준     | 코드 수준     | 코드 수준     | ✅ (ext)      |
| 비용 / 예산 가드레일                  | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| 작업 제약 (허용/거부)                 | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| 스케줄링 (cron)                       | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| 실행 모드 (dry/test/prod)             | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| 프레임워크 독립적                     | ✅        | ✅        | ❌ (CrewAI)   | ❌ (LangGraph)| ❌ (ADK)      | ✅            |
| PR 리뷰에서 사람이 읽을 수 있는 diff  | ✅        | ✅        | ✅            | ❌            | ❌            | ✅            |

**읽는 방법:** AGENTS.md와 SKILL.md는 *하나의* 단위(에이전트, 스킬)를 설명합니다. CrewAI, LangGraph, ADK는 코드나 프레임워크 특정 스키마로 *파이프라인*을 설명합니다. PROJECT.md는 파이프라인 레이어에서 **선언적 Markdown**이자 **프레임워크 독립적**인 유일한 형식입니다.

> `CLAUDE.md`, `GEMINI.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.windsurfrules`, `.clinerules`과 같은 IDE 특정 파일은 의도적으로 제외되었습니다 — 이들은 AGENTS.md와 같은 범위(단일 에이전트, 하나의 저장소)를 공유하며, 어떤 도구가 읽는지만 다릅니다.

---

## 사양

- [SPEC.md](SPEC.md) — 전체 사양 (Core + Extensions)
- [examples/PROJECT-minimal.md](examples/PROJECT-minimal.md) — Core 전용 파이프라인
- [examples/PROJECT-news.md](examples/PROJECT-news.md) — 완전한 실세계 예시
- [validator/](validator/) — 참조 Python 검증기

---

## 상태

`v0.1` — 초안. `v1.0`까지 중대한 변경이 가능합니다. 파일에 `spec_version`을 고정하세요.

---

## 기여

Issue와 PR을 환영합니다 — 특히:
- 격차를 드러내는 실제 사용 사례
- 오케스트레이터 구현
- 사양에 있어서는 *안 되는* 것에 대한 피드백

## 라이선스

Apache-2.0 — [LICENSE](LICENSE) 참조.
