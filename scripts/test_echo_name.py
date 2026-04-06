"""验证声骸名字匹配: 筛选后逐个点击声骸，OCR右侧详情名字。
流程: 打开背包 → 应用筛选(听唤+Cost4+暴击伤害) → 关闭面板 → 点击每个声骸 → OCR详情名字。"""
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
    step = [0]
    def shot(label):
        step[0] += 1
        s = ctx.screenshot()
        results[f'{step[0]:02d}_{label}'] = s.get('path', '')

    if not _ensure_echo_backpack(ctx):
        return {'error': 'nav failed'}
    shot('backpack')

    # Apply filter: 听唤语义之愿 + Cost4 + 暴击伤害
    # Open filter panel
    ctx.dbl_click(0.115, 0.900, after_sleep=2)

    # Select set
    ctx.real_click(0.85, 0.454, after_sleep=2)
    match = ctx.ocr(0.6, 0.45, 1.0, 0.95, match='听唤')
    if match:
        b = match[0] if isinstance(match, list) else match
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)

    # Open overlay, select 暴击伤害 (Cost4 default)
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

    shot('filter_applied')

    # Close filter panel
    for _ in range(3):
        ctx.dbl_click(0.115, 0.900, after_sleep=1.5)
        if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
            break
    shot('panel_closed')

    # Now click each echo in the grid and read the detail name
    # Grid starts at x≈0.08 (avoid sidebar at x<0.06), y≈0.14
    echo_names = []
    GRID_START_X = 0.08
    GRID_START_Y = 0.20
    COL_STEP = 0.075
    ROW_STEP = 0.14
    COLS = 7
    ROWS = 3

    for row in range(ROWS):
        for col in range(COLS):
            ex = GRID_START_X + col * COL_STEP
            ey = GRID_START_Y + row * ROW_STEP
            if ex > 0.55:
                break

            ctx.click(ex, ey, after_sleep=0.8)

            # Echo name at top of detail panel (verified from screenshot)
            name_ocr = ctx.ocr(0.60, 0.03, 0.78, 0.07)
            names = [b.get('name', '') for b in (name_ocr or []) if len(b.get('name','')) >= 2]
            echo_name = names[0] if names else '(empty)'
            echo_names.append(f'({ex:.2f},{ey:.2f}): {echo_name}')

            if len(echo_names) <= 6:
                shot(f'echo_{len(echo_names)}')

            # Stop if we hit an empty slot (no echo at this position)
            if echo_name == '(empty)':
                break
        if echo_names and echo_names[-1].endswith('(empty)'):
            break

    results['echo_names'] = echo_names
    results['count'] = len([n for n in echo_names if not n.endswith('(empty)')])

    # Reset filter and cleanup
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    reset = ctx.ocr(0.6, 0.75, 1.0, 0.95, match='重置')
    if reset:
        b = reset[0] if isinstance(reset, list) else reset
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)
    ctx.dbl_click(0.115, 0.900, after_sleep=1)
    for _ in range(3):
        ctx.send_key('esc', after_sleep=0.5)
    shot('done')

    return results
