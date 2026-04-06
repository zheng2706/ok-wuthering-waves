"""Check DPI scaling issue - compare logical vs physical window size."""
import ctypes
import win32gui


def execute(ctx):
    hwnd = win32gui.FindWindow('UnrealWindow', None)
    results = {}

    # Before DPI awareness
    client_rect_before = win32gui.GetClientRect(hwnd)
    window_rect_before = win32gui.GetWindowRect(hwnd)
    screen_w_before = ctypes.windll.user32.GetSystemMetrics(0)
    screen_h_before = ctypes.windll.user32.GetSystemMetrics(1)

    results['before_dpi_aware'] = {
        'client_rect': client_rect_before,
        'window_rect': window_rect_before,
        'screen': f"{screen_w_before}x{screen_h_before}",
    }

    # Set DPI awareness
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception as e:
        results['dpi_awareness_error'] = str(e)
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

    # After DPI awareness
    client_rect_after = win32gui.GetClientRect(hwnd)
    window_rect_after = win32gui.GetWindowRect(hwnd)
    screen_w_after = ctypes.windll.user32.GetSystemMetrics(0)
    screen_h_after = ctypes.windll.user32.GetSystemMetrics(1)

    dpi = 96
    try:
        dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
    except Exception:
        pass

    results['after_dpi_aware'] = {
        'client_rect': client_rect_after,
        'window_rect': window_rect_after,
        'screen': f"{screen_w_after}x{screen_h_after}",
        'dpi': dpi,
        'scale': dpi / 96.0,
    }

    # Capture info
    cap = ctx.device_manager.capture_method
    results['capture'] = {
        'width': cap.width,
        'height': cap.height,
        'type': type(cap).__name__,
    }

    # The key question: is capture size < actual client rect?
    actual_w = client_rect_after[2]
    actual_h = client_rect_after[3]
    results['MISMATCH'] = cap.width != actual_w or cap.height != actual_h
    results['actual_physical'] = f"{actual_w}x{actual_h}"
    results['capture_size'] = f"{cap.width}x{cap.height}"

    print(f"Before DPI aware: client={client_rect_before}, screen={screen_w_before}x{screen_h_before}")
    print(f"After DPI aware:  client={client_rect_after}, screen={screen_w_after}x{screen_h_after}")
    print(f"DPI: {dpi}, Scale: {dpi/96:.1f}x")
    print(f"Capture: {cap.width}x{cap.height}")
    print(f"Physical client: {actual_w}x{actual_h}")
    print(f">>> MISMATCH: {cap.width != actual_w or cap.height != actual_h}")

    return results
