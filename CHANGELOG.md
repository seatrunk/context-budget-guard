# Changelog

All notable changes to this project. Versions follow [Semantic Versioning](https://semver.org/); while the major version is 0, minor versions may change the model-visible contract.

## [0.4.0] — 2026-11-18

The project is renamed from **Context Budget Guard** (`cbg`) to **Spillway** (`spillway`). The core rules have not changed: it measures the final rendered bytes, keeps the diagnostic facts, checks the result with an independent verifier and fails closed. This release fixes the budgeting bugs found in the 0.3.0 review and makes spilled output recoverable.

### Breaking changes

- **Package and import name:** `cbg` → `spillway` (`import spillway`). The `cbg/` directory is gone.
- **Model-visible contract is now English:** headers read `[spillway preview] original N bytes, M lines; exit_code=…; errors: …; artifact …`. Before, they were Portuguese `[cbg …]` strings. Notes use `[spillway notes]`, and budget markers use `[spillway: …]`. Anything that parses the old headers must be updated.
- **Hermes plugin:** the plugin directory and manifest name are now `spillway` (`~/.hermes/plugins/spillway`, `hermes plugins enable spillway`). The default log directory is now `$HERMES_HOME/spillway`.
- **MCP proxy:** the default log directory is now `~/.cache/spillway`. Enforced MCP text no longer contains the `<untrusted_tool_result>` wrapper unless you pass `--wrap-untrusted`, because MCP clients apply their own framing.
- **Replay report schema:** `cbg-offline-replay/1` → `spillway-offline-replay/2`. It adds a `min_bytes` oracle and two new fixtures.

### Migration

- Environment variables are now `SPILLWAY_*`. The old `CBG_MODE`, `CBG_LOG_DIR`, `CBG_RESULT_CAP`, `CBG_FRAMING_RESERVE` still work as fallbacks when the `SPILLWAY_*` variable is unset or empty. (`install.sh` still reads `CBG_INSTALL_DEST`, but the destination must now end in `/plugins/spillway`.)
- Re-run `sh adapters/hermes/install.sh`, then `hermes plugins disable context-budget-guard`, `hermes plugins enable spillway`, and restart Hermes. Delete `~/.hermes/plugins/context-budget-guard` and the old log directory when you no longer need them.
- `python3 adapters/mcp_proxy/proxy.py …` still works from a source checkout. The installed equivalent is `spillway mcp …`.
- Untrusted tool text that contains `[cbg` or `[spillway` is neutralized to `[untrusted-…`, so old and new headers cannot be forged.

### Fixed

- **Batch water-filling:** `finalize_batch` used to give every flexible row an equal share. That crushed one large row next to many small ones: 9 × 100 B + 1 × 15,500 B under a 16,000 B budget came out at about 2.9 KB in total. It now water-fills, so small rows keep their size and unused slack rolls forward (same batch: 16,000 B).
- **Approved-read receipts in batches:** rows holding an active receipt ignored `cap_override` but were still counted as flexible, which could mark a feasible batch `aggregate_unsatisfiable`. They are now fixed rows, and the other rows absorb the reduction.
- **Line-limited reads:** `full`/`partial` previews got only 2/3 of the byte budget and an empty tail. They now get the whole budget.
- **Unrecoverable artifact pointer:** the header gave a 16-character hash prefix and no location. It now gives the full SHA-256. The Hermes adapter prints the absolute artifact path, and the MCP proxy prints the recovery tool name.
- **JSON-wrapped tool output:** Python tracebacks inside JSON strings (`File \"x.py\", line N`) are now found. JSON values are unwrapped for fact extraction.
- **Tiny caps:** the MCP proxy cap now has the core's 256-byte floor (`MIN_RESULT_CAP`). At that floor, text results still get a header-only marker. Multimodal results or results with large notes need a larger cap; below what they need they fail closed, with a neutral `could not be bounded and verified within cap` message.
- **Pagination stall:** `utf8_slice` returned empty text with `next_offset == offset` when `limit` was smaller than the code point at the offset, so pagination never advanced. It now always moves forward.
- **Recovery output forgery:** `spillway_read_artifact` returned raw artifact text. A stored payload could therefore show a fake `[spillway preview] exit_code=0` header or a closing wrapper tag. Slices are now neutralized like any other tool body, and they are shrunk until the neutralized response fits within the cap.
- **Hermes log directories containing `{` or `}`** broke the artifact hint's `str.format` and silently failed open. Fixed.
- **`spillway stats`** aborted on a truncated `receipts.jsonl` line. It now skips the line and reports `skipped_lines`.
- **Small Python tracebacks and TypeScript errors withheld (present since 0.3.0):** when such a result fit within the cap, it was delivered in full, but the verifier looked for the normalized `file:line` string. The text contains `File "x.py", line N` or `x.ts(l,c)` instead, so the verifier never found it and in `enforce` the result became a `failclosed` stub. The verifier now accepts every form the extractor recognizes.
- **Paths that look like tags:** a location such as `/p/[cbg]/a.py` used to make verification fail. Locations and clues are now neutralized the same way as the body.
- **Lone surrogates** (for example a JSON string cut in the middle of an emoji) raised `UnicodeEncodeError`, so both adapters failed open and returned the **uncapped** output. They are now replaced before measurement and storage.
- **Multimodal previews collapsing to a marker:** text that JSON-escaping makes much larger (`"`, control characters, ANSI codes) made the excess-subtraction loop overshoot. Multimodal previews now binary-search the largest fitting body.
- **Quadratic clue regex:** 40 KB of blank lines took more than 10 s in the clue extractor. It is now linear (about 15 ms for 100 KB).
- **MCP shadow mode was not byte-for-byte:** invalid UTF-8 was replaced and a missing final newline was added. Unchanged messages are now forwarded as the original bytes.
- **Hermes fail-open:** an invalid retention variable could raise from the error-logging path into the host. Empty `SPILLWAY_*` variables now fall back to `CBG_*` and then to the defaults.
- **Artifact store:** `read_slice` could return `U+FFFD` for tiny limits at offsets inside a character. A FIFO at an artifact path blocked `open()`. A symlinked `artifacts/` directory was followed. All three are fixed: a larger read window, `O_NONBLOCK`, and refusing a symlinked directory.

### Added

- **`pyproject.toml`**, with zero runtime dependencies and the `spillway` console script. Only the `spillway` package is installed. The MCP proxy moved into `spillway.mcp_proxy`, so installing no longer adds a generic top-level `adapters` package.
- **CLI:** `spillway mcp`, `spillway stats`, `spillway prune`, `spillway replay` (source checkout only) and `spillway --version`.
- **MCP recovery tool `spillway_read_artifact`**, added to `tools/list` in `enforce` mode. It reads UTF-8-safe paginated slices by SHA-256, and each neutralized response fits within the cap. MCP clients without filesystem access can use it.
- **`ArtifactStore`:** a single hardened I/O layer for adapters. It uses `O_NOFOLLOW`, gives files 0600 and directories 0700, refuses symlinks and non-regular files, and validates SHA-256 names. Retention defaults to at most 200 files and 100 MiB (`SPILLWAY_MAX_ARTIFACTS`, `SPILLWAY_MAX_ARTIFACT_BYTES`, `--max-artifacts`, `--max-artifact-bytes`). Reads use `seek` and load only the requested window, not the whole artifact.
- **Diagnostic clues:** when no `file:line` is found, up to two short `FATAL`/`ERROR`/`panic`/`*Error` lines go into the header as `clues: …`.
- **Wider location coverage:** more source extensions (Vue, Svelte, Swift, C#, Zig, Proto, Terraform, Nix and others) and well-known extensionless files (`Makefile`, `Dockerfile`, `CMakeLists.txt`, `BUILD.bazel` and others).
- **Line-aligned previews:** head and tail cuts snap to line boundaries when that keeps at least half of the segment, so the model sees whole lines.
- **Bounded orphaned notes:** `NoteLedger(pending_cap=256)` evicts the oldest PENDING notes whose call never settled, and counts them in `evicted_pending`.
- **Repository checks:** `CHANGELOG.md` and `pyproject.toml` are required. The versions in `pyproject.toml`, `spillway/__init__.py`, the Hermes manifest and this file must match, and package modules must not import `cbg` or the top-level `adapters` package.
- **Replay fixtures** `json_escaped_traceback` and `waterfill_mixed_batch`. Offline replay now has 12 cases and 62 oracle checks: candidate 62/62, unbudgeted 46/62, emulated historical spill 43/62.

## [0.3.0] — 2026-11-04

Stage 1 (PR #14): a pure, dependency-free `cbg/` core (limits, render, notes, sanitize, facts, budget, verify), a Hermes `transform_tool_result` plugin and an MCP stdio proxy, both in `shadow` by default, plus a deterministic offline replay (10 cases, candidate 39/39). Later commits made all public documentation and code comments English and added `install.sh` guards, gitleaks and zizmor to CI.

[0.4.0]: https://github.com/seatrunk/context-budget-guard/compare/dd8bc4b...HEAD
[0.3.0]: https://github.com/seatrunk/context-budget-guard/commit/de61160
