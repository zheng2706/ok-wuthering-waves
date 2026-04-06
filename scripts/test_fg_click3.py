"""Debug foreground click - check coordinates and try SetCursorPos approach."""
import ctypes
import ctypes.wintypes
import time
import win32gui
import win32api
import win32con


def execute(ctx):
    results = {}

    hwnd = win32gui.FindWindow('UnrealWindow', None)
    cap = ctx.device_manager.capture_method
    w, h = cap.width, cap.height

    # Window position info
    window_rect = win32gui.GetWindowRect(hwnd)
    client_rect = win32gui.GetClientRect(hwnd)
    client_origin = win32gui.ClientToScreen(hwnd, (0, 0))

    screen_w = ctypes.windll.user32.GetSystemMetrics(0)
    screen_h = ctypes.windll.user32.GetSystemMetrics(1)

    # DPI awareness
    try:
        dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
    except Exception:
        dpi = 96

    results['window_rect'] = window_rect
    results['client_rect'] = client_rect
    results['client_origin'] = client_origin
    results['screen'] = f"{screen_w}x{screen_h}"
    results['capture'] = f"{w}x{h}"
    results['dpi'] = dpi

    print(f"Window rect: {window_rect}")
    print(f"Client rect: {client_rect}")
    print(f"Client origin (screen): {client_origin}")
    print(f"Screen: {screen_w}x{screen_h}")
    print(f"Capture: {w}x{h}")
    print(f"DPI: {dpi}")

    # Target: first echo card center
    rel_x, rel_y = 0.12, 0.25
    px, py = int(rel_x * w), int(rel_y * h)
    sx, sy = win32gui.ClientToScreen(hwnd, (px, py))
    print(f"\nTarget: rel({rel_x}, {rel_y}) -> client({px}, {py}) -> screen({sx}, {sy})")

    # Method 1: SetCursorPos + mouse_event (no ABSOLUTE flag)
    print("\n=== Method 1: SetCursorPos + mouse_event ===")
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.2)
    win32api.SetCursorPos((sx, sy))
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(1.5)

    enhance = ctx.ocr(0.82, 0.86, 0.97, 0.96)
    found = any('培养' in b.get('name', '') for b in enhance)
    print(f"  Result: enhance={found}")
    results['method1_found'] = found

    if found:
        shot = ctx.screenshot()
        results['screenshot'] = shot.get('path', '')
        return results

    # Method 2: Try second card position
    print("\n=== Method 2: Second card ===")
    rel_x2, rel_y2 = 0.25, 0.25
    px2, py2 = int(rel_x2 * w), int(rel_y2 * h)
    sx2, sy2 = win32gui.ClientToScreen(hwnd, (px2, py2))
    print(f"Target: rel({rel_x2}, {rel_y2}) -> screen({sx2}, {sy2})")

    win32api.SetCursorPos((sx2, sy2))
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(1.5)

    enhance = ctx.ocr(0.82, 0.86, 0.97, 0.96)
    found = any('培养' in b.get('name', '') for b in enhance)
    print(f"  Result: enhance={found}")
    results['method2_found'] = found

    if found:
        shot = ctx.screenshot()
        results['screenshot'] = shot.get('path', '')
        return results

    # Method 3: Double click first card
    print("\n=== Method 3: Double click ===")
    win32api.SetCursorPos((sx, sy))
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.02)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.02)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(1.5)

    enhance = ctx.ocr(0.82, 0.86, 0.97, 0.96)
    found = any('培养' in b.get('name', '') for b in enhance)
    print(f"  Result: enhance={found}")
    results['method3_dblclick'] = found

    if found:
        shot = ctx.screenshot()
        results['screenshot'] = shot.get('path', '')
        return results

    shot = ctx.screenshot()
    results['screenshot'] = shot.get('path', '')
    return results
