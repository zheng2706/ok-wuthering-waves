"""Test reading character echo sets. Navigate to char page and OCR the 合鸣效果 section."""
import time


def execute(ctx):
    results = {}

    # Navigate: ESC → menu → 共鸣者
    for _ in range(5):
        ctx.send_key('esc', after_sleep=0.7)
    time.sleep(1)
    ctx.send_key('esc', after_sleep=2)

    # Click 共鸣者 in ESC menu
    r = ctx.ocr(0.3, 0.3, 0.7, 0.7, match='共鸣者')
    if r:
        b = r[0] if isinstance(r, list) else r
        ctx.click(b.get('x',0)+b.get('width',0)/2,
                  b.get('y',0)+b.get('height',0)/2, after_sleep=5)
    else:
        results['error'] = '共鸣者 not found'
        return results

    # Switch to echo tab (sidebar y=0.40)
    ctx.click(0.015, 0.40, after_sleep=2)

    # Screenshot
    s = ctx.screenshot()
    results['echo_page'] = s.get('path', '')

    # OCR the 合鸣效果 section (wider region)
    boxes = ctx.ocr(0.05, 0.45, 0.50, 0.80)
    results['ocr_boxes'] = []
    if boxes:
        for b in boxes:
            entry = f"[{b.get('name','')}] y={b.get('y',0):.3f} x={b.get('x',0):.3f}"
            results['ocr_boxes'].append(entry)

    # Also take a screenshot of just this area
    s2 = ctx.screenshot()
    results['final'] = s2.get('path', '')

    # ESC back
    ctx.send_key('esc', after_sleep=1)
    ctx.send_key('esc', after_sleep=1)

    return results
