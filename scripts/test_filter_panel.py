"""
Phase 2: Test all filter panel operations sequentially.
1. Navigate to echo backpack
2. Double-click funnel icon to open filter panel
3. Map panel layout with OCR
4. Click 合鸣 dropdown → select a set
5. Click 添加主属性筛选 → select cost + main stat
6. Verify filter applied
7. Click 重置 to reset
"""
import time


def execute(ctx):
    results = {}
    step = 0

    def log(msg):
        nonlocal step
        step += 1
        print(f"[{step}] {msg}")

    def shot(label):
        s = ctx.screenshot()
        path = s.get('path', '')
        results[f'{label}_screenshot'] = path
        log(f"Screenshot [{label}]: {path}")
        return path

    def dbl_click(x, y, after=1.5):
        """Double-click (required for some UI elements)."""
        ctx.click(x, y, after_sleep=0.1)
        ctx.click(x, y, after_sleep=after)

    def ocr_dump(label, x, y, to_x, to_y):
        boxes = ctx.ocr(x, y, to_x, to_y)
        if boxes:
            for b in boxes:
                print(f"  [{b.get('name','')}] x={b.get('x',0):.3f} y={b.get('y',0):.3f} w={b.get('width',0):.3f} h={b.get('height',0):.3f}")
        return boxes

    # ===== Step 1: Navigate to echo backpack =====
    log("Navigate to echo backpack...")
    # ESC to main world
    for _ in range(6):
        ctx.send_key('esc', after_sleep=0.7)
    time.sleep(0.5)
    # B to open backpack
    ctx.send_key('b', after_sleep=2.5)
    ctx.send_key('esc', after_sleep=1)  # Dismiss popup if any
    # Switch to echo tab
    ctx.click(0.02, 0.30, after_sleep=2)
    # Verify
    h = ctx.ocr(0, 0, 0.25, 0.08)
    header = ''.join(b.get('name', '') for b in (h or []))
    log(f"Header: {header}")
    if '声骸' not in header:
        return {'error': f'Not on echo page: {header}'}

    # ===== Step 2: Open filter panel (DOUBLE-CLICK) =====
    log("Opening filter panel with double-click at (0.115, 0.900)...")
    dbl_click(0.115, 0.900, after=2)

    # Verify filter panel opened
    fcheck = ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选')
    if not fcheck:
        log("Filter not detected, retry double-click...")
        dbl_click(0.115, 0.900, after=2)
        fcheck = ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选')

    if not fcheck:
        log("FAILED to open filter panel")
        shot('filter_fail')
        return {'error': 'filter panel not opened'}

    log("Filter panel OPENED!")
    shot('01_filter_opened')

    # ===== Step 3: Map filter panel layout =====
    log("Mapping filter panel...")
    ocr_dump('panel_full', 0.6, 0.02, 1.0, 0.95)

    # ===== Step 4: Click 合鸣 dropdown =====
    log("Clicking 合鸣 dropdown...")
    hemming = ctx.ocr(0.6, 0.3, 1.0, 0.5, match='合鸣')
    if hemming:
        b = hemming[0] if isinstance(hemming, list) else hemming
        hx = b.get('x', 0) + b.get('width', 0) / 2
        hy = b.get('y', 0) + b.get('height', 0) / 2
        log(f"Found 合鸣 at ({hx:.3f}, {hy:.3f}), clicking...")
        dbl_click(hx, hy, after=1.5)
    else:
        log("合鸣 not found by OCR, trying position...")
        dbl_click(0.85, 0.42, after=1.5)

    shot('02_hemming_clicked')

    # Map dropdown contents
    log("Mapping dropdown...")
    ocr_dump('dropdown', 0.6, 0.3, 1.0, 0.9)

    # ===== Step 5: Select a set (凝夜白霜 = Freezing Frost) =====
    log("Looking for set names in dropdown...")
    test_sets = ['凝夜白霜', '熔山裂谷', '彻空冥雷', '浮星祛暗', '不绝余音', '啸谷长风']
    selected_set = None
    for sn in test_sets:
        match = ctx.ocr(0.6, 0.3, 1.0, 0.95, match=sn)
        if match:
            b = match[0] if isinstance(match, list) else match
            sx = b.get('x', 0) + b.get('width', 0) / 2
            sy = b.get('y', 0) + b.get('height', 0) / 2
            log(f"Found set '{sn}' at ({sx:.3f}, {sy:.3f}), clicking...")
            dbl_click(sx, sy, after=1.5)
            selected_set = sn
            results['selected_set'] = sn
            break

    if not selected_set:
        log("No known set found, dumping all text...")
        ocr_dump('dropdown_all', 0.6, 0.1, 1.0, 0.95)

    shot('03_set_selected')

    # ===== Step 6: Click 添加主属性筛选 =====
    log("Looking for 添加主属性筛选...")
    main_btn = ctx.ocr(0.6, 0.4, 1.0, 0.7, match='添加')
    if not main_btn:
        main_btn = ctx.ocr(0.6, 0.4, 1.0, 0.7, match='主属性')
    if main_btn:
        b = main_btn[0] if isinstance(main_btn, list) else main_btn
        mx = b.get('x', 0) + b.get('width', 0) / 2
        my = b.get('y', 0) + b.get('height', 0) / 2
        log(f"Found at ({mx:.3f}, {my:.3f}), clicking...")
        dbl_click(mx, my, after=1.5)
    else:
        log("添加主属性筛选 not found")

    shot('04_main_stat_section')
    log("Mapping main stat area...")
    ocr_dump('main_stat', 0.6, 0.4, 1.0, 0.9)

    # ===== Step 7: Look for COST and stat options =====
    log("Looking for cost/stat options...")
    # After clicking 添加主属性筛选, there should be cost buttons (1/3/4) and stat options
    for kw in ['4', '3', '1', '暴击', '攻击', '费用']:
        match = ctx.ocr(0.6, 0.4, 1.0, 0.85, match=kw)
        if match:
            b = match[0] if isinstance(match, list) else match
            log(f"Found '{kw}' at x={b.get('x',0):.3f} y={b.get('y',0):.3f}")

    shot('05_cost_stat_options')

    # ===== Step 8: Click 重置 (Reset) =====
    log("Looking for 重置 button...")
    reset = ctx.ocr(0.6, 0.8, 1.0, 0.95, match='重置')
    if reset:
        b = reset[0] if isinstance(reset, list) else reset
        rx = b.get('x', 0) + b.get('width', 0) / 2
        ry = b.get('y', 0) + b.get('height', 0) / 2
        log(f"Found 重置 at ({rx:.3f}, {ry:.3f}), clicking...")
        dbl_click(rx, ry, after=1.5)
        results['reset_found'] = True
    else:
        log("重置 not found")
        results['reset_found'] = False

    shot('06_after_reset')

    # ===== Step 9: Close filter panel =====
    log("Closing filter panel (double-click funnel again)...")
    dbl_click(0.115, 0.900, after=1.5)
    shot('07_closed')

    log("=== DONE ===")
    return results
