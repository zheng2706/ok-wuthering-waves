"""测试筛选后声骸数量估算:
1. 打开背包→声骸tab
2. 应用筛选(长路启航之星 + Cost4 + 暴击伤害)
3. 逐行检查grid，估算数量
4. 重置筛选
"""
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


def _apply_filter(ctx, set_short, cost, main_stat):
    """Apply filter — exact copy of test_bug2_multiround verified flow."""
    # Open panel
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
        ctx.dbl_click(0.115, 0.900, after_sleep=3)

    # Select set
    ctx.real_click(0.85, 0.454, after_sleep=2)
    match = ctx.ocr(0.6, 0.45, 1.0, 0.95, match=set_short)
    if match:
        b = match[0] if isinstance(match, list) else match
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)

    # Open overlay
    add = ctx.ocr(0.6, 0.4, 1.0, 0.65, match='添加')
    if add:
        b = add[0] if isinstance(add, list) else add
        ctx.real_click(b.get('x',0)+b.get('width',0)+0.02,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=3)

    # Switch Cost tab if needed
    if cost != 4:
        COST_TAB = {3: (0.400, 0.216), 1: (0.645, 0.216)}
        pos = COST_TAB.get(cost)
        if pos:
            ctx.click(pos[0], pos[1], after_sleep=2)

    # Select stat
    stat = ctx.ocr(0.0, 0.1, 1.0, 0.8, match=main_stat)
    if stat:
        b = stat[0] if isinstance(stat, list) else stat
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)

    # Confirm
    confirm = ctx.ocr(0.0, 0.7, 1.0, 1.0, match='确认')
    if confirm:
        b = confirm[0] if isinstance(confirm, list) else confirm
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)

    # Close panel
    for _ in range(3):
        ctx.dbl_click(0.115, 0.900, after_sleep=1.5)
        if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
            break


def _count_echoes_in_grid(ctx):
    """Count echoes by checking grid positions row by row.
    Grid: x starts 0.13, col_step 0.075, ~6 cols visible
          y starts 0.22, row_step 0.14
    Click each row's first col, read name. Stop when no name found."""
    count = 0
    last_names = []

    for row in range(6):  # max 6 rows
        y = 0.22 + row * 0.14
        if y > 0.85:
            break

        # Check first col in this row
        ctx.click(0.13, y, after_sleep=0.6)
        name = _read_echo_name(ctx)

        if not name:
            # No echo at row start — this row is empty, we're done
            break

        # Row has echoes, count columns
        row_count = 1
        for col in range(1, 7):
            x = 0.13 + col * 0.075
            if x > 0.55:
                break
            ctx.click(x, y, after_sleep=0.5)
            col_name = _read_echo_name(ctx)
            if not col_name:
                break
            row_count += 1

        count += row_count
        last_names.append(f'row{row}: {row_count} echoes (first: {name})')

    return count, last_names


def execute(ctx):
    results = {}
    step = [0]
    def shot(label):
        step[0] += 1
        s = ctx.screenshot()
        results[f'{step[0]:02d}_{label}'] = s.get('path', '')

    if not _ensure_echo_backpack(ctx):
        return {'error': 'nav failed'}

    # Test 1: Filter with many results (Cost1 攻击力百分比 — should have lots)
    _apply_filter(ctx, '长路', 1, '攻击力百分比')
    time.sleep(1)
    shot('filtered_cost1_atk')

    count1, details1 = _count_echoes_in_grid(ctx)
    results['test1_filter'] = '长路启航之星 1C 攻击力百分比'
    results['test1_count'] = count1
    results['test1_details'] = details1
    results['test1_strict'] = count1 > 20
    shot('count_cost1')

    # Reset
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    reset = ctx.ocr(0.6, 0.75, 1.0, 0.95, match='重置')
    if reset:
        b = reset[0] if isinstance(reset, list) else reset
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1.5)
    for _ in range(3):
        ctx.dbl_click(0.115, 0.900, after_sleep=1.5)
        if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
            break
    time.sleep(1)

    # Test 2: Filter with few results (Cost4 暴击伤害 — should be fewer)
    _apply_filter(ctx, '长路', 4, '暴击伤害')
    time.sleep(1)
    shot('filtered_cost4_crit')

    count2, details2 = _count_echoes_in_grid(ctx)
    results['test2_filter'] = '长路启航之星 4C 暴击伤害'
    results['test2_count'] = count2
    results['test2_details'] = details2
    results['test2_strict'] = count2 > 20
    shot('count_cost4')

    # Cleanup
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    reset = ctx.ocr(0.6, 0.75, 1.0, 0.95, match='重置')
    if reset:
        b = reset[0] if isinstance(reset, list) else reset
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)
    for _ in range(3):
        ctx.dbl_click(0.115, 0.900, after_sleep=1.5)
        if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
            break
    for _ in range(3):
        ctx.send_key('esc', after_sleep=0.5)

    return results
