// PROOT-FAST v2 micro-benchmark: syscalls that kompat filtered (futex, epoll_pwait, openat exit, fcntl) and
// the vDSO it removed (clock_gettime), next to v1's socket pair and a never-filtered control (getpid).
#define _GNU_SOURCE
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/syscall.h>
#include <sys/socket.h>
#include <sys/epoll.h>
#include <sys/stat.h>
#include <sys/auxv.h>
#include <sys/utsname.h>
#include <linux/futex.h>
static double now(void) { struct timespec t; syscall(SYS_clock_gettime, CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
int main(void) {
  const int N = 20000; double t; int fut = 0, s[2], e; char b = 'x'; struct stat st; struct timespec ts; struct epoll_event ev;
  struct utsname u; uname(&u);
  printf("uname_release   %s\n", u.release);
  printf("vdso            %s\n", getauxval(AT_SYSINFO_EHDR) ? "present" : "absent");
  socketpair(AF_UNIX, SOCK_STREAM, 0, s); e = epoll_create1(0);
  t = now(); for (int i = 0; i < N; i++) syscall(SYS_getpid);                                   printf("getpid          %7.2f us/call\n", (now() - t) / N * 1e6);
  t = now(); for (int i = 0; i < N; i++) syscall(SYS_futex, &fut, FUTEX_WAKE_PRIVATE, 1, 0, 0, 0); printf("futex_wake      %7.2f us/call\n", (now() - t) / N * 1e6);
  t = now(); for (int i = 0; i < N; i++) epoll_pwait(e, &ev, 1, 0, NULL);                        printf("epoll_pwait(0)  %7.2f us/call\n", (now() - t) / N * 1e6);
  t = now(); for (int i = 0; i < N; i++) clock_gettime(CLOCK_MONOTONIC, &ts);                   printf("clock_gettime   %7.2f us/call\n", (now() - t) / N * 1e6);
  t = now(); for (int i = 0; i < N; i++) fcntl(s[0], F_GETFL);                                  printf("fcntl(GETFL)    %7.2f us/call\n", (now() - t) / N * 1e6);
  t = now(); for (int i = 0; i < N; i++) fstat(s[0], &st);                                      printf("fstat           %7.2f us/call\n", (now() - t) / N * 1e6);
  t = now(); for (int i = 0; i < N / 4; i++) close(open("/etc/hostname", O_RDONLY));            printf("open+close      %7.2f us/pair\n", (now() - t) / (N / 4) * 1e6);
  t = now(); for (int i = 0; i < N; i++) { send(s[0], &b, 1, 0); recv(s[1], &b, 1, 0); }       printf("sock send+recv  %7.2f us/pair\n", (now() - t) / N * 1e6);
  return 0;
}
