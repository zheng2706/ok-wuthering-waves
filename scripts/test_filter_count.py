"""找筛选结果数量文字: 应用筛选后，OCR dump整个底部区域找数字。"""
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

    if not _ensure_echo_backpack(ctx):
        return {'error': 'nav failed'}

    # Open filter panel
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
        ctx.dbl_click(0.115, 0.900, after_sleep=3)

    # Select set
    ctx.real_click(0.85, 0.454, after_sleep=2)
    match = ctx.ocr(0.6, 0.45, 1.0, 0.95, match='长路')
    if match:
        b = match[0]
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)

    # Open overlay + select stat
    add = ctx.ocr(0.6, 0.4, 1.0, 0.65, match='添加')
    if add:
        b = add[0]
        ctx.real_click(b.get('x',0)+b.get('width',0)+0.02,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=3)
    stat = ctx.ocr(0.0, 0.1, 1.0, 0.8, match='暴击伤害')
    if stat:
        b = stat[0]
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)
    confirm = ctx.ocr(0.0, 0.7, 1.0, 1.0, match='确认')
    if confirm:
        b = confirm[0]
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)

    # 筛选面板还开着，OCR dump整个右侧面板找数量文字
    results['panel_ocr'] = []
    for region_name, (x1, y1, x2, y2) in [
        ('right_panel', (0.55, 0.0, 1.0, 1.0)),
        ('bottom_area', (0.0, 0.80, 1.0, 1.0)),
        ('filter_area', (0.55, 0.80, 1.0, 1.0)),
        ('left_bottom', (0.0, 0.85, 0.55, 1.0)),
    ]:
        ocr_result = ctx.ocr(x1, y1, x2, y2)
        texts = [f"{b.get('name','')}: ({b.get('x',0):.3f},{b.get('y',0):.3f})"
                 for b in (ocr_result or [])]
        results[f'ocr_{region_name}'] = texts

    s = ctx.screenshot()
    results['shot_panel_open'] = s.get('path', '')

    # Close panel, check if count text appears below
    for _ in range(3):
        ctx.dbl_click(0.115, 0.900, after_sleep=1.5)
        if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
            break
    time.sleep(1)

    # OCR bottom area after panel closed
    for region_name, (x1, y1, x2, y2) in [
        ('bottom_closed', (0.0, 0.80, 0.60, 1.0)),
        ('left_header', (0.0, 0.0, 0.55, 0.15)),
    ]:
        ocr_result = ctx.ocr(x1, y1, x2, y2)
        texts = [f"{b.get('name','')}: ({b.get('x',0):.3f},{b.get('y',0):.3f})"
                 for b in (ocr_result or [])]
        results[f'ocr_{region_name}'] = texts

    s = ctx.screenshot()
    results['shot_panel_closed'] = s.get('path', '')

    # Cleanup
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    reset = ctx.ocr(0.6, 0.75, 1.0, 0.95, match='重置')
    if reset:
        b = reset[0]
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)
    for _ in range(3):
        ctx.dbl_click(0.115, 0.900, after_sleep=1.5)
        if not ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'):
            break
    for _ in range(3):
        ctx.send_key('esc', after_sleep=0.5)

    return results
