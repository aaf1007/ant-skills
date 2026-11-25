---
name: component-scout
description: Scout the user's bookmarked UI component libraries (Aceternity, shadcnblocks, 21st.dev, Space UI, Planes, Skecher, Componentry, BoardUI, Neobrutalism, prompt-kit, HeroUI, Mantine UI, Lucide) for ready-made components before hand-building UI. Use when designing or building front-end UI: a page, section, layout, dashboard, form, chat interface, animation, or icon.
---

# Component scout

Before writing a UI piece by hand, check whether one of the user's bookmarked libraries already has it. `scout.py` (next to this file) searches all of them at once and prints a preview link and install command per hit.

## 1. List the needs

Break the design into the pieces a library could supply: sections (hero, pricing, FAQ, footer), controls (date picker, combobox, file dropzone), patterns (chat input, data table, stat cards), effects (animated background, text reveal), and icons. Each piece becomes one short query: `"pricing"`, `"date picker"`, `"chat input"`. Skip pieces the project already has in `components/ui`.

## 2. Check the stack

Read `package.json` and `components.json`. Most sources ship shadcn registries (React + Tailwind, installed with `npx shadcn add`), so they fit any shadcn project. HeroUI and Mantine UI only fit projects that already use those frameworks: pass `--only` to leave them out otherwise. Lucide fits any React project.

## 3. Search

```bash
python3 -I ~/.claude/skills/component-scout/scout.py "pricing" "date picker" "chat input"
```

Flags: `--per-source N` (default 4), `--only aceternity,planes,...`, `--refresh` (ignore the 7-day cache), `--list` (show sources and index sizes). Try a synonym when a query comes back thin (`"plans"` for pricing, `"modal"` for dialog).

Done when every need from step 1 has at least one candidate or an explicit "nothing suitable".

## 4. Vet the candidates

For the best one to three per need, read the actual component before choosing: fetch the registry JSON in the install URL (it holds the source and `dependencies`), or append `.md` to a 21st.dev link. Weigh:

- **Tier.** `(pro)` means it needs a paid license. A shadcnblocks install that returns 401 is Pro too. Prefer free; propose Pro only when nothing free comes close.
- **Dependencies.** Note heavy additions (three.js, a second animation library, a different UI framework).
- **Fit.** Matches the design's style, and can be restyled with the project's tokens.

## 5. Report and install

Give the user one line per need: the pick, its preview link, why it fits, and any tier or dependency cost. Then install free picks with their `install:` command and restyle them to the project's design tokens. Ask first before installing anything Pro or anything that adds a heavy dependency. When no source fits a need, build it by hand and say so.

## Sources

| source | best for |
|---|---|
| aceternity | eye-catching animated effects and hero/landing sections; blocks under `/blocks/` are Pro |
| shadcnblocks | 5,000+ marketing and app blocks (hero, pricing, features, app shells); many are Pro |
| 21st | huge community catalog, searched live by tag |
| spaceui | primitives with many variants, plus interactions and hooks |
| planes | polished WebGL and motion sections; only ~12 free |
| skecher, componentry | small sets of distinctive motion components |
| boardui | dashboards, charts, and AI-agent UI |
| prompt-kit | AI chat UI: prompt input, messages, markdown, code blocks |
| neobrutalism | the neobrutalist look specifically |
| heroui, mantine-ui | only in projects already on HeroUI or Mantine |
| lucide | icons |

For light/dark palette ideas, the user also bookmarked a color generator: https://codepen.io/luispadarotto/full/qBQjoOK (a manual tool; point the user to it rather than scraping it).

To add a source, add an entry to `SOURCES` in `scout.py`. Most component sites expose `/r/registry.json` or `/llms.txt`; check those first.
