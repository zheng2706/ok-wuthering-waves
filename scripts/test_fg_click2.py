"""Test foreground click directly (assumes echo backpack is already open, no popup)."""
import ctypes
import time


def click_fg(hwnd, w, h, x, y):
    import win32gui
    px, py = int(x * w), int(y * h)
    sx, sy = win32gui.ClientToScreen(hwnd, (px, py))
    try:
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.15)
    except Exception:
        pass
    sm_cx = ctypes.windll.user32.GetSystemMetrics(0)
    sm_cy = ctypes.windll.user32.GetSystemMetrics(1)
    nx = int(sx * 65536 / sm_cx)
    ny = int(sy * 65536 / sm_cy)
    ctypes.windll.user32.mouse_event(0x8000 | 0x0001, nx, ny, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
    return sx, sy


def execute(ctx):
    import win32gui
    hwnd = win32gui.FindWindow('UnrealWindow', None)
    cap = ctx.device_manager.capture_method
    w, h = cap.width, cap.height
    print(f"Window: {hwnd}, Capture: {w}x{h}")

    # Grid positions to test (first row)
    positions = [
        (0.12, 0.25), (0.12, 0.20), (0.25, 0.25),
        (0.38, 0.25), (0.12, 0.15), (0.18, 0.20),
    ]

    for x, y in positions:
        sx, sy = click_fg(hwnd, w, h, x, y)
        time.sleep(1.5)

        enhance = ctx.ocr(0.82, 0.86, 0.97, 0.96)
        found = any('培养' in b.get('name', '') for b in enhance)
        print(f"  ({x:.2f}, {y:.2f}) -> screen({sx}, {sy}): enhance={found}")

        if found:
            shot = ctx.screenshot()
            print(f"  >>> HIT! Screenshot: {shot.get('path', '')}")
            return {"success": True, "pos": (x, y), "screen": (sx, sy), "screenshot": shot.get('path', '')}

    # If none worked, take screenshot to see what happened
    shot = ctx.screenshot()
    print(f"All positions failed. Screenshot: {shot.get('path', '')}")
    return {"success": False, "screenshot": shot.get('path', '')}
