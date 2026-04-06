"""Bug 1 验证: 主属性面板全屏overlay OCR区域扩大后能否找到 Cost4 和暴击伤害。
前提: 游戏已在声骸背包页 (按B→切到声骸tab)。
流程: 打开筛选面板 → 选套装 → 打开主属性面板 → OCR全屏找Cost4和暴击伤害 → 截图"""
import time


def execute(ctx):
    results = {}
    def shot(label):
        s = ctx.screenshot()
        results[label] = s.get('path', '')

    # Step 0: Ensure on echo backpack page
    for _ in range(5):
        ctx.send_key('esc', after_sleep=0.7)
    time.sleep(1)
    ctx.send_key('b', after_sleep=3)
    # Dismiss popup only if present
    popup = ctx.ocr(0.2, 0.3, 0.8, 0.8, match='弃置')
    if popup:
        ctx.send_key('esc', after_sleep=1)
    ctx.click(0.02, 0.30, after_sleep=2)
    shot('00_echo_page')

    # Step 1: Open filter panel (dbl_click funnel icon)
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    panel = ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选')
    results['panel_opened'] = bool(panel)
    shot('01_filter_panel')

    if not panel:
        results['error'] = '筛选面板未打开'
        return results

    # Step 2: Open dropdown and select a set (听唤语义之愿)
    ctx.real_click(0.85, 0.454, after_sleep=2)
    match = ctx.ocr(0.6, 0.45, 1.0, 0.95, match='听唤')
    if match:
        b = match[0] if isinstance(match, list) else match
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)
        results['set_selected'] = True
    else:
        results['set_selected'] = False
    shot('02_set_selected')

    # Step 3: Click 添加主属性筛选 + button to open overlay
    add = ctx.ocr(0.6, 0.4, 1.0, 0.65, match='添加')
    if add:
        b = add[0] if isinstance(add, list) else add
        ctx.real_click(b.get('x',0)+b.get('width',0)+0.02,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)
    else:
        ctx.real_click(0.96, 0.592, after_sleep=2)
    shot('03_overlay_opened')

    # Step 4: BUG 1 TEST - OCR with OLD narrow range vs NEW full range
    # Old range (was buggy):
    old_cost = ctx.ocr(0.05, 0.1, 0.95, 0.3, match='Cost4')
    results['old_range_cost4'] = bool(old_cost)

    # New range (fix):
    new_cost = ctx.ocr(0.0, 0.0, 1.0, 0.5, match='Cost4')
    results['new_range_cost4'] = bool(new_cost)

    # Full screen OCR to see everything detected
    full_ocr = ctx.ocr(0.0, 0.0, 1.0, 1.0)
    results['full_ocr_texts'] = [b.get('name','') for b in (full_ocr or [])]
    shot('04_ocr_full_screen')

    # Step 5: Click Cost4 tab (should be found with new range)
    if new_cost:
        b = new_cost[0] if isinstance(new_cost, list) else new_cost
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1.5)
        results['cost4_clicked'] = True
    else:
        results['cost4_clicked'] = False
    shot('05_cost4_selected')

    # Step 6: Find 暴击伤害 with old vs new range
    old_stat = ctx.ocr(0.05, 0.25, 0.95, 0.65, match='暴击伤害')
    results['old_range_crit_dmg'] = bool(old_stat)

    new_stat = ctx.ocr(0.0, 0.0, 1.0, 0.8, match='暴击伤害')
    results['new_range_crit_dmg'] = bool(new_stat)
    shot('06_stat_search')

    # Step 7: Find 确认 with old vs new range
    old_confirm = ctx.ocr(0.5, 0.7, 0.95, 0.95, match='确认')
    results['old_range_confirm'] = bool(old_confirm)

    new_confirm = ctx.ocr(0.0, 0.7, 1.0, 1.0, match='确认')
    results['new_range_confirm'] = bool(new_confirm)

    # Step 8: Clean up - press ESC to close overlay, then close filter panel
    ctx.send_key('esc', after_sleep=1)
    ctx.dbl_click(0.115, 0.900, after_sleep=1)
    shot('07_cleanup')

    # Summary
    results['bug1_fixed'] = (results.get('new_range_cost4') and
                             results.get('new_range_crit_dmg') and
                             results.get('new_range_confirm'))

    return results
