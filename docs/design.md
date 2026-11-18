# Design

This page describes what the `spillway/` core implements (v0.4.0) and the invariants its tests enforce. A separate private native Hermes patch aims at the same contract, but that patch is **not** part of this repository and is not proven by these tests; see [project status](project-status.md).

## Goals and non-goals

Keep the information the agent needs for its next decision and keep the rest recoverable. Fidelity comes first and size second. A preview that hides why a command failed counts as a failure, however small it is.

Spillway is not conversation-summary compaction, a cap on total tokens or money, or a security boundary against same-UID processes. Lines, UTF-8 bytes and provider tokens are different units, and Spillway caps only bytes and lines.

## Output policy (`spillway.Policy`)

| Surface | Default | Notes |
| --- | --- | --- |
| Ordinary tool result | 16,384 UTF-8 bytes (`result_cap`) | Measured on the final rendered form; floor `MIN_RESULT_CAP = 256` |
| Complete file read (`read_kind="full"`) | 350 effective LF lines **and** the byte cap | A head-only preview gets the whole byte budget |
| Partial file read (`read_kind="partial"`) | 150 effective LF lines **and** the byte cap | Same |
| Note bundle | 4,096 bytes per note (`note_cap`), 8,192 per row (`note_batch_cap`) | Notes over the budget become a bounded marker listing their IDs |
| Batch row floor | 1,024 bytes (`min_row_cap`) | Lower bound used during aggregate water-filling |

Effective LF lines: `""` is 0 lines, `"a"` is 1, `"a\n"` is 1, `"a\nb"` is 2 and `"\n"` is 1. Only LF separates lines. Byte cuts never split a UTF-8 code point. Head and tail cuts also snap to line boundaries when that keeps at least half of the segment.

Mandatory control rows (`control=True`) are never capped. A valid one-use approved-read `Receipt` that matches the exact call ID and session raises the cap to `max_bytes` and replaces the line limit. Settling the same call again does not revoke it, and another call cannot replay it.

## Rendering and measurement

[`render.py`](../spillway/render.py) produces the delivered output and the measured output from one function.

- **Text:** `<untrusted_tool_result>\n{body}\n</untrusted_tool_result>`, followed by an optional `\n[spillway notes]\n[note:ID] …` suffix outside the wrapper.
- **Multimodal:** a JSON list of parts. The wrapped body goes in the first text part, media parts keep their original order, and notes go in a final text part. Size is measured on the compact JSON with media replaced by a fixed placeholder, so JSON escaping of control characters is counted.

Adapters whose host adds its own framing (Hermes, and MCP by default) deliver `Rendered.unwrapped_payload()`. That form is never larger than what was measured.

## Facts that survive any cut

[`facts.py`](../spillway/facts.py) extracts facts from the **full** output before anything is cut:

- `exit_code`: an explicit argument, or `exit_code`/`returncode`/`exitCode` in a dict result.
- Up to 5 `file:line` locations, keeping the last frames: Python tracebacks (raw or JSON-escaped), TypeScript/MSBuild `file(l,c)`, and GCC/Rust/ESLint/SQL/Make `file:l[:c]`. Many source extensions are recognized, as are well-known extensionless files. JSON results are also unwrapped and scanned.
- When no location is found, up to 2 short `FATAL`/`PANIC`/`ERROR`/`FAILED`/`*Error`/`*Exception` lines are kept as `clues`.

These facts go into the preview header. The verifier then checks that the exit code and every location appear in the final output.

## Per-result algorithm (`apply_budget`)

1. Split the result into body and media, extract facts, hash the full original (`artifact_sha256`), and neutralize the body (see [Trust boundary](#trust-boundary)).
2. If the result is within its line limit and the full render fits the cap, the mode is **`full`**, or **`control`** for control rows.
3. Otherwise build `[spillway preview] original N bytes, M lines; exit_code=…; errors|clues: …; <artifact hint>` plus a head and a tail. Line-limited reads get a head only. Re-measure the complete render and shrink by the exact excess until it fits, giving the mode **`preview`**.
4. If no preview fits, emit the header alone (**`marker`**). If even that does not fit with the notes, replace the notes with one marker that lists their IDs.
5. Run the independent verifier. If it finds any violation, the result becomes a bounded **`failclosed`** marker.

`force="withheld"` (from a batch policy failure) skips steps 2–3 and keeps the notes the call owns.

## Batch settlement (`finalize_batch`)

1. Budget every row on its own.
2. If `turn_budget` is exceeded, treat control rows and rows that used a receipt as **fixed**. For the remaining rows, compute water-filling caps: sort by size, let rows smaller than the fair share keep their full size, and give the rest an equal share of what remains, never below `min_row_cap`. Re-settle the largest rows first, and pass any bytes a row did not use on to the rows after it.
3. If the budget still cannot be met (fixed rows plus floors are too large), set `aggregate_unsatisfiable=true` on every receipt. Rows are never truncated below their floors to hide this.
4. If a policy or aggregate callback raises, every row becomes `withheld` and keeps the notes it owns. Tools are never re-run.
5. `NoteLedger.complete_batch` runs only after the last settlement.

## Trust boundary

- There is exactly one genuine wrapper. Any case or whitespace variant of `<untrusted_tool_result` or `</untrusted_tool_result` inside the body **or a note** has its `<` rewritten to `&lt;`. This is deterministic and idempotent.
- Reserved tags in untrusted bodies (`[note:`, `[spillway`, and the legacy `[cbg`) become `[untrusted-…`, so tool output cannot forge a header or a note.
- Notes are owned by call IDs and are placed outside the wrapper exactly once. The verifier checks that placement.
- MCP recovery slices are neutralized in the same way before they are returned.

## Note ownership

Notes move through `PENDING → DELIVERED → RETIRED`. Each note is bound to the SHA-256 of the render that was actually delivered, keeps its eligibility across re-settlement, and survives session rotation while PENDING. State is bounded (`retired_cap`, `pending_cap`). The full model is in [model/notes.md](model/notes.md).

## Artifacts and adapters

The budgeting core does no I/O. [`artifacts.py`](../spillway/artifacts.py) is the only layer that touches the filesystem:

- Content-addressed `artifacts/<sha256>.txt`, written idempotently, files 0600, directories 0700, using `O_NOFOLLOW`. Names must be valid SHA-256 hex, and symlinks and non-regular files are refused.
- Retention by count and total bytes (default 200 files / 100 MiB). The oldest files go first, and the file just written is never evicted.
- `read_slice(sha256, offset, limit)` seeks and reads only the requested window. It returns UTF-8-safe text with `next_offset` and `eof`, and every call makes progress even when `limit` is smaller than one code point.

Both adapters default to `shadow` and **fail open**: on any internal error the original result passes through. See [adapters/hermes](../adapters/hermes/README.md) and [adapters/mcp_proxy](../adapters/mcp_proxy/README.md).

## Receipt fields

The core (`apply_budget`) writes these fields. Adapters write them to `receipts.jsonl`, and no field contains output content.

| Field | Meaning |
| --- | --- |
| `call_id` | Tool call ID (`mcp-<JSON-RPC id>` in the proxy) |
| `mode` | `full`, `preview`, `marker`, `withheld`, `failclosed` or `control` |
| `kind` | `text` or `multimodal` |
| `cap` | Cap applied in bytes (`null` for control rows) |
| `rendered_bytes`, `rendered_sha256` | Size and hash of the measured final render |
| `original_bytes`, `original_lines` | UTF-8 bytes and effective LF lines of the original body |
| `exit_code` | Detected exit code, or `null` |
| `error_locations`, `diagnostic_clues` | Extracted `file:line` locations; fallback clue lines |
| `notes_shown`, `notes_marked` | Note IDs shown in full, or represented only by a marker |
| `media_parts` | Number of preserved media parts |
| `artifact_sha256`, `artifact_bytes` | Hash and size of the full original |
| `receipt_used` | Whether an approved-read receipt was applied |
| `verified` | Whether the verifier accepted the final render |
| `violations_before_failclose` | Violations found before failing closed (normally `[]`) |
| `policy_error`, `aggregate_bytes`, `aggregate_unsatisfiable` | Batch settlement only |

Adapter fields: `ts`, `tool`, `adapter`, `adapter_mode`, `elapsed_us`, `would_change` (the mode is neither `full` nor `control`), and also `session_id` (Hermes) or `is_error` (MCP). When the MCP proxy drops `structuredContent` it writes an extra `{"call_id", "structured_content_dropped": true}` line.

## Review evidence

Cover exact limits and the values next to them, complete versus partial reads, multibyte text, mandatory exceptions, media, artifact recovery and privacy, exit codes, and aggregate spill with notes. Inspect the model-visible result, not only stored output. See [benchmarking](benchmarking.md), [rollout](rollout.md) and the [historical reviews](reviews/2026-11-04-combined-assessment.md) that motivated these invariants.
