#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#if defined(__has_include)
#if __has_include(<linux/memfd.h>)
#include <linux/memfd.h>
#endif
#endif
#include <linux/netlink.h>
#include <linux/stat.h>
#include <pty.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

#ifndef MFD_CLOEXEC
#define MFD_CLOEXEC 0x0001U
#endif
#ifndef MFD_ALLOW_SEALING
#define MFD_ALLOW_SEALING 0x0002U
#endif
#ifndef SYS_memfd_create
#ifdef __NR_memfd_create
#define SYS_memfd_create __NR_memfd_create
#endif
#endif

static int test_auxv_close_reuse(void) {
    int afd = open("/proc/self/auxv", O_RDONLY);
    if (afd < 0) { perror("open auxv"); return 1; }
    unsigned long pair[2] = {0, 0};
    if (read(afd, pair, sizeof(pair)) != sizeof(pair)) { perror("read auxv"); close(afd); return 2; }
    int target_fd = afd;
    close(afd);

    /* Create a pipe and dup2 write/read onto target_fd to reuse auxv_fd number */
    int pfd[2];
    if (pipe(pfd) != 0) { perror("pipe"); return 3; }
    if (pfd[1] == target_fd) {
        int nw = dup(pfd[1]);
        if (nw < 0) { perror("dup pfd1"); return 4; }
        close(pfd[1]);
        pfd[1] = nw;
    }
    if (pfd[0] != target_fd) {
        if (dup2(pfd[0], target_fd) != target_fd) { perror("dup2"); return 4; }
        close(pfd[0]);
    }

    /* Write synthetic auxv-like record (AT_EXECFN = 31) with sentinel value 0x123456789abcdef0 */
    unsigned long payload[4] = { 31UL, 0x123456789abcdef0UL, 0UL, 0UL };
    if (write(pfd[1], payload, sizeof(payload)) != sizeof(payload)) { perror("write"); return 5; }
    unsigned long got[4] = {0};
    if (read(target_fd, got, sizeof(got)) != sizeof(got)) { perror("read reused"); return 6; }
    close(pfd[1]);
    close(target_fd);

    if (got[0] != 31UL || got[1] != 0x123456789abcdef0UL) {
        fprintf(stderr, "auxv reuse CORRUPTED: got=0x%lx 0x%lx\n", got[0], got[1]);
        return 7;
    }
    return 0;
}

static int test_pipe_shadow_early_close(void) {
    signal(SIGPIPE, SIG_DFL);
    int pfd[2];
    if (pipe(pfd) != 0) { perror("pipe"); return 10; }
    pid_t pid = fork();
    if (pid < 0) { perror("fork"); return 11; }
    if (pid == 0) {
        close(pfd[0]);
        usleep(30000);
        ssize_t n = write(pfd[1], "OK", 2);
        close(pfd[1]);
        _exit(n == 2 ? 0 : 1);
    }
    /* Child inherited pfd[0] too? No, let child close pfd[0], parent keeps nothing: wait—if parent closes pfd[0] first while another reader exists only briefly, test standard shell pipeline behavior: spawn writer and reader cleanly, plus self-close test */
    close(pfd[1]);
    char buf[8];
    ssize_t rn = read(pfd[0], buf, sizeof(buf));
    close(pfd[0]);
    int st = 0;
    waitpid(pid, &st, 0);
    if (!WIFEXITED(st) || WEXITSTATUS(st) != 0 || rn != 2) {
        fprintf(stderr, "pipe_shadow failed st=%d rn=%zd\n", st, rn);
        return 12;
    }
    return 0;
}

static int test_netlink_close_reuse(void) {
    int nl = socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE);
    if (nl < 0) {
        perror("socket NETLINK_ROUTE");
        return 20;
    }
    struct sockaddr_storage addr;
    socklen_t alen = sizeof(addr);
    if (getsockname(nl, (struct sockaddr *)&addr, &alen) != 0 ||
        addr.ss_family != AF_NETLINK) {
        fprintf(stderr, "NETLINK_ROUTE lost its socket family\n");
        return 20;
    }

    int pair[2];
    if (socketpair(AF_UNIX, SOCK_DGRAM, 0, pair) != 0) {
        perror("socketpair");
        return 21;
    }
    if (close(nl) != 0 || dup2(pair[0], nl) != nl) {
        perror("reuse closed netlink fd");
        return 22;
    }

    char byte = 'x';
    struct iovec iov = { .iov_base = &byte, .iov_len = 1 };
    struct msghdr message = { .msg_iov = &iov, .msg_iovlen = 1 };
    if (sendmsg(nl, &message, 0) != 1 ||
        recv(pair[1], &byte, 1, MSG_DONTWAIT) != 1 || byte != 'x') {
        fprintf(stderr, "reused Unix socket did not deliver datagram\n");
        return 23;
    }

    alen = sizeof(addr);
    if (getsockname(nl, (struct sockaddr *)&addr, &alen) != 0 ||
        addr.ss_family != AF_UNIX) {
        fprintf(stderr, "reused Unix socket has wrong family\n");
        return 24;
    }
    close(pair[0]);
    close(pair[1]);
    close(nl);
    return 0;
}

static int test_ioctl_mixed(void) {
    int mfd = -1, sfd = -1;
    if (openpty(&mfd, &sfd, NULL, NULL, NULL) != 0) { perror("openpty"); return 30; }
    struct winsize ws = { .ws_row = 36, .ws_col = 120 }, rws = {0};
    if (ioctl(mfd, TIOCSWINSZ, &ws) != 0) { perror("TIOCSWINSZ"); return 31; }
    if (ioctl(sfd, TIOCGWINSZ, &rws) != 0 || rws.ws_col != 120) {
        fprintf(stderr, "TIOCGWINSZ col=%u\n", rws.ws_col);
        close(mfd); close(sfd);
        return 32;
    }
    close(mfd); close(sfd);

    int pfd[2];
    if (pipe(pfd) != 0) { perror("pipe"); return 33; }
    if (write(pfd[1], "abcde", 5) != 5) { perror("write"); return 34; }
    int avail = -1;
    if (ioctl(pfd[0], FIONREAD, &avail) != 0 || avail != 5) {
        fprintf(stderr, "FIONREAD avail=%d errno=%d\n", avail, errno);
        close(pfd[0]); close(pfd[1]);
        return 35;
    }
    close(pfd[0]); close(pfd[1]);
    return 0;
}

static int test_stat_l2s_id0(void) {
    if (geteuid() != 0) { fprintf(stderr, "geteuid=%u\n", geteuid()); return 40; }
    struct statx stx;
    if (syscall(__NR_statx, AT_FDCWD, "/etc/os-release", 0, STATX_BASIC_STATS, &stx) != 0) {
        perror("statx");
        return 41;
    }
    char a[128], b[128];
    snprintf(a, sizeof(a), "/tmp/f9_l2s_a_%d", getpid());
    snprintf(b, sizeof(b), "/tmp/f9_l2s_b_%d", getpid());
    int fd = open(a, O_CREAT | O_WRONLY | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 42; }
    close(fd);
    if (link(a, b) != 0) { perror("link"); unlink(a); return 43; }
    struct stat sa, sb;
    if (stat(a, &sa) != 0 || stat(b, &sb) != 0 || sa.st_nlink < 2 || sb.st_nlink < 2) {
        fprintf(stderr, "l2s nlink fail %lu %lu\n", (unsigned long)sa.st_nlink, (unsigned long)sb.st_nlink);
        unlink(a); unlink(b);
        return 44;
    }
    unlink(a); unlink(b);
    return 0;
}

static int test_memfd_shared_memory_region(void) {
#ifdef SYS_memfd_create
    errno = 0;
    long rc = syscall(SYS_memfd_create, "shared-memory-region",
                      MFD_CLOEXEC | MFD_ALLOW_SEALING);
    if (rc != -1 || errno != ENOSYS) {
        fprintf(stderr, "memfd shared-memory-region rc=%ld errno=%d (expected -1/ENOSYS)\n",
                rc, errno);
        if (rc >= 0) close((int)rc);
        return 50;
    }
    return 0;
#else
    fprintf(stderr, "SYS_memfd_create not defined\n");
    return 51;
#endif
}

static int test_proc_self_fd_ro_cloexec(void) {
    char path[] = "/tmp/f9_proc_fd_XXXXXX";
    int fd = mkstemp(path);
    if (fd < 0) { perror("mkstemp"); return 60; }
    if (write(fd, "hello", 5) != 5) {
        perror("write temp");
        close(fd); unlink(path);
        return 61;
    }

    char ppath[64];
    snprintf(ppath, sizeof(ppath), "/proc/self/fd/%d", fd);
    int ro_fd = open(ppath, O_RDONLY | O_CLOEXEC);
    if (ro_fd < 0) {
        perror("open /proc/self/fd ro");
        close(fd); unlink(path);
        return 62;
    }
    int fdf = fcntl(ro_fd, F_GETFD);
    if (fdf < 0 || (fdf & FD_CLOEXEC) == 0) {
        fprintf(stderr, "proc_self_fd ro missing FD_CLOEXEC: fdf=%d errno=%d\n", fdf, errno);
        close(ro_fd); close(fd); unlink(path);
        return 63;
    }
    errno = 0;
    if (write(ro_fd, "x", 1) != -1 || errno != EBADF) {
        fprintf(stderr, "proc_self_fd ro write did not fail with EBADF (errno=%d)\n", errno);
        close(ro_fd); close(fd); unlink(path);
        return 64;
    }
    close(ro_fd);

    int opath_fd = open(path, O_PATH | O_CLOEXEC);
    if (opath_fd < 0) {
        perror("open O_PATH");
        close(fd); unlink(path);
        return 65;
    }
    snprintf(ppath, sizeof(ppath), "/proc/self/fd/%d", opath_fd);
    int ro2 = open(ppath, O_RDONLY | O_CLOEXEC);
    if (ro2 < 0) {
        perror("open /proc/self/fd O_PATH ro");
        close(opath_fd); close(fd); unlink(path);
        return 66;
    }
    fdf = fcntl(ro2, F_GETFD);
    if (fdf < 0 || (fdf & FD_CLOEXEC) == 0) {
        fprintf(stderr, "proc_self_fd O_PATH ro missing FD_CLOEXEC: fdf=%d errno=%d\n", fdf, errno);
        close(ro2); close(opath_fd); close(fd); unlink(path);
        return 67;
    }
    char buf[16] = {0};
    ssize_t rn = read(ro2, buf, sizeof(buf));
    if (rn != 5 || memcmp(buf, "hello", 5) != 0) {
        fprintf(stderr, "proc_self_fd O_PATH ro read failed: rn=%zd errno=%d\n", rn, errno);
        close(ro2); close(opath_fd); close(fd); unlink(path);
        return 68;
    }
    errno = 0;
    if (write(ro2, "x", 1) != -1 || errno != EBADF) {
        fprintf(stderr, "proc_self_fd O_PATH ro write did not fail with EBADF (errno=%d)\n", errno);
        close(ro2); close(opath_fd); close(fd); unlink(path);
        return 69;
    }
    close(ro2);
    close(opath_fd);
    close(fd);
    unlink(path);
    return 0;
}

static int test_dev_fd_stdio_cloexec(void) {
    int fd = open("/dev/fd/1", O_WRONLY | O_CLOEXEC);
    if (fd < 0) {
        perror("open /dev/fd/1");
        return 70;
    }
    int fdf = fcntl(fd, F_GETFD);
    if (fdf < 0 || (fdf & FD_CLOEXEC) == 0) {
        fprintf(stderr, "/dev/fd/1 missing FD_CLOEXEC: fdf=%d errno=%d\n", fdf, errno);
        close(fd);
        return 71;
    }
    close(fd);
    return 0;
}

static int bench_ioctl_hot(void) {
    int pfd[2];
    if (pipe(pfd) != 0) return 1;
    if (write(pfd[1], "x", 1) != 1) return 2;
    int avail = 0;
    for (int i = 0; i < 30000; i++) {
        if (ioctl(pfd[0], FIONREAD, &avail) != 0 || avail != 1) {
            close(pfd[0]); close(pfd[1]);
            return 3;
        }
    }
    close(pfd[0]); close(pfd[1]);
    printf("IOCTL_HOT_OK n=30000\n");
    return 0;
}

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], "ioctl_hot") == 0)
        return bench_ioctl_hot();
    int rc;
    if ((rc = test_auxv_close_reuse()) != 0) return rc;
    if ((rc = test_pipe_shadow_early_close()) != 0) return rc;
    if ((rc = test_netlink_close_reuse()) != 0) return rc;
    if ((rc = test_ioctl_mixed()) != 0) return rc;
    if ((rc = test_stat_l2s_id0()) != 0) return rc;
    if ((rc = test_memfd_shared_memory_region()) != 0) return rc;
    if ((rc = test_proc_self_fd_ro_cloexec()) != 0) return rc;
    if ((rc = test_dev_fd_stdio_cloexec()) != 0) return rc;
    printf("FAST9_REGRESS_OK\n");
    return 0;
}
