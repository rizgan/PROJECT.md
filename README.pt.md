# PROJECT.md

![PROJECT.md](project.md.png)

**Language / Язык / 语言 / 言語 / 언어:**
[English](README.md) · [中文](README.zh.md) · [हिंदी](README.hi.md) · [Русский](README.ru.md) · [Português](README.pt.md) · [Español](README.es.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

---

Um formato de arquivo aberto para **pipelines multi-agente**.

Um único arquivo Markdown descreve o projeto inteiro: quais agentes são executados, em que ordem, com quais modelos, o que têm permissão de fazer e o que acontece quando falham. Um orquestrador lê o arquivo e executa o pipeline — sem código de cola necessário.

Se [AGENTS.md](https://agents.md) diz a **um agente** como se comportar em um repositório, o PROJECT.md diz a **um orquestrador** como executar um projeto inteiro.

---

## Exemplo mínimo

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

Isso é um PROJECT.md válido. Tudo mais é opcional.

---

## Por quê

Hoje, definir um pipeline multi-agente significa escrever código de orquestração. Cada novo projeto requer novas classes, novas conexões, novos arquivos de configuração. A definição do pipeline é dados, não código — ela pertence a um arquivo.

PROJECT.md é esse arquivo.

---

## Princípios de design

1. **Markdown + YAML frontmatter.** Nenhuma nova linguagem para aprender.
2. **O núcleo permanece pequeno.** Se uma funcionalidade não é necessária para 80% dos pipelines, vai para Extensões, não para o Núcleo.
3. **Declarativo, não imperativo.** O arquivo descreve *o quê*; o orquestrador decide *como*.
4. **Independente de framework.** Qualquer orquestrador pode implementá-lo.

---

## Comparação

| Capacidade                             | AGENTS.md | SKILL.md  | CrewAI yaml   | LangGraph     | Google ADK    | PROJECT.md    |
| -------------------------------------- | :-------: | :-------: | :-----------: | :-----------: | :-----------: | :-----------: |
| Formato                                | Markdown  | Markdown  | 2× YAML       | Código Python | Código Python | Markdown+YAML |
| Perfil do autor                        | qualquer  | qualquer  | desenvolvedor | desenvolvedor | desenvolvedor | qualquer      |
| Escopo                                 | 1 agente  | 1 habilid.| pipeline      | pipeline      | pipeline      | pipeline      |
| Arquivo único                          | ✅        | ✅        | ❌ (2 arquivos)| ❌ (código)  | ❌ (código)   | ✅            |
| Pipeline multi-agente                  | ❌        | ❌        | ✅            | ✅            | ✅            | ✅            |
| Execução sequencial                    | —         | —         | ✅            | ✅            | ✅            | ✅            |
| Execução paralela                      | —         | —         | ✅            | ✅            | ✅            | ✅ (`wave`)   |
| Dependências de dados explícitas       | —         | —         | implícitas    | ✅ (arestas)  | implícitas    | ✅ (`after`)  |
| Loops / retry por juiz                 | —         | —         | parcial       | ✅            | ✅            | ✅ (ext)      |
| Agentes hierárquicos                   | —         | —         | ✅            | ✅            | ✅            | ✅ (ext)      |
| Modelo e provedor por agente           | —         | —         | ✅            | ✅            | ✅            | ✅ (ext)      |
| Declaração de ferramentas              | parcial   | parcial   | ✅            | ✅            | ✅            | ✅ (ext)      |
| I/O tipado (schema)                    | —         | —         | parcial       | ✅            | ✅ (Pydantic) | ✅ (ext)      |
| Segredos como referências              | —         | —         | nível-código  | nível-código  | nível-código  | ✅ (ext)      |
| Memória entre execuções                | —         | —         | nível-código  | ✅            | nível-código  | ✅ (ext)      |
| Hooks de ciclo de vida                 | —         | —         | nível-código  | nível-código  | nível-código  | ✅ (ext)      |
| Guardrails de custo / orçamento        | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| Restrições de ação (permitir/negar)    | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| Agendamento (cron)                     | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| Modos de execução (dry/test/prod)      | —         | —         | ❌            | ❌            | ❌            | ✅ (ext)      |
| Independente de framework              | ✅        | ✅        | ❌ (CrewAI)   | ❌ (LangGraph)| ❌ (ADK)      | ✅            |
| Diff legível por humanos em PR review  | ✅        | ✅        | ✅            | ❌            | ❌            | ✅            |

**Leia como:** AGENTS.md e SKILL.md descrevem *uma* unidade (um agente, uma habilidade). CrewAI, LangGraph e ADK descrevem *pipelines* mas em código ou schema específico de framework. PROJECT.md é o único formato que é tanto **Markdown declarativo** quanto **independente de framework** para a camada de pipeline.

PROJECT.md pode referenciar opcionalmente arquivos AGENTS.md e SKILL.md existentes por meio de extensões, mas continua funcionando perfeitamente sem eles.

> Arquivos específicos de IDE como `CLAUDE.md`, `GEMINI.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.windsurfrules`, `.clinerules` são intencionalmente omitidos — eles compartilham o escopo do AGENTS.md (agente único, um repositório) e diferem apenas em qual ferramenta os lê.

---

## Especificação

- [SPEC.md](SPEC.md) — especificação completa (Core + Extensions)
- [examples/PROJECT-minimal.md](examples/PROJECT-minimal.md) — pipeline apenas com Core
- [examples/PROJECT-news.md](examples/PROJECT-news.md) — exemplo completo do mundo real
- [validator/](validator/) — validador Python de referência

---

## Status

`v0.5` — rascunho. Mudanças incompatíveis são possíveis até `v1.0`. Fixe `spec_version` em seus arquivos.

---

## Contribuindo

Issues e PRs são bem-vindos — especialmente:
- Casos de uso reais que expõem lacunas
- Implementações de orquestradores
- Feedback sobre o que *não* deveria estar na especificação

## Licença

Apache-2.0 — veja [LICENSE](LICENSE).
