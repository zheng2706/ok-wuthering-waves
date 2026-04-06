"""Find exact Cost tab positions by trying clicks and checking which tab is active.
Must be on the overlay page already (run after opening overlay manually or via script)."""
import time


def _ensure_overlay(ctx):
    """Navigate to backpack, open filter, open overlay."""
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

    # Open filter panel
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    # Open overlay
    add = ctx.ocr(0.6, 0.4, 1.0, 0.65, match='添加')
    if add:
        b = add[0] if isinstance(add, list) else add
        ctx.real_click(b.get('x',0)+b.get('width',0)+0.02,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=3)


def execute(ctx):
    results = {}
    def shot(label):
        s = ctx.screenshot()
        results[label] = s.get('path', '')

    _ensure_overlay(ctx)
    shot('00_overlay')

    # First, OCR the tab bar area to find exact positions
    tab_ocr = ctx.ocr(0.0, 0.08, 0.75, 0.22)
    for b in (tab_ocr or []):
        n = b.get('name', '')
        if 'Cost' in n or 'cost' in n:
            results[f'ocr_{n}'] = f"x={b.get('x',0):.4f} y={b.get('y',0):.4f} w={b.get('width',0):.4f} h={b.get('height',0):.4f}"

    # Try clicking Cost3 at several Y positions with x=0.35
    test_positions = [
        ('x035_y012', 0.35, 0.12),
        ('x035_y013', 0.35, 0.13),
        ('x035_y014', 0.35, 0.14),
        ('x035_y015', 0.35, 0.15),
        ('x035_y016', 0.35, 0.16),
    ]

    for label, x, y in test_positions:
        # First reset to Cost4 by clicking at known Cost4 position
        ctx.real_click(0.15, 0.14, after_sleep=1)
        # Now try clicking Cost3
        ctx.real_click(x, y, after_sleep=1.5)
        # Check if Cost3 stats are showing (elemental damage = Cost3 indicator)
        check = ctx.ocr(0.0, 0.1, 1.0, 0.8, match='冷凝')
        results[label] = bool(check)
        shot(label)

    # Cleanup
    ctx.send_key('esc', after_sleep=1)
    ctx.send_key('esc', after_sleep=1)
    ctx.dbl_click(0.115, 0.900, after_sleep=1)
    for _ in range(3):
        ctx.send_key('esc', after_sleep=0.5)

    return results
