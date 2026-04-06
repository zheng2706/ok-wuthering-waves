"""声骸名字匹配验证v2: 用精确坐标读名字，点击网格切换声骸。
名字OCR区域: (0.65, 0.10, 0.85, 0.16) — 从OCR dump验证
网格中心Y≈0.22, 间距≈0.075"""
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


def _read_echo_name(ctx):
    """Read currently selected echo's name from detail panel."""
    name_ocr = ctx.ocr(0.65, 0.10, 0.85, 0.16)
    for b in (name_ocr or []):
        name = b.get('name', '')
        if len(name) >= 2 and not name.isdigit():
            return name
    return None


def execute(ctx):
    results = {}
    step = [0]
    def shot(label):
        step[0] += 1
        s = ctx.screenshot()
        results[f'{step[0]:02d}_{label}'] = s.get('path', '')

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
    for _ in range(3):
        ctx.dbl_click(0.115, 0.900, after_sleep=1.5)
        if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
            break
    shot('filtered')

    # Read first echo name (already selected after filter)
    name1 = _read_echo_name(ctx)
    results['echo1_name'] = name1
    shot('echo1')

    # Click second echo (grid position from OCR dump: +0 was at x=0.254)
    # Echo centers: first ≈ (0.13, 0.22), second ≈ (0.21, 0.22)
    ctx.click(0.21, 0.22, after_sleep=1)
    name2 = _read_echo_name(ctx)
    results['echo2_name'] = name2
    shot('echo2')

    # Try clicking back to first
    ctx.click(0.13, 0.22, after_sleep=1)
    name1b = _read_echo_name(ctx)
    results['echo1b_name'] = name1b
    shot('echo1b')

    # Verify we're still on echo page
    header = ctx.ocr(0, 0, 0.15, 0.06)
    results['still_echo_page'] = any('声骸' in b.get('name','') for b in (header or []))

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
