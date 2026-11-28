# F13 — native `git_ro` over PRoot link2symlink objects: acceptance freeze (2026-11-28)

Frozen before implementation and before any device data for this fix. Context: [pilot deployment record](../evidence/session/proot/STAGE7-5-PILOT-DEPLOY-20261128.md).

## Observed layout (survey of 8 object stores, 4,140 symlinks, before the fix)

Every symlink under `objects/` was one of:

- loose object `objects/XX/<38 hex>`, or pack file `objects/pack/pack-<hex>.{pack,idx,rev}`;
- hop 1: absolute `<rootfs>/.l2s/.l2s.tmp_<kind>_<6 alnum><4 digits>`, kind `obj` for loose objects, `pack`/`idx`/`rev` by pack extension;
- hop 2: absolute `<hop 1>.<4 digits>`, a regular file directly in `<rootfs>/.l2s`.

## Rule

An object entry whose real path leaves the mapped root is accepted only if **all** hold; otherwise the existing `symlink-escape` refusal applies unchanged:

1. The entry name is object-shaped for its directory (as above). Fan-out directory symlinks, `objects/info`, other pack files and any other position get no allowance.
2. Hop 1 is an absolute, normalised path whose parent is exactly the configured l2s directory (`<rootfs>/.l2s`), with the name pattern for the entry's kind.
3. Hop 1 is itself a symlink; hop 2 is absolute, normalised, in the same directory, named `<hop 1 name>.<4 digits>`.
4. Hop 2 is a regular file (not a symlink, not a directory), and the entry's real path equals hop 2.

No other policy check changes: user-supplied `.l2s` paths stay refused (`l2s-path`), alternates, worktrees, config scanning and trust roots are untouched.

Exposure argument: the allowance only reaches files git itself created under a `tmp_<kind>_` name inside PRoot's hard-link store, which the PRoot fallback already reads through the same links. It does not widen what `git_ro` can read compared with the fallback route.

## Gates

| Gate | PASS condition |
|---|---|
| U1 unit, positive | Fixture with the exact two-hop layout for a loose object and for `.pack`/`.idx`: `validate_git_ro` accepts and `git cat-file -t HEAD` returns `commit`. |
| U2 unit, should-be-red | Each refused with `symlink-escape` and Git never launched: non-git name in l2s; kind mismatch (loose → `tmp_pack_`); hop 1 pointing outside l2s; hop 1 in a subdirectory of l2s; relative hop 1; one-hop link to an l2s regular file; three hops; hop 2 a directory; real path ≠ hop 2; non-object-shaped name in a fan-out dir; fan-out directory symlink into l2s; policy with no l2s directory configured. |
| U3 regression | Full suite passes on PRoot and Termux native. |
| U4 negative control | Reverting the rule makes U1 fail. |
| D1 device parity | Isolated native daemon (`--map /fixture=<host path of a PRoot-written fixture repo>`): the fixture contains real PRoot l2s objects (checked before running); native `git_ro` for `log -n 20 --stat`, `show --stat HEAD`, `cat-file -p <l2s-linked oid>`, `rev-list --count HEAD`, `ls-tree -r --name-only HEAD` all return `returncode 0` with byte-identical `stdout`/`stderr`/`returncode` to `F8_NO_HYBRID=1`. Any mismatch is FAIL for that cell; no re-judging. |
| D2 device should-be-red | In the same fixture, a loose object replaced by a link into a PRoot hard link of a non-git file (`.l2s.<name>NNNN`) is refused natively with `symlink-escape`. |
| D3 pilot | After redeploying with `git_ro` routed native: the same 5 commands on every trusted non-worktree repo match `F8_NO_HYBRID=1` byte for byte; no `symlink-escape` in the audit log for those calls; red lines unchanged. |
| CI | Governance CI green on the final head (separate from device gates). |

Latency is recorded for information only and is not a gate.
