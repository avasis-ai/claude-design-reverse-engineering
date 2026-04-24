# Claude-style output design — community framework

This document is a **practical distillation** of patterns commonly seen in high-quality long-form assistant answers. Use it to design docs, marketing pages, in-app help, and prompt templates. It is **descriptive**, not normative for any vendor product.

## 1. Answer first (progressive disclosure)

1. **Hook:** 2–3 sentences that answer the core question.
2. **Breakdown:** Sections or numbered steps, one main idea each.
3. **Recap:** Short summary, risks, or next actions.

Readers should be able to stop after the hook without losing the main point.

## 2. Chunking and scanning

- Prefer **one idea per chunk** (paragraph, card, or list block).
- Keep paragraphs short (roughly 3–4 sentences) when writing for screens.
- When a paragraph grows a list, **promote** bullets instead of embedding many clauses.
- Avoid more than **~7** parallel bullets without subgrouping.

## 3. Hierarchy

- Long-form: use clear `H2` pillars; use `H3` for subtopics.
- Conversational UI: prefer **minimal headers**; use bold labels only when they improve scan paths.

## 4. Lists and tables

- **Bullets** for unordered sets of actions, features, or constraints.
- **Numbers** only when order matters.
- **Tables** for side-by-side comparison; cells should stay short (keywords, numbers, fragments).

## 5. Tone

- Professional, direct, second person where appropriate.
- Prefer **active voice** and concrete verbs in procedures.
- Avoid filler stacks (“honestly”, “obviously”) unless tone research for your brand says otherwise.

## 6. Signposting

Use transitions and section titles as **handles**: “First”, “Next”, “Tradeoffs”, “Security”, “What to do now”.

## 7. Checklist (self-edit or prompt)

| Aspect | Ask |
| --- | --- |
| Structure | Does the first screen answer the question? |
| Chunks | Can each paragraph title be stated as one noun phrase? |
| Lists | Are bullets parallel in grammar and length? |
| Tables | Would a table reduce repeated sentence patterns? |
| Depth | Is optional detail behind toggles, links, or appendices? |
| Close | Is there an explicit recap or next step? |

## 8. Mapping to UI tokens

When your team adopts this framework for web properties, align spacing and type ramps to shared tokens in `packages/tokens/tokens.css`. Tokens are **brand-level** choices; this framework addresses **information architecture** first.
