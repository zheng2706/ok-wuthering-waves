"""Test DPI-aware click on echo grid.
DPI=144 (150%) may require coordinate adjustment."""

import ctypes
import time
import win32gui
import win32api
import win32con


def execute(ctx):
    results = {}

    hwnd = win32gui.FindWindow('UnrealWindow', None)
    cap = ctx.device_manager.capture_method
    w, h = cap.width, cap.height

    # Make this thread DPI-aware
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        pass

    # Re-check metrics after DPI awareness
    screen_w = ctypes.windll.user32.GetSystemMetrics(0)
    screen_h = ctypes.windll.user32.GetSystemMetrics(1)
    window_rect = win32gui.GetWindowRect(hwnd)
    client_origin = win32gui.ClientToScreen(hwnd, (0, 0))
    dpi = 96
    try:
        dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
    except Exception:
        pass

    results['screen_after_dpi'] = f"{screen_w}x{screen_h}"
    results['window_rect'] = window_rect
    results['client_origin'] = client_origin
    results['dpi'] = dpi
    print(f"Screen (DPI-aware): {screen_w}x{screen_h}")
    print(f"Window rect: {window_rect}")
    print(f"Client origin: {client_origin}")
    print(f"DPI: {dpi}")
    print(f"Capture: {w}x{h}")

    # Open backpack if needed
    header = ctx.ocr(0, 0, 0.5, 0.15, match='声骸')
    if not header:
        # Close any menu first
        for _ in range(3):
            ctx.send_key('esc', after_sleep=0.5)
        time.sleep(0.3)
        ctx.send_key('b', after_sleep=2)
        # Dismiss popup
        warning = ctx.ocr(0.2, 0.3, 0.8, 0.8, match='弃置')
        if warning:
            ctx.send_key('esc', after_sleep=1)

    # Try clicking with DPI-adjusted coordinates
    target_x, target_y = 0.12, 0.25
    px = int(target_x * w)
    py = int(target_y * h)
    sx, sy = win32gui.ClientToScreen(hwnd, (px, py))

    # Scale factor = DPI / 96
    scale = dpi / 96.0
    print(f"\nTarget: rel({target_x}, {target_y}) -> client({px}, {py}) -> screen({sx}, {sy}), scale={scale}")

    # Method A: Normal SetCursorPos (uses logical coords)
    print("\n=== Method A: SetCursorPos (logical) ===")
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.2)
    win32api.SetCursorPos((sx, sy))
    time.sleep(0.1)
    # Get actual cursor position
    actual = win32api.GetCursorPos()
    print(f"  SetCursorPos({sx}, {sy}), actual cursor: {actual}")
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(1.5)

    enhance = ctx.ocr(0.82, 0.86, 0.97, 0.96)
    found_a = any('培养' in b.get('name', '') for b in enhance)
    results['method_a'] = found_a
    print(f"  Enhance found: {found_a}")

    if found_a:
        shot = ctx.screenshot()
        results['screenshot'] = shot.get('path', '')
        return results

    # Method B: DPI-scaled coordinates
    print("\n=== Method B: DPI-scaled SetCursorPos ===")
    scaled_sx = int(sx * scale)
    scaled_sy = int(sy * scale)
    print(f"  Scaled: ({scaled_sx}, {scaled_sy})")
    win32api.SetCursorPos((scaled_sx, scaled_sy))
    time.sleep(0.1)
    actual = win32api.GetCursorPos()
    print(f"  SetCursorPos({scaled_sx}, {scaled_sy}), actual cursor: {actual}")
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(1.5)

    enhance = ctx.ocr(0.82, 0.86, 0.97, 0.96)
    found_b = any('培养' in b.get('name', '') for b in enhance)
    results['method_b'] = found_b
    print(f"  Enhance found: {found_b}")

    if found_b:
        shot = ctx.screenshot()
        results['screenshot'] = shot.get('path', '')
        return results

    # Method C: Use SendMessage WM_LBUTTONDOWN directly to window
    print("\n=== Method C: SendMessage WM_LBUTTONDOWN ===")
    import win32con
    lParam = (py << 16) | (px & 0xFFFF)  # MAKELPARAM(px, py)
    print(f"  SendMessage WM_LBUTTONDOWN lParam=0x{lParam:08x} ({px}, {py})")
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    time.sleep(0.05)
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
    time.sleep(1.5)

    enhance = ctx.ocr(0.82, 0.86, 0.97, 0.96)
    found_c = any('培养' in b.get('name', '') for b in enhance)
    results['method_c'] = found_c
    print(f"  Enhance found: {found_c}")

    shot = ctx.screenshot()
    results['screenshot'] = shot.get('path', '')
    return results
