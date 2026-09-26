// X3-DIRECT-FEAS-01 diagnostic 2: GL_EXT_memory_object_fd storage variants on a dma-buf.
// diag-01 showed the opaque-fd import of a dma-buf succeeds (memfd control rejected) but
// BufferStorageMem / TexStorageMem2D give GL_INVALID_VALUE. Sweep the parameters the spec ties
// to INVALID_VALUE (size/offset vs object size, dedicated flag) and the texture width vs pitch.

#include "diag01_body.inc"

typedef void (*PFN_glGetMemoryObjectParameterivEXT)(GLuint, GLenum, GLint *);
typedef GLboolean (*PFN_glIsMemoryObjectEXT)(GLuint);

static void pbo_check(int fd, GLuint pbo, const char *tag) {
    GLuint tex;
    p_glGenTextures(1, &tex);
    p_glBindTexture(GL_TEXTURE_2D, tex);
    glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, W, H);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    for (int v = 0; v < 3; v++) {
        fill(fd, v, v != 2);
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, pbo);
        glPixelStorei(GL_UNPACK_ROW_LENGTH, PITCH / 4);
        p_glBindTexture(GL_TEXTURE_2D, tex);
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, W, H, GL_RGBA, GL_UNSIGNED_BYTE, (const void *) 0);
        GLenum e1 = p_glGetError();
        glPixelStorei(GL_UNPACK_ROW_LENGTH, 0);
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0);
        int de = draw_read(GL_TEXTURE_2D, tex);
        printf("PBO[%s] v=%d%s upload_err=0x%x draw_err=0x%x mismatch=%ld mismatch_flipped=%ld of=%d wrong_pattern_mismatch=%ld\n",
               tag, v, v == 2 ? "(nosync)" : "", e1, de, compare(DRM_FORMAT_ABGR8888, v, 0),
               compare(DRM_FORMAT_ABGR8888, v, 1), W * H, compare(DRM_FORMAT_ABGR8888, (v + 1) % 3, 0));
    }
    p_glDeleteTextures(1, &tex);
}

int main(void) {
    if (load()) return 1;
    q_glGenBuffers = dlsym(gles_lib, "glGenBuffers");
    q_glBindBuffer = dlsym(gles_lib, "glBindBuffer");
    q_glTexStorage2D = dlsym(gles_lib, "glTexStorage2D");
    q_glTexSubImage2D = dlsym(gles_lib, "glTexSubImage2D");
    dpy = p_eglGetDisplay(EGL_DEFAULT_DISPLAY);
    EGLint maj, min; p_eglInitialize(dpy, &maj, &min);
    p_eglBindAPI(EGL_OPENGL_ES_API);
    EGLint cattr[] = { EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT_KHR, EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
                       EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8, EGL_NONE };
    EGLConfig cfg; EGLint nc = 0; p_eglChooseConfig(dpy, cattr, &cfg, 1, &nc);
    EGLint xattr[] = { EGL_CONTEXT_CLIENT_VERSION, 3, EGL_NONE };
    EGLContext ctx = p_eglCreateContext(dpy, cfg, EGL_NO_CONTEXT, xattr);
    EGLint sattr[] = { EGL_WIDTH, 16, EGL_HEIGHT, 16, EGL_NONE };
    EGLSurface surf = p_eglCreatePbufferSurface(dpy, cfg, sattr);
    if (!p_eglMakeCurrent(dpy, surf, surf, ctx)) { printf("CTX=FAIL\n"); return 1; }
    if (gl_setup()) return 1;
    p_cmo = (PFN_glCreateMemoryObjectsEXT) p_eglGetProcAddress("glCreateMemoryObjectsEXT");
    p_imfd = (PFN_glImportMemoryFdEXT) p_eglGetProcAddress("glImportMemoryFdEXT");
    p_bsm = (PFN_glBufferStorageMemEXT) p_eglGetProcAddress("glBufferStorageMemEXT");
    p_tsm = (PFN_glTexStorageMem2DEXT) p_eglGetProcAddress("glTexStorageMem2DEXT");
    p_mop = (PFN_glMemoryObjectParameterivEXT) p_eglGetProcAddress("glMemoryObjectParameterivEXT");
    PFN_glGetMemoryObjectParameterivEXT gmop = (PFN_glGetMemoryObjectParameterivEXT) p_eglGetProcAddress("glGetMemoryObjectParameterivEXT");
    PFN_glIsMemoryObjectEXT ismo = (PFN_glIsMemoryObjectEXT) p_eglGetProcAddress("glIsMemoryObjectEXT");
    int fd = heap_alloc();
    if (fd < 0) return 1;

    /* import size given to GL x storage size x dedicated */
    struct { GLuint64 isz; GLsizeiptr ssz; int ded; } bv[] = {
        { 622592, 622592, 0 }, { 622592, 622592, 1 }, { 622592, 4096, 0 }, { 622592, 4096, 1 },
        { 4096, 4096, 0 }, { 1048576, 622592, 0 } };
    for (unsigned i = 0; i < sizeof bv / sizeof *bv; i++) {
        GLuint mo = 0; while (p_glGetError()) {}
        p_cmo(1, &mo);
        GLenum e0 = p_glGetError();
        if (bv[i].ded) { GLint d = GL_TRUE; p_mop(mo, GL_DEDICATED_MEMORY_OBJECT_EXT, &d); }
        GLenum ep = p_glGetError();
        p_imfd(mo, bv[i].isz, GL_HANDLE_TYPE_OPAQUE_FD_EXT, dup(fd));
        GLenum ei = p_glGetError();
        GLint dq = -1; gmop(mo, GL_DEDICATED_MEMORY_OBJECT_EXT, &dq);
        GLuint pbo; glGenBuffers(1, &pbo); glBindBuffer(GL_PIXEL_UNPACK_BUFFER, pbo);
        while (p_glGetError()) {}
        p_bsm(GL_PIXEL_UNPACK_BUFFER, bv[i].ssz, mo, 0);
        GLenum es = p_glGetError();
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0);
        printf("BUF import_size=%llu storage_size=%ld dedicated=%d | mo=%u is=%d create_err=0x%x param_err=0x%x import_err=0x%x dedicated_q=%d storage_err=0x%x\n",
               (unsigned long long) bv[i].isz, (long) bv[i].ssz, bv[i].ded, mo, ismo(mo), e0, ep, ei, dq, es);
        if (!es && bv[i].ssz == 622592) pbo_check(fd, pbo, bv[i].ded ? "ded" : "nonded");
    }

    /* texture: width = pitch/4 (1216) so a driver-chosen linear pitch can equal 4864 */
    struct { int w; int ded; GLint tiling; } tv[] = {
        { 1216, 0, GL_LINEAR_TILING_EXT }, { 1216, 1, GL_LINEAR_TILING_EXT },
        { 1200, 1, GL_LINEAR_TILING_EXT }, { 1216, 1, 0x9584 /* OPTIMAL */ } };
    for (unsigned i = 0; i < sizeof tv / sizeof *tv; i++) {
        GLuint mo = 0; while (p_glGetError()) {}
        p_cmo(1, &mo);
        if (tv[i].ded) { GLint d = GL_TRUE; p_mop(mo, GL_DEDICATED_MEMORY_OBJECT_EXT, &d); }
        p_imfd(mo, 622592, GL_HANDLE_TYPE_OPAQUE_FD_EXT, dup(fd));
        GLenum ei = p_glGetError();
        GLuint tex; p_glGenTextures(1, &tex); p_glBindTexture(GL_TEXTURE_2D, tex);
        p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_TILING_EXT, tv[i].tiling);
        p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        while (p_glGetError()) {}
        p_tsm(GL_TEXTURE_2D, 1, GL_RGBA8, tv[i].w, H, mo, 0);
        GLenum es = p_glGetError();
        printf("TEX w=%d dedicated=%d tiling=0x%x import_err=0x%x storage_err=0x%x\n", tv[i].w, tv[i].ded, tv[i].tiling, ei, es);
        p_glDeleteTextures(1, &tex);
    }
    printf("DONE\n");
    return 0;
}
