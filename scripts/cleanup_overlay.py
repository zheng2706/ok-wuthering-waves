"""Close any open overlay/panel and return to main world."""
import time


def execute(ctx):
    results = {}
    def shot(label):
        s = ctx.screenshot()
        results[label] = s.get('path', '')

    shot('00_before')

    # Try clicking X button on overlay (top-right)
    ctx.real_click(0.96, 0.03, after_sleep=1)
    shot('01_after_x')

    # Multiple ESC to close everything
    for i in range(6):
        ctx.send_key('esc', after_sleep=0.8)
    shot('02_after_esc')

    # Check if we're in main world (no menu keywords)
    time.sleep(1)
    shot('03_final')

    return results
