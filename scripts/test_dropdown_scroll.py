"""验证下拉框滚动: 先截图确认布局，再用OCR定位下拉框，real_scroll滚动查找套装。"""
import ctypes
import time
import win32gui


def _ensure_echo_backpack(ctx):
    for attempt in range(10):
        cancel = ctx.ocr(0.1, 0.3, 0.9, 0.9, match='取消')
        if cancel:
            b = cancel[0] if isinstance(cancel, list) else cancel
            ctx.click(b.get('x',0)+b.get('width',0)/2,
                      b.get('y',0)+b.get('height',0)/2, after_sleep=1.5)
            continue
        top = ctx.ocr(0, 0, 0.5, 0.12)
        texts = ' '.join(b.get('name', '') for b in (top or []))
        if any(kw in texts for kw in ['武器', '声骸', '补给', '资源']):
            ctx.click(0.02, 0.30, after_sleep=2)
            return True
        if any(kw in texts for kw in ['终端', '活动', '商城', '共鸣者']):
            ctx.send_key('esc', after_sleep=1)
            continue
        ctx.send_key('b', after_sleep=3)
    return False


def _real_scroll_at(ctx, x, y, clicks=-3):
    """Real mouse wheel scroll using SetCursorPos + mouse_event."""
    dm = ctx.device_manager
    cap = dm.capture_method
    hwnd = dm.interaction.hwnd_window.hwnd
    px = int(x * cap.width)
    py = int(y * cap.height)
    screen_x, screen_y = win32gui.ClientToScreen(hwnd, (px, py))
    try:
        dm.interaction.hwnd_window.bring_to_front()
    except Exception:
        pass
    time.sleep(0.2)
    ctypes.windll.user32.SetCursorPos(screen_x, screen_y)
    time.sleep(0.1)
    ctypes.windll.user32.mouse_event(0x0800, 0, 0, clicks * 120, 0)


def execute(ctx):
    results = {}
    step = [0]
    def shot(label):
        step[0] += 1
        s = ctx.screenshot()
        results[f'{step[0]:02d}_{label}'] = s.get('path', '')

    if not _ensure_echo_backpack(ctx):
        return {'error': 'nav failed'}
    shot('backpack')

    # Open filter panel with verification
    for _ in range(3):
        ctx.dbl_click(0.115, 0.900, after_sleep=2)
        if ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
            break
    results['panel'] = bool(ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'))
    shot('panel')

    if not results['panel']:
        return results

    # OCR dump the filter panel to find the dropdown position
    panel_ocr = ctx.ocr(0.6, 0.2, 1.0, 0.6)
    results['panel_items'] = [
        f"{b.get('name','')}: ({b.get('x',0):.3f},{b.get('y',0):.3f})"
        for b in (panel_ocr or [])
    ]

    # Find "合鸣" or "全部" label to locate dropdown
    dropdown_match = ctx.ocr(0.6, 0.3, 1.0, 0.5, match='全部')
    if not dropdown_match:
        dropdown_match = ctx.ocr(0.6, 0.3, 1.0, 0.5, match='合鸣')
    if dropdown_match:
        b = dropdown_match[0] if isinstance(dropdown_match, list) else dropdown_match
        dd_x = b.get('x',0) + b.get('width',0) / 2
        dd_y = b.get('y',0) + b.get('height',0) / 2
        results['dropdown_pos'] = f'{dd_x:.3f},{dd_y:.3f}'
    else:
        dd_x, dd_y = 0.85, 0.454
        results['dropdown_pos'] = 'fallback'

    # Click dropdown to open it
    ctx.real_click(dd_x, dd_y, after_sleep=2)
    shot('dropdown_open')

    # Check if dropdown list appeared (look for set names)
    dd_check = ctx.ocr(0.6, 0.45, 1.0, 0.95)
    dd_names = [b.get('name','') for b in (dd_check or []) if len(b.get('name','')) >= 3]
    results['dropdown_items'] = dd_names
    results['dropdown_opened'] = len(dd_names) > 0

    if not results['dropdown_opened']:
        shot('dropdown_failed')
        return results

    # Scroll down to find target set
    target = '凝夜白霜'
    found = False

    for scroll_try in range(15):
        match = ctx.ocr(0.6, 0.4, 1.0, 0.95, match=target)
        if match:
            b = match[0] if isinstance(match, list) else match
            results['found_scroll'] = scroll_try
            ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                           b.get('y',0)+b.get('height',0)/2, after_sleep=2)
            found = True
            shot('found')
            break
        # Real scroll within the dropdown (same position as SmartEnhanceTask)
        _real_scroll_at(ctx, 0.85, 0.65, -5)
        time.sleep(1)

    results['target'] = target
    results['found'] = found

    # Cleanup
    ctx.send_key('esc', after_sleep=0.5)
    for _ in range(3):
        ctx.dbl_click(0.115, 0.900, after_sleep=1)
        if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
            break
    for _ in range(3):
        ctx.send_key('esc', after_sleep=0.5)

    return results
