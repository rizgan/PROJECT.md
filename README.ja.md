# PROJECT.md

![PROJECT.md](project.md.png)

**Language / Язык / 语言 / 言語 / 언어:**
[English](README.md) · [中文](README.zh.md) · [हिंदी](README.hi.md) · [Русский](README.ru.md) · [Português](README.pt.md) · [Español](README.es.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

---

**マルチエージェントパイプライン**のためのオープンファイルフォーマット。

1つのMarkdownファイルがプロジェクト全体を記述します：どのエージェントが実行されるか、どの順序で、どのモデルを使用して、何が許可されているか、そして失敗したときに何が起こるか。オーケストレーターはファイルを読み取り、パイプラインを実行します — グルーコードは不要です。

[AGENTS.md](https://agents.md) が**1つのエージェント**にリポジトリでの振る舞いを伝えるのと同様に、PROJECT.md は**オーケストレーター**にプロジェクト全体の実行方法を伝えます。

---

## 最小限の例

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

これは有効なPROJECT.mdです。それ以外はすべてオプションです。

---

## なぜ

現在、マルチエージェントパイプラインを定義するにはオーケストレーションコードを書く必要があります。新しいプロジェクトごとに新しいクラス、新しい配線、新しい設定ファイルが必要です。パイプラインの定義はデータであり、コードではありません — ファイルに属しています。

PROJECT.mdがそのファイルです。

---

## 設計原則

1. **Markdown + YAMLフロントマター。** 新しい言語を学ぶ必要はありません。
2. **コアは小さく保つ。** 80%のパイプラインに必要でない機能は、コアではなく拡張機能に入ります。
3. **宣言的、命令的ではない。** ファイルは*何を*記述します；オーケストレーターが*どのように*を決定します。
4. **フレームワーク非依存。** どのオーケストレーターでも実装できます。

---

## 比較

| 機能                                    | AGENTS.md | SKILL.md  | CrewAI yaml   | LangGraph     | Google ADK    | PROJECT.md    |
| --------------------------------------- | :-------: | :-------: | :-----------: | :-----------: | :-----------: | :-----------: |
| フォーマット                            | Markdown  | Markdown  | 2× YAML       | Pythonコード  | Pythonコード  | Markdown+YAML |
| 著者プロフィール                        | 誰でも    | 誰でも    | 開発者        | 開発者        | 開発者        | 誰でも        |
| スコープ                                | 1エージェント| 1スキル | パイプライン  | パイプライン  | パイプライン  | パイプライン  |
| 単一ファイル                            | ✅        | ✅        | ❌ (2ファイル)| ❌ (コード)   | ❌ (コード)   | ✅            |
| マルチエージェントパイプライン          | ❌        | ❌        | ✅            | ✅            | ✅            | ✅            |
| 逐次実行                                | —         | —         | ✅            | ✅            | ✅            | ✅            |
| 並列実行                                | —         | —         | ✅            | ✅            | ✅            | ✅ (`wave`)   |
| 明示的なデータ依存関係                  | —         | —         | 暗黙的        | ✅ (エッジ)   | 暗黙的        | ✅ (`after`)  |
| ループ / ジャッジによる再試行           | —         | —         | 部分的        | ✅            | ✅            | ✅ (ext)      |
| 階層型エージェント                      | —         | —         | ✅            | ✅            | ✅            | ❌ (v0.1)     |
| エージェントごとのモデルとプロバイダー  | —         | —         | ✅            | ✅            | ✅            | ✅ (ext)      |
| ツール宣言                              | 部分的    | 部分的    | ✅            | ✅            | ✅            | ✅ (ext)      |
| 型付きI/O（スキーマ）                   | —         | —         | 部分的        | ✅            | ✅ (Pydantic) | ✅ (ext)      |
| シークレットの参照                      | —         | —         | コードレベル  | コードレベル  | コードレベル  | ✅ (ext)      |
| 実行間メモリ                            | —         | —         | コードレベル  | ✅            | コードレベル  | ✅ (ext)      |
| ライフサイクルフック                    | —         | —         | コードレベル  | コードレベル  | コードレベル  | ✅ (ext)      |
| コスト / 予算ガードレール               | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| アクション制約（許可/拒否）             | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| スケジューリング（cron）                | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| 実行モード（dry/test/prod）             | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| フレームワーク非依存                    | ✅        | ✅        | ❌ (CrewAI)   | ❌ (LangGraph)| ❌ (ADK)      | ✅            |
| PRレビューでの人間可読なdiff            | ✅        | ✅        | ✅            | ❌            | ❌            | ✅            |

**読み方:** AGENTS.mdとSKILL.mdは*1つ*のユニット（エージェント、スキル）を記述します。CrewAI、LangGraph、ADKはコードやフレームワーク固有のスキーマで*パイプライン*を記述します。PROJECT.mdは、パイプライン層において**宣言的Markdown**かつ**フレームワーク非依存**の唯一のフォーマットです。

> `CLAUDE.md`、`GEMINI.md`、`.cursorrules`、`.github/copilot-instructions.md`、`.windsurfrules`、`.clinerules` などのIDE固有ファイルは意図的に省略されています — これらはAGENTS.mdと同じスコープ（単一エージェント、1つのリポジトリ）を持ち、どのツールがそれらを読むかが異なるだけです。

---

## 仕様

- [SPEC.md](SPEC.md) — 完全な仕様（Core + Extensions）
- [examples/PROJECT-minimal.md](examples/PROJECT-minimal.md) — Coreのみのパイプライン
- [examples/PROJECT-news.md](examples/PROJECT-news.md) — 完全な実世界の例
- [validator/](validator/) — 参照Pythonバリデーター

---

## ステータス

`v0.1` — ドラフト。`v1.0`まで破壊的変更の可能性があります。ファイルに`spec_version`を固定してください。

---

## 貢献

IssueとPRを歓迎します — 特に：
- ギャップを露呈する実際のユースケース
- オーケストレーターの実装
- 仕様に含めるべき*でない*ものへのフィードバック

## ライセンス

Apache-2.0 — [LICENSE](LICENSE) を参照。
