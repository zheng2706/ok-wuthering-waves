"""简化版声骸名字读取: 筛选后直接读右侧详情，不点击网格。
先做OCR dump定位名字精确坐标。"""
import time


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


def execute(ctx):
    results = {}
    def shot(label):
        s = ctx.screenshot()
        results[label] = s.get('path', '')

    if not _ensure_echo_backpack(ctx):
        return {'error': 'nav failed'}

    # Apply filter: 听唤 + Cost4 + 暴击伤害
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    ctx.real_click(0.85, 0.454, after_sleep=2)
    match = ctx.ocr(0.6, 0.45, 1.0, 0.95, match='听唤')
    if match:
        b = match[0] if isinstance(match, list) else match
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)

    add = ctx.ocr(0.6, 0.4, 1.0, 0.65, match='添加')
    if add:
        b = add[0] if isinstance(add, list) else add
        ctx.real_click(b.get('x',0)+b.get('width',0)+0.02,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=3)

    stat = ctx.ocr(0.0, 0.1, 1.0, 0.8, match='暴击伤害')
    if stat:
        b = stat[0] if isinstance(stat, list) else stat
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)

    confirm = ctx.ocr(0.0, 0.7, 1.0, 1.0, match='确认')
    if confirm:
        b = confirm[0] if isinstance(confirm, list) else confirm
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)

    # Close filter panel
    for _ in range(3):
        ctx.dbl_click(0.115, 0.900, after_sleep=1.5)
        if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
            break

    shot('filtered')

    # OCR dump the right detail panel to find echo name position
    detail_ocr = ctx.ocr(0.58, 0.0, 1.0, 0.15)
    results['detail_top'] = [
        f"{b.get('name','')}: x={b.get('x',0):.3f} y={b.get('y',0):.3f} w={b.get('width',0):.3f} h={b.get('height',0):.3f}"
        for b in (detail_ocr or [])
    ]

    # Also dump the echo grid area to find echo positions
    grid_ocr = ctx.ocr(0.04, 0.12, 0.58, 0.50)
    results['grid_items'] = [
        f"{b.get('name','')}: x={b.get('x',0):.3f} y={b.get('y',0):.3f}"
        for b in (grid_ocr or []) if len(b.get('name','')) >= 1
    ]

    # Cleanup
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    reset = ctx.ocr(0.6, 0.75, 1.0, 0.95, match='重置')
    if reset:
        b = reset[0] if isinstance(reset, list) else reset
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)
    ctx.dbl_click(0.115, 0.900, after_sleep=1)
    for _ in range(3):
        ctx.send_key('esc', after_sleep=0.5)

    return results
