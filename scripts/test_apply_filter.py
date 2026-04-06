"""
Test the complete filter flow end-to-end:
1. Navigate to echo backpack
2. Open filter panel
3. Select set (听唤语义之愿 - visible in dropdown)
4. Open main stat panel, select Cost4 + 暴击伤害
5. Confirm
6. Verify filter applied
7. Reset and close
"""
import re
import time


def execute(ctx):
    results = {}
    def log(msg):
        results.setdefault('_log', []).append(str(msg))
    def shot(label):
        s = ctx.screenshot()
        results[label] = s.get('path', '')

    # === Navigate to echo backpack ===
    log("Nav: ESC to main")
    for _ in range(6):
        ctx.send_key('esc', after_sleep=0.7)
    time.sleep(1)
    log("Nav: B to open backpack")
    ctx.send_key('b', after_sleep=3)
    ctx.send_key('esc', after_sleep=1)  # dismiss popup
    log("Nav: Switch to echo tab")
    ctx.click(0.02, 0.30, after_sleep=2)
    h = ctx.ocr(0, 0, 0.25, 0.08)
    if not any('声骸' in b.get('name','') for b in (h or [])):
        log("FAIL: not on echo page")
        shot('fail')
        return results
    log("OK: on echo page")

    # === Step 1: Open filter panel ===
    log("Step 1: Open filter panel (dbl_click funnel)")
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    if not ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选'):
        ctx.dbl_click(0.115, 0.900, after_sleep=2)
    if not ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选'):
        log("FAIL: cannot open filter panel")
        return results
    log("OK: filter panel open")
    shot('s1_panel')

    # === Step 2: Open dropdown + select set ===
    log("Step 2: Open dropdown (real_click)")
    ctx.real_click(0.85, 0.454, after_sleep=2)

    # Select 听唤语义之愿 (first visible set)
    target_set = '听唤语义之愿'
    log(f"Step 2b: Select set [{target_set}]")
    match = ctx.ocr(0.6, 0.45, 1.0, 0.95, match='听唤')
    if match:
        b = match[0] if isinstance(match, list) else match
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)
        log("OK: set selected")
    else:
        log("FAIL: set not found in dropdown")
        shot('s2_fail')
        return results
    shot('s2_set')

    # Verify: check if filter shows the set name
    check = ctx.ocr(0.6, 0.4, 1.0, 0.5, match='听唤')
    log(f"Set verification: {'OK' if check else 'FAIL'}")

    # === Step 3: Open main stat panel ===
    log("Step 3: Open main stat panel")
    add = ctx.ocr(0.6, 0.5, 1.0, 0.65, match='添加')
    if add:
        b = add[0] if isinstance(add, list) else add
        plus_x = b.get('x',0) + b.get('width',0) + 0.02
        plus_y = b.get('y',0) + b.get('height',0) / 2
        ctx.real_click(plus_x, plus_y, after_sleep=2)
    else:
        ctx.real_click(0.96, 0.592, after_sleep=2)
    shot('s3_mainstat')

    # === Step 4: Select Cost4 ===
    log("Step 4: Select Cost4")
    c4 = ctx.ocr(0, 0, 1.0, 0.5, match='Cost4')
    if not c4:
        c4 = ctx.ocr(0, 0, 1.0, 0.5, match='cost4')
    if not c4:
        c4 = ctx.ocr(0, 0, 1.0, 0.5, match='Cost 4')
    if c4:
        b = c4[0] if isinstance(c4, list) else c4
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1.5)
        log("OK: Cost4 selected")
    else:
        # Try position-based: Cost4 is first tab, ~left side
        log("Cost4 not found by OCR, try position (0.15, 0.18)")
        ctx.real_click(0.15, 0.18, after_sleep=1.5)
    shot('s4_cost')

    # === Step 5: Select 暴击伤害 ===
    log("Step 5: Select main stat")
    stat = ctx.ocr(0, 0.2, 1.0, 0.7, match='暴击伤害')
    if stat:
        b = stat[0] if isinstance(stat, list) else stat
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1.5)
        log("OK: 暴击伤害 selected")
    else:
        log("暴击伤害 not found")
    shot('s5_stat')

    # === Step 6: Confirm ===
    log("Step 6: Confirm")
    confirm = ctx.ocr(0.3, 0.7, 1.0, 1.0, match='确认')
    if confirm:
        b = confirm[0] if isinstance(confirm, list) else confirm
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)
        log("OK: confirmed")
    else:
        log("confirm button not found")
    shot('s6_confirm')

    # === Step 7: Verify filter applied ===
    log("Step 7: Verify filter")
    filtered = ctx.ocr(0.6, 0.8, 1.0, 0.92, match='已筛选')
    if filtered:
        b = filtered[0] if isinstance(filtered, list) else filtered
        log(f"FILTER APPLIED: {b.get('name','')}")
        results['filter_applied'] = True
    else:
        # Check if echo count changed
        h = ctx.ocr(0, 0, 0.25, 0.08)
        header = ''.join(b.get('name','') for b in (h or []))
        log(f"Header after filter: {header}")
        results['filter_applied'] = False
    shot('s7_result')

    # === Step 8: Reset ===
    log("Step 8: Reset")
    reset = ctx.ocr(0.6, 0.8, 1.0, 0.92, match='重置')
    if reset:
        b = reset[0] if isinstance(reset, list) else reset
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1.5)
        log("OK: reset")

    # Close panel
    ctx.dbl_click(0.115, 0.900, after_sleep=1)
    shot('s8_done')

    log("=== COMPLETE ===")
    return results
