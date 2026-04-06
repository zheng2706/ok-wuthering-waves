"""
Use REAL mouse input (SetCursorPos + mouse_event) to click dropdown.
This requires the game window to be in foreground.
"""
import time
import ctypes
import win32gui
import win32con


def execute(ctx):
    dm = ctx.device_manager
    cap = dm.capture_method
    interaction = dm.interaction
    hw = interaction.hwnd_window

    def real_click(rel_x, rel_y, after=1.0):
        """Send real mouse click using OS-level input."""
        # Convert relative to client pixel coords
        px = int(rel_x * cap.width)
        py = int(rel_y * cap.height)

        # Convert client coords to screen coords
        hwnd = hw.hwnd
        screen_x, screen_y = win32gui.ClientToScreen(hwnd, (px, py))
        print(f"  rel=({rel_x},{rel_y}) client=({px},{py}) screen=({screen_x},{screen_y})")

        # Bring window to foreground using framework method
        try:
            hw.bring_to_front()
        except Exception:
            try:
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass
        time.sleep(0.3)

        # Move cursor
        ctypes.windll.user32.SetCursorPos(screen_x, screen_y)
        time.sleep(0.1)

        # Click
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(after)

    # Ensure filter panel is open
    fcheck = ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选')
    if not fcheck:
        print("Opening filter panel...")
        ctx.click(0.115, 0.900, after_sleep=0.1)
        ctx.click(0.115, 0.900, after_sleep=2)

    # Click 合鸣 dropdown with REAL mouse
    print("=== Real-clicking 合鸣 dropdown at (0.85, 0.454) ===")
    real_click(0.85, 0.454, after=2)

    # Check if expanded
    r = ctx.ocr(0.6, 0.45, 1.0, 0.85)
    names = [b.get('name', '') for b in (r or [])]
    sets = [n for n in names if any(kw in n for kw in ['凝夜', '熔山', '彻空', '不绝', '浮星', '全部'])]
    print(f"After real click: {str(names[:10]).encode('utf-8','replace')}")

    if len(sets) > 1:
        print(f"DROPDOWN EXPANDED! Sets: {sets}")
        s = ctx.screenshot()
        return {'method': 'real_click', 'screenshot': s.get('path', ''), 'sets': sets}

    # Try clicking the ∨ arrow area
    print("=== Real-clicking dropdown arrow at (0.95, 0.454) ===")
    real_click(0.95, 0.454, after=2)

    r = ctx.ocr(0.6, 0.45, 1.0, 0.85)
    names = [b.get('name', '') for b in (r or [])]
    print(f"After arrow click: done")

    s = ctx.screenshot()
    return {'names': names[:10], 'screenshot': s.get('path', '')}
