// newfstatat by path (what git / find / Python os.stat use): N calls, absolute and relative path, follow and nofollow.
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/syscall.h>
static double now(void) { struct timespec t; syscall(SYS_clock_gettime, CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
static void run(const char *label, const char *p, int flags, int n) { struct stat st; double t = now();
  for (int i = 0; i < n; i++) fstatat(AT_FDCWD, p, &st, flags);
  printf("%-22s %7.2f us/call uid=%u nlink=%lu\n", label, (now() - t) / n * 1e6, st.st_uid, (unsigned long) st.st_nlink); }
int main(int argc, char **argv) { int n = argc > 1 ? atoi(argv[1]) : 20000; chdir("/etc");
  run("stat abs", "/etc/hostname", 0, n); run("lstat abs", "/etc/hostname", AT_SYMLINK_NOFOLLOW, n);
  run("stat rel", "hostname", 0, n); run("stat missing", "/etc/no-such-file", 0, n); return 0; }
