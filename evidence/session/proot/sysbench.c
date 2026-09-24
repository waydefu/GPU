// Per-call cost of syscalls inside PRoot: not filtered (getpid, pipe write/read) vs filtered (socket send/recv).
#include <stdio.h>
#include <sys/socket.h>
#include <sys/uio.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec / 1e9; }
int main(void) {
  enum { N = 20000 }; char b = 'x'; int p[2], s[2]; double t;
  pipe(p); socketpair(AF_UNIX, SOCK_STREAM, 0, s);
  t = now(); for (int i = 0; i < N; i++) syscall(SYS_getpid);           printf("getpid          %7.2f us/call\n", (now() - t) / N * 1e6);
  t = now(); for (int i = 0; i < N; i++) { write(p[1], &b, 1); read(p[0], &b, 1); } printf("pipe write+read %7.2f us/pair\n", (now() - t) / N * 1e6);
  t = now(); for (int i = 0; i < N; i++) { send(s[0], &b, 1, 0); recv(s[1], &b, 1, 0); } printf("sock send+recv  %7.2f us/pair\n", (now() - t) / N * 1e6);
  t = now(); for (int i = 0; i < N; i++) { write(s[0], &b, 1); read(s[1], &b, 1); } printf("sock write+read %7.2f us/pair\n", (now() - t) / N * 1e6);
  struct iovec iv = { &b, 1 }; struct msghdr mh = { 0 }; mh.msg_iov = &iv; mh.msg_iovlen = 1;
  t = now(); for (int i = 0; i < N; i++) { sendmsg(s[0], &mh, 0); recvmsg(s[1], &mh, 0); } printf("sock sendmsg+recvmsg %7.2f us/pair\n", (now() - t) / N * 1e6);
  return 0;
}
