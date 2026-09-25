// Decompose the per-stop cost: N fstat() calls; prints wall time and this process's own user/sys CPU.
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sys/stat.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <fcntl.h>
static double now(void) { struct timespec t; syscall(SYS_clock_gettime, CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
int main(int argc, char **argv) {
  int n = argc > 1 ? atoi(argv[1]) : 20000, fd = open("/etc/hostname", O_RDONLY); struct stat st; struct rusage a, b;
  getrusage(RUSAGE_SELF, &a); double t0 = now();
  for (int i = 0; i < n; i++) fstat(fd, &st);
  double t1 = now(); getrusage(RUSAGE_SELF, &b);
  double u = (b.ru_utime.tv_sec - a.ru_utime.tv_sec) + (b.ru_utime.tv_usec - a.ru_utime.tv_usec) * 1e-6;
  double s = (b.ru_stime.tv_sec - a.ru_stime.tv_sec) + (b.ru_stime.tv_usec - a.ru_stime.tv_usec) * 1e-6;
  printf("FSTATLOOP n=%d wall_us_per=%.2f tracee_user_us_per=%.2f tracee_sys_us_per=%.2f nvcsw=%ld nivcsw=%ld\n",
         n, (t1 - t0) / n * 1e6, u / n * 1e6, s / n * 1e6, b.ru_nvcsw - a.ru_nvcsw, b.ru_nivcsw - a.ru_nivcsw);
  return 0;
}
