"""Test: which click method works for Cost tabs in the main stat overlay.
Tests PostMessage click vs real_click vs real_click without bring_to_front."""
import ctypes
import time
import win32gui


def _ensure_echo_backpack(ctx):
    """Navigate to echo backpack, handling popups."""
    menu_kw = ['终端', '活动', '商城', '共鸣者']
    backpack_kw = ['武器', '声骸', '补给', '资源']

    for attempt in range(10):
        # Check for popup/dialog FIRST (before checking headers)
        center = ctx.ocr(0.1, 0.2, 0.9, 0.8)
        center_texts = ' '.join(b.get('name', '') for b in (center or []))
        if any(kw in center_texts for kw in ['弃置', '提示', '取消']):
            ctx.send_key('esc', after_sleep=1.5)
            continue

        top = ctx.ocr(0, 0, 0.3, 0.12)
        texts = ' '.join(b.get('name', '') for b in (top or []))

        if any(kw in texts for kw in backpack_kw):
            ctx.click(0.02, 0.30, after_sleep=2)
            return True
        if any(kw in texts for kw in menu_kw):
            ctx.send_key('esc', after_sleep=1)
            continue
        ctx.send_key('b', after_sleep=3)
    return False


def execute(ctx):
    results = {}
    def shot(label):
        s = ctx.screenshot()
        results[label] = s.get('path', '')

    # Nav to echo backpack
    if not _ensure_echo_backpack(ctx):
        return {'error': 'nav failed'}
    shot('00_backpack')

    # Open filter panel
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    if not ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选'):
        ctx.dbl_click(0.115, 0.900, after_sleep=2)
    shot('01_filter_panel')

    # Select a set
    ctx.real_click(0.85, 0.454, after_sleep=2)
    match = ctx.ocr(0.6, 0.45, 1.0, 0.95, match='听唤')
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
    shot('02_overlay')

    overlay_open = bool(ctx.ocr(0.0, 0.0, 1.0, 0.3, match='Cost'))
    results['overlay_open'] = overlay_open
    if not overlay_open:
        return results

    # ========== TEST 1: PostMessage click on Cost3 ==========
    cost3 = ctx.ocr(0.0, 0.0, 1.0, 0.3, match='Cost3')
    if cost3:
        b = cost3[0] if isinstance(cost3, list) else cost3
        cx = b.get('x',0) + b.get('width',0)/2
        cy = b.get('y',0) + b.get('height',0)/2
        ctx.click(cx, cy, after_sleep=2)  # PostMessage click
        still_open = bool(ctx.ocr(0.0, 0.0, 1.0, 0.3, match='Cost'))
        results['T1_postmsg'] = still_open
        shot('03_T1_postmsg')

        # Check if Cost3 stats are now showing (different from Cost4)
        if still_open:
            # Cost3 should show elemental DMG stats
            c3_stats = ctx.ocr(0.0, 0.1, 1.0, 0.8)
            results['T1_visible_stats'] = [b2.get('name','') for b2 in (c3_stats or [])
                                            if '伤害' in b2.get('name','') or 'Cost' in b2.get('name','')]

    # If overlay closed, reopen
    if not bool(ctx.ocr(0.0, 0.0, 1.0, 0.3, match='Cost')):
        ctx.send_key('esc', after_sleep=1)
        add = ctx.ocr(0.6, 0.4, 1.0, 0.65, match='添加')
        if add:
            b = add[0] if isinstance(add, list) else add
            ctx.real_click(b.get('x',0)+b.get('width',0)+0.02,
                           b.get('y',0)+b.get('height',0)/2, after_sleep=3)

    # ========== TEST 2: real_click on Cost1 ==========
    if bool(ctx.ocr(0.0, 0.0, 1.0, 0.3, match='Cost')):
        cost1 = ctx.ocr(0.0, 0.0, 1.0, 0.3, match='Cost1')
        if cost1:
            b = cost1[0] if isinstance(cost1, list) else cost1
            cx = b.get('x',0) + b.get('width',0)/2
            cy = b.get('y',0) + b.get('height',0)/2
            ctx.real_click(cx, cy, after_sleep=2)
            still_open = bool(ctx.ocr(0.0, 0.0, 1.0, 0.3, match='Cost'))
            results['T2_real_click'] = still_open
            shot('04_T2_real_click')

    # If overlay closed, reopen
    if not bool(ctx.ocr(0.0, 0.0, 1.0, 0.3, match='Cost')):
        ctx.send_key('esc', after_sleep=1)
        add = ctx.ocr(0.6, 0.4, 1.0, 0.65, match='添加')
        if add:
            b = add[0] if isinstance(add, list) else add
            ctx.real_click(b.get('x',0)+b.get('width',0)+0.02,
                           b.get('y',0)+b.get('height',0)/2, after_sleep=3)

    # ========== TEST 3: Click at fixed position for Cost3 tab ==========
    if bool(ctx.ocr(0.0, 0.0, 1.0, 0.3, match='Cost')):
        # Cost3 tab is roughly in the middle third of the tab bar
        ctx.real_click(0.38, 0.165, after_sleep=2)
        still_open = bool(ctx.ocr(0.0, 0.0, 1.0, 0.3, match='Cost'))
        results['T3_fixed_pos'] = still_open
        shot('05_T3_fixed_pos')

    # Cleanup
    for _ in range(5):
        ctx.send_key('esc', after_sleep=0.7)
    shot('99_cleanup')

    return results
