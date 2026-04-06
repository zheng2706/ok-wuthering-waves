"""Test with ACTUAL target set (荣斗铸锋之冠) + try reading echo names after filter."""
import time
import ctypes


def execute(ctx):
    results = {}
    def shot(label):
        s = ctx.screenshot()
        results[label] = s.get('path', '')

    def real_scroll_at(x, y, clicks):
        """Scroll at position using real mouse."""
        dm = ctx.device_manager
        cap = dm.capture_method
        hwnd = dm.interaction.hwnd_window.hwnd
        import win32gui
        px, py = int(x * cap.width), int(y * cap.height)
        sx, sy = win32gui.ClientToScreen(hwnd, (px, py))
        try:
            dm.interaction.hwnd_window.bring_to_front()
        except: pass
        time.sleep(0.2)
        ctypes.windll.user32.SetCursorPos(sx, sy)
        time.sleep(0.1)
        ctypes.windll.user32.mouse_event(0x0800, 0, 0, clicks * 120, 0)

    # Nav to echo backpack
    for _ in range(5):
        ctx.send_key('esc', after_sleep=0.7)
    time.sleep(1)
    ctx.send_key('b', after_sleep=3)
    ctx.send_key('esc', after_sleep=1)
    ctx.click(0.02, 0.30, after_sleep=2)

    # Open filter + dropdown
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    ctx.real_click(0.85, 0.454, after_sleep=2)
    shot('01_dropdown')

    # Scroll to find 荣斗铸锋之冠
    found = False
    for i in range(15):
        match = ctx.ocr(0.6, 0.4, 1.0, 0.95, match='荣斗')
        if match:
            b = match[0] if isinstance(match, list) else match
            cx = b.get('x',0) + b.get('width',0)/2
            cy = b.get('y',0) + b.get('height',0)/2
            ctx.real_click(cx, cy, after_sleep=2)
            found = True
            break
        real_scroll_at(0.85, 0.65, -3)
        time.sleep(0.8)

    results['set_found'] = found
    shot('02_set_selected')

    if not found:
        results['error'] = '荣斗铸锋之冠 not found after scrolling'
        return results

    # Verify set in panel
    check = ctx.ocr(0.6, 0.35, 1.0, 0.50, match='荣斗')
    results['set_confirmed'] = bool(check)
    shot('03_confirmed')

    # Add main stat filter: Cost4 + 暴击伤害
    add = ctx.ocr(0.6, 0.5, 1.0, 0.65, match='添加')
    if add:
        b = add[0] if isinstance(add, list) else add
        ctx.real_click(b.get('x',0)+b.get('width',0)+0.02,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)

    stat = ctx.ocr(0, 0.2, 1.0, 0.7, match='暴击伤害')
    if stat:
        b = stat[0] if isinstance(stat, list) else stat
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)

    confirm = ctx.ocr(0.3, 0.7, 1.0, 1.0, match='确认')
    if confirm:
        b = confirm[0] if isinstance(confirm, list) else confirm
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)

    shot('04_filtered')

    # === NEW: Try reading echo names from filtered results ===
    # After filtering, echoes should be visible in the grid
    # Click on the first echo and read its name from detail panel
    echo_names = []

    # Check if there are any filtered echoes
    count_ocr = ctx.ocr(0.6, 0.8, 1.0, 0.92)
    count_text = ' '.join(b.get('name','') for b in (count_ocr or []))
    results['filter_count'] = count_text

    # Click first echo in grid (approximately at col1 row1 of filtered results)
    # Grid starts at about x=0.07, y=0.12
    for col_x in [0.10, 0.20, 0.30]:
        ctx.click(col_x, 0.20, after_sleep=1.5)
        # Read echo name from detail panel (right side, top area)
        name_ocr = ctx.ocr(0.65, 0.08, 0.95, 0.15)
        if name_ocr:
            for b in name_ocr:
                n = b.get('name', '')
                if len(n) >= 2 and n not in ['COST', '+0', '+25']:
                    echo_names.append(n)
                    break

    results['echo_names'] = echo_names
    shot('05_echo_detail')

    # Reset and close
    reset = ctx.ocr(0.6, 0.8, 1.0, 0.92, match='重置')
    if reset:
        b = reset[0] if isinstance(reset, list) else reset
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)
    ctx.dbl_click(0.115, 0.900, after_sleep=1)

    return results
