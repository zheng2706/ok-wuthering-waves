"""
Try raw PostMessage to open 合鸣 dropdown.
Use WM_LBUTTONDBLCLK and various positions across the dropdown row.
"""
import time
import win32con
import win32api


def execute(ctx):
    dm = ctx.device_manager
    interaction = dm.interaction
    cap = dm.capture_method

    def check_expanded():
        """Check if dropdown shows set names."""
        r = ctx.ocr(0.6, 0.45, 1.0, 0.9)
        names = [b.get('name', '') for b in (r or [])]
        sets = [n for n in names if any(kw in n for kw in ['凝夜', '熔山', '彻空', '不绝', '浮星', '全部选择'])]
        return len(sets) > 0, names

    def raw_click(px, py, method='normal'):
        lp = win32api.MAKELONG(px, py)
        if method == 'normal':
            interaction.post(win32con.WM_MOUSEMOVE, 0, lp)
            time.sleep(0.05)
            interaction.post(win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lp)
            time.sleep(0.05)
            interaction.post(win32con.WM_LBUTTONUP, 0, lp)
        elif method == 'dblclk':
            interaction.post(win32con.WM_MOUSEMOVE, 0, lp)
            time.sleep(0.05)
            interaction.post(win32con.WM_LBUTTONDBLCLK, win32con.MK_LBUTTON, lp)
            time.sleep(0.05)
            interaction.post(win32con.WM_LBUTTONUP, 0, lp)
        elif method == 'slow':
            interaction.post(win32con.WM_MOUSEMOVE, 0, lp)
            time.sleep(0.3)
            interaction.post(win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lp)
            time.sleep(0.15)
            interaction.post(win32con.WM_LBUTTONUP, 0, lp)
        elif method == 'double_slow':
            interaction.post(win32con.WM_MOUSEMOVE, 0, lp)
            time.sleep(0.1)
            interaction.post(win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lp)
            time.sleep(0.05)
            interaction.post(win32con.WM_LBUTTONUP, 0, lp)
            time.sleep(0.3)
            interaction.post(win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lp)
            time.sleep(0.05)
            interaction.post(win32con.WM_LBUTTONUP, 0, lp)

    # Ensure filter panel is open
    fcheck = ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选')
    if not fcheck:
        print("Filter not open, opening...")
        ctx.click(0.115, 0.900, after_sleep=0.1)
        ctx.click(0.115, 0.900, after_sleep=2)

    # Test grid of positions × methods
    # Dropdown row: OCR says text at y=0.4394-0.4685
    # Try y values across the row
    y_values = [0.44, 0.45, 0.46, 0.47]
    x_values = [0.74, 0.80, 0.85, 0.90, 0.95]
    methods = ['normal', 'dblclk', 'slow', 'double_slow']

    for method in methods:
        for y_rel in y_values:
            for x_rel in x_values:
                px = int(x_rel * cap.width)
                py = int(y_rel * cap.height)
                raw_click(px, py, method)
                time.sleep(0.8)

                found, names = check_expanded()
                if found:
                    print(f"SUCCESS: method={method} at ({x_rel},{y_rel}) -> {names[:5]}")
                    s = ctx.screenshot()
                    return {'method': method, 'x': x_rel, 'y': y_rel, 'screenshot': s.get('path', '')}

        # After each method, check if panel is still open
        fcheck = ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选')
        if not fcheck:
            print(f"Panel closed after method={method}, reopening...")
            ctx.click(0.115, 0.900, after_sleep=0.1)
            ctx.click(0.115, 0.900, after_sleep=2)

    print("All methods failed")
    s = ctx.screenshot()
    return {'status': 'failed', 'screenshot': s.get('path', '')}
