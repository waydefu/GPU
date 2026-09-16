---
name: no-guess-search
description: >-
  After getting stuck once, search current official or authoritative docs
  instead of guessing. Use when stuck, unknown, unsure about an API, compile
  flags, headers, ABI, SCM_RIGHTS, host tests, missing includes, or any next
  step that would be invented rather than read. Trigger on 卡住, 不要瞎猜,
  官方, 權威, 過時, look up, search the web.
---

# No Guess Search

只要一卡住就上網查不要瞎猜
The moment you get stuck, look it up. Do not guess.

卡住一次才查，一定要官方或權威文件，不可過時
Search only after getting stuck once. Use current official or authoritative
documents only. Do not use outdated sources.

## When

Search only after the first real stuck: local source/authority was read, and
the next step would still be inferred. Examples: unknown API, header isolation,
host vs Android compile, ABI/`sizeof`, `recvmsg`/`SCM_RIGHTS`, tool flags,
missing include, or a look-alike parser when production code exists.

Do not search preemptively. Do not guess through a second attempt first.

## Sources

Use only current official or authoritative documents:

- Vendor/project docs for the installed version (Android/NDK, POSIX/Linux man,
  LLVM/Clang, X.org, kernel, GitHub Actions).
- Bind URL, version, and date. Prefer the live canonical page over mirrors.
- Reject blogs, forums, Stack Overflow, and superseded/archived pages as
  authority. An old official page that the vendor replaced is 過時 / outdated —
  do not use it.

## Do

1. WebSearch/WebFetch the current official page.
2. Bind URL + version/date + the exact claim.
3. If that page and local source still disagree, stop and report UNKNOWN.

## Do not

Guess include paths, compiler flags, wire sizes, or a disconnected
implementation. Blind retries of the same unproven idea are forbidden.

Related: `evidence-first-debugging`, Serena `mem:global/no-guess-search`.
