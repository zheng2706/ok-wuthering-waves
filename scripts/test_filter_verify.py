"""Verify filter works end-to-end with screenshots at every step.
Use 听唤语义之愿 (118 echoes) + Cost4 + 暴击伤害 to guarantee results."""
import time


def execute(ctx):
    results = {}
    def shot(label):
        s = ctx.screenshot()
        results[label] = s.get('path', '')

    # Nav to echo backpack
    for _ in range(5):
        ctx.send_key('esc', after_sleep=0.7)
    time.sleep(1)
    ctx.send_key('b', after_sleep=3)
    ctx.send_key('esc', after_sleep=1)
    ctx.click(0.02, 0.30, after_sleep=2)
    shot('00_echo_page')

    # Step 1: Open filter
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    shot('01_panel_open')

    # Step 2: Open dropdown
    ctx.real_click(0.85, 0.454, after_sleep=2)
    shot('02_dropdown')

    # Step 3: Select 听唤语义之愿 (should be visible without scroll)
    match = ctx.ocr(0.6, 0.45, 1.0, 0.95, match='听唤')
    if match:
        b = match[0] if isinstance(match, list) else match
        cx = b.get('x',0) + b.get('width',0)/2
        cy = b.get('y',0) + b.get('height',0)/2
        ctx.real_click(cx, cy, after_sleep=2)
        results['set_selected'] = True
    else:
        results['set_selected'] = False
    shot('03_set_selected')

    # Step 4: Verify set shown in panel
    panel_check = ctx.ocr(0.6, 0.35, 1.0, 0.50, match='听唤')
    results['set_confirmed'] = bool(panel_check)
    shot('04_set_confirmed')

    # Step 5: Click 添加主属性筛选 +
    add = ctx.ocr(0.6, 0.5, 1.0, 0.65, match='添加')
    if add:
        b = add[0] if isinstance(add, list) else add
        ctx.real_click(b.get('x',0)+b.get('width',0)+0.02,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)
    shot('05_main_stat_panel')

    # Step 6: Cost4 should be default, select 暴击伤害
    stat = ctx.ocr(0, 0.2, 1.0, 0.7, match='暴击伤害')
    if stat:
        b = stat[0] if isinstance(stat, list) else stat
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)
    shot('06_stat_selected')

    # Step 7: Confirm
    confirm = ctx.ocr(0.3, 0.7, 1.0, 1.0, match='确认')
    if confirm:
        b = confirm[0] if isinstance(confirm, list) else confirm
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)
    shot('07_filter_result')

    # Step 8: Read filter count
    count_ocr = ctx.ocr(0.6, 0.8, 1.0, 0.92)
    for b in (count_ocr or []):
        n = b.get('name', '')
        if '筛选' in n or n.isdigit():
            results['filter_count_text'] = n

    # Step 9: Reset and close
    reset = ctx.ocr(0.6, 0.8, 1.0, 0.92, match='重置')
    if reset:
        b = reset[0] if isinstance(reset, list) else reset
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)
    ctx.dbl_click(0.115, 0.900, after_sleep=1)
    shot('08_done')

    return results
