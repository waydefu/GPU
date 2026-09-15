/* p_r6_d2_present.c — Gate A P2 R6-D2 client.
 * DISPLAY=:3 only. PresentPixmap without waiting CompleteNotify, then
 * immediate Over Composite on a BGRA→RGBX pair whose destination is the
 * window backing pixmap family used by Present. After that race, wait for
 * PresentCompleteNotify (presentproto: delivered when PresentPixmap
 * completes; serial echoes the request) and only then run the later
 * Composite oracle.
 *
 * Env TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL is an X-side one-shot; this
 * client does not set it. Harness: inflight unset, oom exact "1".
 *
 *   cc -O2 -o p_r6_d2_present p_r6_d2_present.c -lxcb -lxcb-render -lxcb-present
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <xcb/present.h>
#include <xcb/render.h>
#include <xcb/xcb.h>
#include <xcb/xproto.h>

#define PRESENT_SERIAL 1u

#define W 1024
#define H 1024
#define BUF_BYTES ((uint32_t) ((size_t) W * H * sizeof(uint32_t)))

static uint32_t div255(unsigned x) {
    return (x + 128 + ((x + 128) >> 8)) >> 8;
}

static uint32_t premul(uint8_t a, uint8_t r, uint8_t g, uint8_t b) {
    return ((uint32_t) a << 24) | (div255((unsigned) r * a) << 16) |
           (div255((unsigned) g * a) << 8) | div255((unsigned) b * a);
}

static uint32_t ref_over_x8(uint32_t s, uint32_t d) {
    unsigned sa = (s >> 24) & 255;
    unsigned sr = (s >> 16) & 255, sg = (s >> 8) & 255, sb = s & 255;
    unsigned dr = (d >> 16) & 255, dg = (d >> 8) & 255, db = d & 255;
    unsigned ia = 255 - sa;
    unsigned r = sr + div255(dr * ia);
    unsigned g = sg + div255(dg * ia);
    unsigned b = sb + div255(db * ia);
    if (r > 255) r = 255;
    if (g > 255) g = 255;
    if (b > 255) b = 255;
    return (r << 16) | (g << 8) | b;
}

static xcb_render_pictformat_t find_fmt(xcb_render_query_pict_formats_reply_t *r, int depth, int alpha) {
    xcb_render_pictforminfo_iterator_t it = xcb_render_query_pict_formats_formats_iterator(r);
    for (; it.rem; xcb_render_pictforminfo_next(&it)) {
        xcb_render_pictforminfo_t *f = it.data;
        if (f->type != XCB_RENDER_PICT_TYPE_DIRECT)
            continue;
        if (f->depth != depth)
            continue;
        if (alpha && f->direct.alpha_mask == 0)
            continue;
        if (!alpha && f->direct.alpha_mask != 0)
            continue;
        return f->id;
    }
    return 0;
}

static int check_pix(xcb_connection_t *c, xcb_pixmap_t pm, uint32_t expect, const char *tag) {
    xcb_generic_error_t *e = NULL;
    xcb_get_image_reply_t *img;
    uint8_t *data;
    int len, stride, i, fail = 0, max_d = 0;
    uint32_t got0 = 0;
    img = xcb_get_image_reply(c, xcb_get_image(c, XCB_IMAGE_FORMAT_Z_PIXMAP, pm, 0, 0, W, H, ~0u), &e);
    if (e || !img) {
        printf("FAIL %s GetImage\n", tag);
        free(e);
        free(img);
        return 1;
    }
    data = xcb_get_image_data(img);
    len = xcb_get_image_data_length(img);
    stride = len / H;
    for (i = 0; i < W * H; i++) {
        int y = i / W, x = i % W;
        uint8_t *p = data + y * stride + x * 4;
        uint32_t g = ((uint32_t) p[2] << 16) | ((uint32_t) p[1] << 8) | p[0];
        int dr, dg, db, ad;
        if (i == 0)
            got0 = g;
        dr = (int) ((g >> 16) & 255) - (int) ((expect >> 16) & 255);
        dg = (int) ((g >> 8) & 255) - (int) ((expect >> 8) & 255);
        db = (int) (g & 255) - (int) (expect & 255);
        ad = abs(dr);
        if (abs(dg) > ad) ad = abs(dg);
        if (abs(db) > ad) ad = abs(db);
        if (ad > max_d) max_d = ad;
        if (ad != 0)
            fail++;
    }
    free(img);
    if (fail) {
        printf("FAIL %s pixels fail=%d maxΔ=%d got0=%08x expect=%08x\n", tag, fail, max_d, got0, expect);
        return 1;
    }
    printf("PASS %s exact_px=%d maxΔ=0 got0=%08x\n", tag, W * H, got0);
    return 0;
}

/* presentproto PresentSelectInput + CompleteNotify; XCB XGE special queue
 * (xcb_register_for_special_xge in xcb.h). Do not block the racing Composite. */
static int wait_complete_notify(xcb_connection_t *c, xcb_special_event_t *se,
                                uint32_t serial, int timeout_ms) {
    struct timespec start, now;
    if (!c || !se)
        return 1;
    clock_gettime(CLOCK_MONOTONIC, &start);
    xcb_flush(c);
    for (;;) {
        xcb_generic_event_t *ge;
        xcb_generic_event_t *pump;
        xcb_get_input_focus_reply_t *focus;

        /* Round-trip so libxcb reads the socket into the XGE special queue. */
        focus = xcb_get_input_focus_reply(c, xcb_get_input_focus(c), NULL);
        free(focus);
        ge = xcb_poll_for_special_event(c, se);
        if (ge) {
            xcb_present_complete_notify_event_t *cn =
                (xcb_present_complete_notify_event_t *) ge;
            if (cn->event_type == XCB_PRESENT_EVENT_COMPLETE_NOTIFY
                && cn->serial == serial) {
                printf("D2 CompleteNotify serial=%u kind=%u mode=%u\n",
                       cn->serial, cn->kind, cn->mode);
                free(ge);
                return 0;
            }
            free(ge);
        }
        while ((pump = xcb_poll_for_event(c)) != NULL)
            free(pump);
        if (xcb_connection_has_error(c)) {
            printf("FAIL connection during CompleteNotify wait\n");
            return 1;
        }
        clock_gettime(CLOCK_MONOTONIC, &now);
        if ((now.tv_sec - start.tv_sec) * 1000
            + (now.tv_nsec - start.tv_nsec) / 1000000 >= timeout_ms) {
            printf("FAIL CompleteNotify timeout serial=%u\n", serial);
            return 1;
        }
        usleep(1000);
    }
}

int main(int argc, char **argv) {
    const char *mode = argc > 1 ? argv[1] : "inflight";
    xcb_connection_t *c;
    xcb_screen_t *s;
    xcb_render_query_pict_formats_reply_t *fmtr;
    xcb_render_pictformat_t fmt32, fmt24;
    xcb_window_t win;
    xcb_pixmap_t presentpm, srcpm, dstpm;
    xcb_gcontext_t gc, gc32, gc24;
    xcb_render_picture_t src, dst;
    uint32_t *buf, src_px, dst_px, expect, wval[1];
    unsigned i;
    xcb_generic_error_t *e;
    const xcb_query_extension_reply_t *pe;
    xcb_present_event_t eid;
    xcb_special_event_t *se;
    xcb_void_cookie_t ck_present, ck_comp;

    setvbuf(stdout, NULL, _IONBF, 0);
    if (strcmp(mode, "inflight") != 0 && strcmp(mode, "oom") != 0) {
        printf("FAIL usage: p_r6_d2_present inflight|oom\n");
        return 1;
    }
    printf("D2_MODE %s\n", mode);

    buf = (uint32_t *) malloc((size_t) W * H * sizeof(uint32_t));
    if (!buf) {
        printf("FAIL malloc\n");
        return 1;
    }

    c = xcb_connect(NULL, NULL);
    if (xcb_connection_has_error(c)) {
        printf("FAIL connect\n");
        return 1;
    }
    pe = xcb_get_extension_data(c, &xcb_present_id);
    if (!pe || !pe->present) {
        printf("FAIL Present absent\n");
        return 1;
    }
    s = xcb_setup_roots_iterator(xcb_get_setup(c)).data;
    fmtr = xcb_render_query_pict_formats_reply(c, xcb_render_query_pict_formats(c), NULL);
    if (!fmtr) {
        printf("FAIL QueryPictFormats\n");
        return 1;
    }
    fmt32 = find_fmt(fmtr, 32, 1);
    fmt24 = find_fmt(fmtr, 24, 0);
    free(fmtr);
    if (!fmt32 || !fmt24) {
        printf("FAIL pictformat\n");
        return 1;
    }

    src_px = premul(0x80, 0xff, 0x00, 0x00);
    dst_px = 0x00008000u;
    expect = ref_over_x8(src_px, dst_px) & 0x00ffffffu;

    win = xcb_generate_id(c);
    wval[0] = s->black_pixel;
    xcb_create_window(c, 24, win, s->root, 0, 0, W, H, 0,
                      XCB_WINDOW_CLASS_INPUT_OUTPUT, s->root_visual,
                      XCB_CW_BACK_PIXEL, wval);
    xcb_map_window(c, win);
    eid = xcb_generate_id(c);
    e = xcb_request_check(c, xcb_present_select_input_checked(
            c, eid, win, XCB_PRESENT_EVENT_MASK_COMPLETE_NOTIFY));
    if (e) {
        printf("FAIL PresentSelectInput err=%d\n", e->error_code);
        free(e);
        return 1;
    }
    se = xcb_register_for_special_xge(c, &xcb_present_id, eid, NULL);
    if (!se) {
        printf("FAIL register CompleteNotify XGE\n");
        return 1;
    }
    presentpm = xcb_generate_id(c);
    srcpm = xcb_generate_id(c);
    dstpm = xcb_generate_id(c);
    gc = xcb_generate_id(c);
    gc32 = xcb_generate_id(c);
    gc24 = xcb_generate_id(c);
    src = xcb_generate_id(c);
    dst = xcb_generate_id(c);
    xcb_create_pixmap(c, 24, presentpm, win, W, H);
    xcb_create_pixmap(c, 32, srcpm, s->root, W, H);
    xcb_create_pixmap(c, 24, dstpm, s->root, W, H);
    xcb_create_gc(c, gc, presentpm, 0, NULL);
    xcb_create_gc(c, gc32, srcpm, 0, NULL);
    xcb_create_gc(c, gc24, win, 0, NULL);
    xcb_render_create_picture(c, src, srcpm, fmt32, 0, NULL);
    /* Composite destination must be the Present window backing, not a
     * disjoint pixmap, or DIRECT_ADMIT_REJECT cannot fire. */
    xcb_render_create_picture(c, dst, win, fmt24, 0, NULL);
    xcb_render_set_picture_filter(c, src, 7, "nearest", 0, NULL);

    for (i = 0; i < W * H; i++)
        buf[i] = dst_px & 0x00ffffffu;
    xcb_put_image(c, XCB_IMAGE_FORMAT_Z_PIXMAP, presentpm, gc, W, H, 0, 0, 0, 24,
                  BUF_BYTES, (const uint8_t *) buf);
    xcb_put_image(c, XCB_IMAGE_FORMAT_Z_PIXMAP, win, gc24, W, H, 0, 0, 0, 24,
                  BUF_BYTES, (const uint8_t *) buf);
    for (i = 0; i < W * H; i++)
        buf[i] = src_px;
    xcb_put_image(c, XCB_IMAGE_FORMAT_Z_PIXMAP, srcpm, gc32, W, H, 0, 0, 0, 32,
                  BUF_BYTES, (const uint8_t *) buf);
    xcb_flush(c);

    /* Warm up srcpm to S2_AHB so Composite does not incur an
     * AHardwareBuffer_allocate Binder IPC delay during the race against Present. */
    {
        xcb_pixmap_t warm_pm = xcb_generate_id(c);
        xcb_render_picture_t warm_dst = xcb_generate_id(c);
        xcb_void_cookie_t ck_warm;
        xcb_create_pixmap(c, 24, warm_pm, s->root, 8, 8);
        xcb_render_create_picture(c, warm_dst, warm_pm, fmt24, 0, NULL);
        ck_warm = xcb_render_composite_checked(c, XCB_RENDER_PICT_OP_OVER, src, XCB_NONE, warm_dst,
                                               0, 0, 0, 0, 0, 0, 8, 8);
        xcb_flush(c);
        e = xcb_request_check(c, ck_warm);
        if (e) {
            printf("FAIL warm_composite err=%d\n", e->error_code);
            free(e);
            return 1;
        }
        xcb_render_free_picture(c, warm_dst);
        xcb_free_pixmap(c, warm_pm);
        xcb_flush(c);
    }

    /* Official Present options (xcb/present.h): ASYNC so target_msc=crtc_msc
     * and present_execute_copy runs inside this request; COPY so flip is
     * skipped (CALLBACK xop=4 and gpu_copy_pending live only on that path).
     * Pipeline PresentPixmap and immediate Over Composite into the same socket
     * flush so the X dispatch loop receives the immediate Composite as soon as
     * possible. The valid outcome is either busy→reason-1 reject or a complete
     * Present watermark before the first direct lease; timing cannot guarantee
     * which branch wins. */
    ck_present = xcb_present_pixmap_checked(
            c, win, presentpm, PRESENT_SERIAL, XCB_NONE, XCB_NONE, 0, 0,
            XCB_NONE, XCB_NONE, XCB_NONE,
            XCB_PRESENT_OPTION_ASYNC | XCB_PRESENT_OPTION_COPY,
            0, 0, 0, 0, NULL);
    ck_comp = xcb_render_composite_checked(
            c, XCB_RENDER_PICT_OP_OVER, src, XCB_NONE, dst, 0, 0, 0, 0, 0, 0, W, H);
    xcb_flush(c);

    e = xcb_request_check(c, ck_present);
    if (e) {
        printf("FAIL PresentPixmap err=%d\n", e->error_code);
        free(e);
        return 1;
    }
    e = xcb_request_check(c, ck_comp);
    if (e) {
        printf("FAIL D2-immediate Composite err=%d\n", e->error_code);
        free(e);
        return 1;
    }
    printf("D2 immediate Composite returned (admission reject is an X event, not a protocol error)\n");

    /* Official CompleteNotify is after presentation, not before the race.
     * Wait here so the later oracle Composite is post-quiescence. */
    if (wait_complete_notify(c, se, PRESENT_SERIAL, 2000)) {
        xcb_unregister_for_special_event(c, se);
        return 1;
    }
    xcb_unregister_for_special_event(c, se);
    se = NULL;
    for (i = 0; i < W * H; i++)
        buf[i] = dst_px & 0x00ffffffu;
    xcb_put_image(c, XCB_IMAGE_FORMAT_Z_PIXMAP, win, gc24, W, H, 0, 0, 0, 24,
                  BUF_BYTES, (const uint8_t *) buf);
    e = xcb_request_check(c, xcb_render_composite_checked(
            c, XCB_RENDER_PICT_OP_OVER, src, XCB_NONE, dst, 0, 0, 0, 0, 0, 0, W, H));
    if (e) {
        printf("FAIL D2-later Composite err=%d\n", e->error_code);
        free(e);
        free(buf);
        return 1;
    }
    if (check_pix(c, win, expect, "D2-later-composite")) {
        free(buf);
        return 1;
    }

    free(buf);
    xcb_disconnect(c);
    printf("RESULT p_r6_d2_present CLIENT_OK mode=%s later pixels exact; X reject/early-ack on server trace\n",
           mode);
    return 0;
}
