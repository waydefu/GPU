// statx by path (what coreutils ls/stat and Node's fs.stat use) and by fd (AT_EMPTY_PATH): N calls each.
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/syscall.h>
static double now(void) { struct timespec t; syscall(SYS_clock_gettime, CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
static void run(const char *label, int dirfd, const char *p, int flags, int n) { struct statx sx = {0}; int rc = 0; double t = now();
  for (int i = 0; i < n; i++) rc = statx(dirfd, p, flags, STATX_BASIC_STATS, &sx);
  printf("%-20s %7.2f us/call rc=%d uid=%u nlink=%u mask=0x%x\n", label, (now() - t) / n * 1e6, rc, sx.stx_uid, sx.stx_nlink, sx.stx_mask); }
int main(int argc, char **argv) { int n = argc > 1 ? atoi(argv[1]) : 20000, fd = open("/etc/hostname", O_RDONLY);
  run("statx abs", AT_FDCWD, "/etc/hostname", 0, n); run("statx nofollow", AT_FDCWD, "/etc/hostname", AT_SYMLINK_NOFOLLOW, n);
  run("statx fd", fd, "", AT_EMPTY_PATH, n); run("statx missing", AT_FDCWD, "/etc/no-such", 0, n); return 0; }
