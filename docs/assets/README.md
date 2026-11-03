# README artwork

Original project illustrations, distributed under the repository's existing MIT license. These are editable SVG graphics—not generated performance charts, screenshots of a shipped product, or evidence of runtime approval.

| Source | PNG export | Purpose |
| --- | --- | --- |
| [hero.svg](hero.svg) | [hero.png](hero.png) | The concept: less noise, preserve the clue, recover detail |
| [output-flow.svg](output-flow.svg) | [output-flow.png](output-flow.png) | Intended output, metadata, trust boundary and artifact flow |
| [roadmap.svg](roadmap.svg) | [roadmap.png](roadmap.png) | Current rejected review and the remaining promotion gates |
| [evaluation.svg](evaluation.svg) | [evaluation.png](evaluation.png) | Proposed comparison arms, semantic oracles and later efficiency metrics |

The README embeds SVG so graphics remain crisp when zoomed. PNG exports are provided for viewers that do not display SVG. Each SVG contains an accessible title and description, local/system font fallbacks, and no JavaScript, remote assets or external font downloads. README alt text and nearby prose provide a text alternative; status is communicated in words, not color alone.

The [visual guide](../visual-guide.html) embeds all four illustrations and its CSS in one offline HTML file. **Download and open it locally:** GitHub displays HTML source rather than executing this page.

## Editing and exports

Edit the SVG source, then regenerate its PNG with librsvg's `rsvg-convert`:

```sh
for source in docs/assets/*.svg; do
  rsvg-convert "$source" --output "${source%.svg}.png"
done
```

Also refresh the matching inline SVG in `docs/visual-guide.html`. This export tool is optional artwork-maintenance tooling; it is not a dependency of the public Python checks or an installer for the absent runtime.

Keep the design language consistent: dark navy canvas, cyan data flow, emerald retained metadata, violet recovery detail, amber planned gates and rose rejection/blockers. Preserve the explicit experimental/not-shipped/blocked labels. If the actual state changes, update status text, image descriptions, README prose and the gallery together.

Before publishing: parse SVG XML, inspect rendered images for clipped/overlapping labels and incorrect arrows, verify SVG/PNG dimensions, inspect small-width presentation, run repository checks, and verify exact-head GitHub CI. Do not invent a compression ratio, savings number or completion percentage to fill an empty chart.
