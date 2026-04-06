"""Test foreground click on echo grid cards using mouse_event."""

import ctypes
import time


def click_foreground(hwnd, cap_width, cap_height, x, y):
    """Click at relative (x, y) using foreground mouse_event."""
    import win32gui

    px = int(x * cap_width)
    py = int(y * cap_height)
    screen_x, screen_y = win32gui.ClientToScreen(hwnd, (px, py))

    try:
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.15)
    except Exception:
        pass

    sm_cx = ctypes.windll.user32.GetSystemMetrics(0)
    sm_cy = ctypes.windll.user32.GetSystemMetrics(1)
    norm_x = int(screen_x * 65536 / sm_cx)
    norm_y = int(screen_y * 65536 / sm_cy)

    MOUSEEVENTF_ABSOLUTE = 0x8000
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    # Move mouse
    ctypes.windll.user32.mouse_event(
        MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, norm_x, norm_y, 0, 0)
    time.sleep(0.05)
    # Click down
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    # Click up
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    return screen_x, screen_y


def execute(ctx):
    import win32gui

    results = {}

    hwnd = win32gui.FindWindow('UnrealWindow', None)
    if not hwnd:
        return {"error": "Game window not found"}
    results['hwnd'] = hwnd

    cap = ctx.device_manager.capture_method
    results['capture_size'] = f"{cap.width}x{cap.height}"

    # Make sure we're on echo backpack
    header = ctx.ocr(0, 0, 0.5, 0.15)
    results['header'] = [b.get('name', '') for b in header]
    if not any('声骸' in b.get('name', '') for b in header):
        ctx.send_key('b', after_sleep=2)
        warning = ctx.ocr(0.2, 0.3, 0.8, 0.8, match='弃置')
        if warning:
            ctx.send_key('esc', after_sleep=1)

    positions = [
        (0.12, 0.25, "card1_center"),
        (0.12, 0.20, "card1_upper"),
        (0.25, 0.25, "card2_center"),
    ]

    for x, y, label in positions:
        print(f"Foreground click ({x}, {y}) [{label}]...")
        sx, sy = click_foreground(hwnd, cap.width, cap.height, x, y)
        time.sleep(1.5)

        enhance = ctx.ocr(0.82, 0.86, 0.97, 0.96)
        enhance_text = [b.get('name', '') for b in enhance]
        has_enhance = any('培养' in t for t in enhance_text)

        results[label] = {
            'screen': f"({sx}, {sy})",
            'enhance': enhance_text,
            'found': has_enhance,
        }
        print(f"  screen=({sx},{sy}), enhance={enhance_text}, found={has_enhance}")

        if has_enhance:
            shot = ctx.screenshot()
            results['detail_screenshot'] = shot.get('path', '')
            print(f"  >>> SUCCESS!")
            break

    return results
