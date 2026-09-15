# UTF-8 path / Gradle wrapper — 2026-09-14

This is a **host-tool encoding boundary**, not a Gate A source defect.

## Observed

Worktree:

```text
/root/projects/GPU加速/src/f8-ahb-gatea-a1
```

`./gradlew --no-daemon --no-build-cache :lorie:buildCMakeDebug[arm64-v8a]`
exited 1 in ~300 ms. Log:

```text
Error: An unexpected error occurred while trying to open file
/root/projects/GPU??????/src/f8-ahb-gatea-a1/gradle/wrapper/gradle-wrapper.jar
```

`gradle-wrapper.jar` exists and is readable. The path is rewritten from
UTF-8 `加速` to `??????`. An ASCII symlink `/tmp/f8-ahb-gatea-a1` → the
same worktree still failed: `gradlew` resolves `APP_HOME` to the real
Unicode path, then the JVM/wrapper opens the jar with a non-UTF-8
decoded name.

## Rule

Any Gradle / Java invocation on this workstation **must** run with a
UTF-8 locale, for example:

```text
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export LANGUAGE=C.UTF-8
```

Do not treat `GPU??????` as a missing file, a dirty tree, or a reason to
`reset --hard`. Do not rename the project folder in this round.

Previous successful ARM64 compiles on this tree used a UTF-8 locale.
This round’s first Gradle attempt did not.

## Not this

- D0a / source / ABI / timeout / Production Gate A
- ADB / install / runtime
