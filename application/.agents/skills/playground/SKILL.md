---
name: playground
description: Creates interactive HTML playgrounds — self-contained single-file explorers that let users configure something visually through controls, see a live preview, and copy out a prompt. Use when the user asks to make a playground, explorer, or interactive tool for a topic.
---

# Playground Builder

A new general-purpose playground is a self-contained HTML file with interactive controls, a live preview, and a copyable prompt. When the user provides or the project already has a concrete template, preserve that template and add only the interactions the current request needs.

## When to use this skill

When the user asks for an interactive playground, explorer, or visual tool for a topic — especially when the input space is large, visual, or structural and hard to express as plain text.

## Reuse a concrete template first

- Inspect the supplied template or existing approved page before selecting a generic template below. Keep its layout, content hierarchy, visual style, and existing entry point. Adapt the content and requested controls; do not treat the template as visual inspiration for a redesign.
- For a requirements board showing customer pain points, planned functions, and expected effects, use the sibling [review-project-requirements](../review-project-requirements/SKILL.md) workflow when available. Fill its approved light three-column template in `assets/board.html` with `scripts/build_board.py`. Preserve its colors, cards, decorative artwork, and default reading controls; adapt the content, row count, and height to the actual requirements. Do not duplicate that HTML into this skill or apply the generic dark theme below.
- In that requirements-board workflow, “review each item” means the rows must be easy to compare. It does not by itself request approval states, comments, progress tracking, source viewers, downloads, or persistence. Typography, spacing, and reset controls are already part of the default template; keep them unless the user requests a static version.
- A concrete-template adaptation follows that workflow's contract. The generic prompt output and 3–5 presets below are not mandatory additions to an existing requirements board.
- Before implementation, state which template is being reused and the small changes needed. Before delivery, compare the actual page with that template as well as checking the requested interactions, using only the verification methods allowed in the current session. If the user will review the appearance themselves, provide the preview and state that visual verification remains with them. Functional tests alone do not establish template fidelity.

## Build a new generic playground

1. **Identify the playground type** from the user's request
2. **Load the matching template** from `templates/`:
   - `templates/design-playground.md` — Visual design decisions (components, layouts, spacing, color, typography)
   - `templates/data-explorer.md` — Data and query building (SQL, APIs, pipelines, regex)
   - `templates/concept-map.md` — Learning and exploration (concept maps, knowledge gaps, scope mapping)
   - `templates/document-critique.md` — Document review (suggestions with approve/reject/comment workflow)
   - `templates/diff-review.md` — Code review (git diffs, commits, PRs with line-by-line commenting)
   - `templates/code-map.md` — Codebase architecture (component relationships, data flow, layer diagrams)
3. **Follow the selected template's structure.** If no template fits cleanly, adapt the closest one only where the user's task requires it. Do not combine unrelated workflows or introduce extra panels and features merely because another template contains them.
4. **Open and compare in an allowed browser.** Follow the workspace's browser rules, check the selected template's structure, and verify the requested controls on desktop and narrow screens.

## Core requirements for a new generic playground

- **Single HTML file.** Inline all CSS and JS. No external dependencies.
- **Live preview.** Updates instantly on every control change. No "Apply" button.
- **Prompt output.** Natural language, not a value dump. Only mentions non-default choices. Includes enough context to act on without seeing the playground. Updates live.
- **Copy button.** Clipboard copy with brief "Copied!" feedback.
- **Sensible defaults + presets.** Looks good on first load. Include 3-5 named presets that snap all controls to a cohesive combination.
- **Dark theme.** System font for UI, monospace for code/values. Minimal chrome.

## State management pattern

Keep a single state object. Every control writes to it, every render reads from it.

```javascript
const state = { /* all configurable values */ };

function updateAll() {
  renderPreview(); // update the visual
  updatePrompt();  // rebuild the prompt text
}
// Every control calls updateAll() on change
```

## Prompt output pattern

```javascript
function updatePrompt() {
  const parts = [];

  // Only mention non-default values
  if (state.borderRadius !== DEFAULTS.borderRadius) {
    parts.push(`border-radius of ${state.borderRadius}px`);
  }

  // Use qualitative language alongside numbers
  if (state.shadowBlur > 16) parts.push('a pronounced shadow');
  else if (state.shadowBlur > 0) parts.push('a subtle shadow');

  prompt.textContent = `Update the card to use ${parts.join(', ')}.`;
}
```

## Common mistakes to avoid

- Prompt output is just a value dump → write it as a natural instruction
- Too many controls at once → group by concern, hide advanced in a collapsible section
- Preview doesn't update instantly → every control change must trigger immediate re-render
- No defaults or presets → starts empty or broken on load
- External dependencies → if CDN is down, playground is dead
- Prompt lacks context → include enough that it's actionable without the playground
