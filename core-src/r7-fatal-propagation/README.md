# R7-04 fatal-propagation core-src

Production copies at SHA `fdfb1ce`. Compile the host test **from this directory**:

```bash
cc -O0 -o /tmp/test_gatea_direct_done_class test_gatea_direct_done_class.c
/tmp/test_gatea_direct_done_class
```

`verify_r7_fatal_propagation.py` still needs the full case-loop worktree:

```bash
python3 verify_r7_fatal_propagation.py /root/projects/GPU加速/src/f8-ahb-gatea-case-loop
```

`gateA*.c` files are excerpts from `InitOutput.c`, not a buildable translation unit.
