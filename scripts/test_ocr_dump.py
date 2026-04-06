"""Dump all OCR boxes from the overlay to find exact Cost tab coordinates."""
import time


def execute(ctx):
    results = {}

    # Navigate to overlay
    menu_kw = ['终端', '活动', '商城', '共鸣者']
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
            break
        if any(kw in texts for kw in menu_kw):
            ctx.send_key('esc', after_sleep=1)
            continue
        ctx.send_key('b', after_sleep=3)

    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    add = ctx.ocr(0.6, 0.4, 1.0, 0.65, match='添加')
    if add:
        b = add[0] if isinstance(add, list) else add
        ctx.real_click(b.get('x',0)+b.get('width',0)+0.02,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=3)

    s = ctx.screenshot()
    results['screenshot'] = s.get('path', '')

    # Full screen OCR dump
    all_boxes = ctx.ocr(0.0, 0.0, 1.0, 1.0)
    cost_boxes = []
    for b in (all_boxes or []):
        name = b.get('name', '')
        entry = f"{name}: x={b.get('x',0):.4f} y={b.get('y',0):.4f} w={b.get('width',0):.4f} h={b.get('height',0):.4f}"
        if 'Cost' in name or 'cost' in name:
            cost_boxes.append(entry)

    results['cost_boxes'] = cost_boxes
    results['all_count'] = len(all_boxes or [])

    # Also narrow region OCR for comparison
    narrow_boxes = ctx.ocr(0.05, 0.10, 0.70, 0.20)
    results['narrow_boxes'] = [
        f"{b.get('name','')}: x={b.get('x',0):.4f} y={b.get('y',0):.4f} w={b.get('width',0):.4f} h={b.get('height',0):.4f}"
        for b in (narrow_boxes or [])
    ]

    # Cleanup
    ctx.send_key('esc', after_sleep=1)
    ctx.dbl_click(0.115, 0.900, after_sleep=1)
    for _ in range(3):
        ctx.send_key('esc', after_sleep=0.5)

    return results
