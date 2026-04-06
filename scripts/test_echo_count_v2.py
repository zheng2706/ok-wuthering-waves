"""测试声骸数量估算v2: OCR网格区域直接计数，不依赖详情面板。
思路: 每个声骸在grid中显示level(+0/+5/+15/+25等)，OCR grid区域统计有多少个。
"""
import time
import re


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


def _apply_filter(ctx, set_short, cost, main_stat):
    """Apply filter — verified flow."""
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
        ctx.dbl_click(0.115, 0.900, after_sleep=3)

    ctx.real_click(0.85, 0.454, after_sleep=2)
    match = ctx.ocr(0.6, 0.45, 1.0, 0.95, match=set_short)
    if match:
        b = match[0]
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)

    add = ctx.ocr(0.6, 0.4, 1.0, 0.65, match='添加')
    if add:
        b = add[0]
        ctx.real_click(b.get('x',0)+b.get('width',0)+0.02,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=3)

    if cost != 4:
        COST_TAB = {3: (0.400, 0.216), 1: (0.645, 0.216)}
        pos = COST_TAB.get(cost)
        if pos:
            ctx.click(pos[0], pos[1], after_sleep=2)

    stat = ctx.ocr(0.0, 0.1, 1.0, 0.8, match=main_stat)
    if stat:
        b = stat[0]
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)

    confirm = ctx.ocr(0.0, 0.7, 1.0, 1.0, match='确认')
    if confirm:
        b = confirm[0]
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)

    for _ in range(3):
        ctx.dbl_click(0.115, 0.900, after_sleep=1.5)
        if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
            break


def _count_grid_echoes(ctx):
    """Count echoes in grid by OCR-ing for level indicators (+N).
    Each echo shows its level like +0, +5, +10, +15, +20, +25.
    Grid area: (0.04, 0.12, 0.58, 0.90)."""
    grid_ocr = ctx.ocr(0.04, 0.12, 0.58, 0.90)
    level_pattern = re.compile(r'^\+\d+$')
    levels = []
    all_texts = []
    for b in (grid_ocr or []):
        name = b.get('name', '')
        all_texts.append(f"{name} @({b.get('x',0):.3f},{b.get('y',0):.3f})")
        if level_pattern.match(name):
            levels.append(name)
    return len(levels), levels, all_texts


def _reset_and_close(ctx):
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    reset = ctx.ocr(0.6, 0.75, 1.0, 0.95, match='重置')
    if reset:
        b = reset[0]
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1.5)
    for _ in range(3):
        ctx.dbl_click(0.115, 0.900, after_sleep=1.5)
        if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
            break
    time.sleep(1)


def execute(ctx):
    results = {}

    if not _ensure_echo_backpack(ctx):
        return {'error': 'nav failed'}

    # Test 1: 无筛选 (should be many)
    count0, levels0, texts0 = _count_grid_echoes(ctx)
    results['no_filter_count'] = count0
    results['no_filter_levels'] = levels0[:10]
    results['no_filter_all'] = texts0[:15]
    s = ctx.screenshot()
    results['no_filter_shot'] = s.get('path', '')

    # Test 2: 长路启航之星 + 4C + 暴击伤害 (few expected)
    _apply_filter(ctx, '长路', 4, '暴击伤害')
    time.sleep(1)
    count1, levels1, texts1 = _count_grid_echoes(ctx)
    results['t1_filter'] = '长路 4C 暴击伤害'
    results['t1_count'] = count1
    results['t1_levels'] = levels1[:10]
    results['t1_all'] = texts1[:15]
    s = ctx.screenshot()
    results['t1_shot'] = s.get('path', '')

    _reset_and_close(ctx)

    # Test 3: 长路启航之星 + 1C + 攻击力百分比 (many expected)
    _apply_filter(ctx, '长路', 1, '攻击力百分比')
    time.sleep(1)
    count2, levels2, texts2 = _count_grid_echoes(ctx)
    results['t2_filter'] = '长路 1C 攻击力百分比'
    results['t2_count'] = count2
    results['t2_levels'] = levels2[:10]
    results['t2_all'] = texts2[:15]
    s = ctx.screenshot()
    results['t2_shot'] = s.get('path', '')

    _reset_and_close(ctx)

    # Cleanup
    for _ in range(3):
        ctx.send_key('esc', after_sleep=0.5)

    return results
