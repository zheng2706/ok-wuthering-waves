"""
Test filter icon with double-click and various click strategies.
The icon at (0.115, 0.900) shows hover effect but click doesn't register.
Try: double-click, longer down_time, move-then-click with delay.
"""
import time
import win32con
import win32api


def execute(ctx):
    dm = ctx.device_manager
    interaction = dm.interaction
    cap = dm.capture_method

    # Target: filter funnel icon
    rel_x, rel_y = 0.115, 0.900
    px = int(rel_x * cap.width)   # 441
    py = int(rel_y * cap.height)  # 1944

    def check_filter():
        """Check if filter panel opened."""
        r = ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选')
        return bool(r)

    def shot(label):
        s = ctx.screenshot()
        print(f"  [{label}] {s.get('path','')}")

    # === Strategy 1: Double-click via ctx.click ===
    print("=== Strategy 1: Double ctx.click ===")
    ctx.click(rel_x, rel_y, after_sleep=0.1)
    ctx.click(rel_x, rel_y, after_sleep=1.5)
    if check_filter():
        print("  SUCCESS with double ctx.click!")
        shot('double_click')
        return {'method': 'double_ctx_click'}
    shot('after_double_click')

    # === Strategy 2: Move first, wait, then click ===
    print("=== Strategy 2: Move + wait + click ===")
    # Send WM_MOUSEMOVE first
    long_pos = win32api.MAKELONG(px, py)
    interaction.post(win32con.WM_MOUSEMOVE, 0, long_pos)
    time.sleep(0.5)
    # Now send click
    interaction.post(win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, long_pos)
    time.sleep(0.05)
    interaction.post(win32con.WM_LBUTTONUP, 0, long_pos)
    time.sleep(2)
    if check_filter():
        print("  SUCCESS with move+wait+click!")
        shot('move_wait_click')
        return {'method': 'move_wait_click'}
    shot('after_move_wait')

    # === Strategy 3: Longer down_time ===
    print("=== Strategy 3: Long down_time click ===")
    interaction.post(win32con.WM_MOUSEMOVE, 0, long_pos)
    time.sleep(0.1)
    interaction.post(win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, long_pos)
    time.sleep(0.2)  # Hold for 200ms
    interaction.post(win32con.WM_LBUTTONUP, 0, long_pos)
    time.sleep(2)
    if check_filter():
        print("  SUCCESS with long down_time!")
        shot('long_down')
        return {'method': 'long_down_time'}
    shot('after_long_down')

    # === Strategy 4: WM_LBUTTONDBLCLK ===
    print("=== Strategy 4: WM_LBUTTONDBLCLK ===")
    interaction.post(win32con.WM_MOUSEMOVE, 0, long_pos)
    time.sleep(0.1)
    interaction.post(win32con.WM_LBUTTONDBLCLK, win32con.MK_LBUTTON, long_pos)
    time.sleep(0.05)
    interaction.post(win32con.WM_LBUTTONUP, 0, long_pos)
    time.sleep(2)
    if check_filter():
        print("  SUCCESS with DBLCLK!")
        shot('dblclk')
        return {'method': 'dblclk'}
    shot('after_dblclk')

    # === Strategy 5: Multiple rapid clicks ===
    print("=== Strategy 5: Triple rapid click ===")
    for i in range(3):
        interaction.post(win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, long_pos)
        time.sleep(0.02)
        interaction.post(win32con.WM_LBUTTONUP, 0, long_pos)
        time.sleep(0.05)
    time.sleep(2)
    if check_filter():
        print("  SUCCESS with triple click!")
        shot('triple')
        return {'method': 'triple_click'}
    shot('after_triple')

    print("=== All strategies failed ===")
    return {'method': 'none'}
