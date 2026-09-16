/* Excerpt from InitOutput.c at fdfb1ce. Not the full file. */

__attribute__((noreturn)) static void gateAXFatal(const char *what,
                                                   uint32_t reason,
                                                   uint64_t serial);
static int gateAUsed = 0;
static int gateAClosing = 0; /* clean close rejects new admission */
static int gateAInternalRepair = 0; /* SUCCESS-only repair may access live lease */

struct vblank {
    struct xorg_list link;
    uint64_t id, msc;
}
