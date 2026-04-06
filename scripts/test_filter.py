"""
Test backpack filter UI - step by step with screenshots.
Usage: POST /script/run {"name": "test_filter"}
Prerequisite: Game open, in backpack echo page (press B first).

Each step is isolated. Run this script, check output/test_filter_*.png screenshots
to verify each UI operation before integrating into SmartEnhanceTask.
"""
import re
import time


def execute(ctx):
    results = {}
    step = 0

    def log(msg):
        nonlocal step
        step += 1
        print(f"[Step {step}] {msg}")

    def shot(label):
        s = ctx.screenshot()
        path = s.get('path', '')
        results[f'{label}_screenshot'] = path
        log(f"Screenshot saved: {label}")
        return path

    def ocr_dump(label, x, y, to_x, to_y):
        """OCR a region and print all boxes with positions."""
        boxes = ctx.ocr(x, y, to_x, to_y)
        texts = []
        if boxes:
            for b in boxes:
                name = b.get('name', '')
                bx = round(b.get('x', 0), 3)
                by = round(b.get('y', 0), 3)
                bw = round(b.get('width', 0), 3)
                bh = round(b.get('height', 0), 3)
                texts.append(f"  [{name}] x={bx} y={by} w={bw} h={bh}")
        log(f"OCR [{label}] ({x},{y})-({to_x},{to_y}): {len(texts)} boxes")
        for t in texts:
            print(t)
        results[f'ocr_{label}'] = texts
        return boxes

    # ===== Prerequisites: ensure we're in backpack =====
    log("Checking if backpack is open...")
    header = ctx.ocr(0, 0, 0.5, 0.15)
    header_texts = [b.get('name', '') for b in (header or [])]
    in_backpack = any(any(kw in t for kw in ['武器', '声骸', '补给', '资源', '/3000']) for t in header_texts)
    results['in_backpack'] = in_backpack
    log(f"Backpack open: {in_backpack}, header: {header_texts}")

    if not in_backpack:
        log("NOT in backpack! Opening backpack with B key...")
        ctx.send_key('b', after_sleep=2)
        # Check for popup
        popup = ctx.ocr(0.2, 0.3, 0.8, 0.8, match='弃置')
        if popup:
            log("Popup detected, dismissing with ESC")
            ctx.send_key('esc', after_sleep=1)
        # Re-check
        header = ctx.ocr(0, 0, 0.5, 0.15)
        header_texts = [b.get('name', '') for b in (header or [])]
        in_backpack = any(any(kw in t for kw in ['武器', '声骸', '补给', '资源', '/3000']) for t in header_texts)
        if not in_backpack:
            log("FAILED to open backpack, aborting")
            return results

    shot('01_backpack_initial')

    # ===== STEP 1: Find the filter (funnel) icon =====
    log("=== STEP 1: Locate filter icon (bottom area) ===")
    # OCR the bottom area to find the funnel/筛选 button
    ocr_dump('bottom_bar', 0, 0.85, 0.25, 1.0)
    # Also try broader area
    ocr_dump('bottom_left', 0, 0.80, 0.20, 1.0)
    shot('02_before_filter_click')

    # ===== STEP 2: Click to open filter panel =====
    log("=== STEP 2: Click filter icon to open panel ===")
    # Try OCR match for '筛' first
    filter_btn = ctx.ocr(0, 0.80, 0.20, 1.0, match='筛')
    if filter_btn:
        # Click it
        b = filter_btn[0] if isinstance(filter_btn, list) else filter_btn
        fx = b.get('x', 0) + b.get('width', 0) / 2
        fy = b.get('y', 0) + b.get('height', 0) / 2
        log(f"Found '筛' at ({fx:.3f}, {fy:.3f}), clicking...")
        ctx.click(fx, fy, after_sleep=1.5)
    else:
        # Fallback: try several positions for the funnel icon
        log("'筛' not found by OCR, trying position clicks...")
        # Common positions for funnel icon in backpack
        positions = [
            (0.06, 0.93, "pos1: 0.06,0.93"),
            (0.06, 0.90, "pos2: 0.06,0.90"),
            (0.04, 0.93, "pos3: 0.04,0.93"),
            (0.08, 0.93, "pos4: 0.08,0.93"),
            (0.10, 0.93, "pos5: 0.10,0.93"),
        ]
        for px, py, desc in positions:
            log(f"Trying click {desc}")
            ctx.click(px, py, after_sleep=1.5)
            # Check if filter panel opened
            check = ctx.ocr(0.55, 0, 0.85, 0.10)
            check_texts = [b.get('name', '') for b in (check or [])]
            if any('筛选' in t for t in check_texts):
                log(f"Filter panel opened with {desc}!")
                results['filter_open_position'] = desc
                break
            # Also check for 合鸣 or 重置 as indicators
            check2 = ctx.ocr(0.55, 0.1, 1.0, 0.5)
            check2_texts = [b.get('name', '') for b in (check2 or [])]
            if any(any(kw in t for kw in ['合鸣', '重置', '筛选']) for t in check2_texts):
                log(f"Filter panel opened with {desc}! (detected via keywords)")
                results['filter_open_position'] = desc
                break
        else:
            log("WARNING: Could not open filter panel with any position")

    time.sleep(0.5)
    shot('03_filter_panel_opened')

    # ===== STEP 3: Map the filter panel layout =====
    log("=== STEP 3: Map filter panel contents ===")
    # OCR the entire right side where filter panel should be
    ocr_dump('filter_panel_top', 0.55, 0, 1.0, 0.15)
    ocr_dump('filter_panel_upper', 0.55, 0.10, 1.0, 0.40)
    ocr_dump('filter_panel_middle', 0.55, 0.35, 1.0, 0.65)
    ocr_dump('filter_panel_lower', 0.55, 0.60, 1.0, 0.85)
    ocr_dump('filter_panel_bottom', 0.55, 0.80, 1.0, 1.0)
    shot('04_filter_panel_mapped')

    # ===== STEP 4: Click 合鸣 dropdown (if visible) =====
    log("=== STEP 4: Click 合鸣 dropdown ===")
    hemming = ctx.ocr(0.55, 0.10, 1.0, 0.50, match='合鸣')
    if hemming:
        b = hemming[0] if isinstance(hemming, list) else hemming
        hx = b.get('x', 0) + b.get('width', 0) / 2
        hy = b.get('y', 0) + b.get('height', 0) / 2
        log(f"Found '合鸣' at ({hx:.3f}, {hy:.3f}), clicking...")
        ctx.click(hx, hy, after_sleep=1.5)
    else:
        log("'合鸣' not found, trying to find dropdown area...")
        # OCR dump to understand layout
        ocr_dump('filter_full', 0.55, 0.05, 1.0, 0.95)

    time.sleep(0.5)
    shot('05_after_hemming_click')

    # ===== STEP 5: Map dropdown contents =====
    log("=== STEP 5: Map dropdown list ===")
    ocr_dump('dropdown_top', 0.55, 0.10, 1.0, 0.40)
    ocr_dump('dropdown_mid', 0.55, 0.35, 1.0, 0.65)
    ocr_dump('dropdown_bot', 0.55, 0.60, 1.0, 0.90)
    shot('06_dropdown_contents')

    # ===== STEP 6: Try selecting a known set (凝夜白霜 = Freezing Frost) =====
    log("=== STEP 6: Select set '凝夜白霜' ===")
    test_set = '凝夜白霜'
    set_match = ctx.ocr(0.55, 0.10, 1.0, 0.95, match=test_set)
    if set_match:
        b = set_match[0] if isinstance(set_match, list) else set_match
        sx = b.get('x', 0) + b.get('width', 0) / 2
        sy = b.get('y', 0) + b.get('height', 0) / 2
        log(f"Found '{test_set}' at ({sx:.3f}, {sy:.3f}), clicking...")
        ctx.click(sx, sy, after_sleep=1.0)
        results['set_found'] = True
    else:
        log(f"'{test_set}' not found in dropdown. Trying scroll or different set...")
        # Try another set
        for alt_set in ['熔山裂谷', '彻空冥雷', '浮星祛暗', '不绝余音']:
            alt_match = ctx.ocr(0.55, 0.10, 1.0, 0.95, match=alt_set)
            if alt_match:
                b = alt_match[0] if isinstance(alt_match, list) else alt_match
                sx = b.get('x', 0) + b.get('width', 0) / 2
                sy = b.get('y', 0) + b.get('height', 0) / 2
                log(f"Found alt set '{alt_set}' at ({sx:.3f}, {sy:.3f}), clicking...")
                ctx.click(sx, sy, after_sleep=1.0)
                results['set_found'] = True
                results['set_used'] = alt_set
                break
        else:
            log("No known set found in dropdown!")
            results['set_found'] = False

    time.sleep(0.5)
    shot('07_after_set_select')

    # ===== STEP 7: Check for 主属性 section =====
    log("=== STEP 7: Look for main stat filter section ===")
    ocr_dump('after_set_full', 0.55, 0.10, 1.0, 0.95)
    # Look for 主属性/添加 keywords
    main_stat_btn = ctx.ocr(0.55, 0.30, 1.0, 0.70, match='主属性')
    if main_stat_btn:
        b = main_stat_btn[0] if isinstance(main_stat_btn, list) else main_stat_btn
        mx = b.get('x', 0) + b.get('width', 0) / 2
        my = b.get('y', 0) + b.get('height', 0) / 2
        log(f"Found '主属性' at ({mx:.3f}, {my:.3f})")
        results['main_stat_section_found'] = True
    else:
        log("'主属性' section not found")
        results['main_stat_section_found'] = False

    shot('08_main_stat_section')

    # ===== STEP 8: Click 主属性 to expand/add =====
    log("=== STEP 8: Click to add main stat filter ===")
    if main_stat_btn:
        ctx.click(mx, my, after_sleep=1.5)
        time.sleep(0.5)
        ocr_dump('main_stat_expanded', 0.55, 0.30, 1.0, 0.95)
        shot('09_main_stat_expanded')
    else:
        # Try looking for 添加
        add_btn = ctx.ocr(0.55, 0.30, 1.0, 0.70, match='添加')
        if add_btn:
            b = add_btn[0] if isinstance(add_btn, list) else add_btn
            ax = b.get('x', 0) + b.get('width', 0) / 2
            ay = b.get('y', 0) + b.get('height', 0) / 2
            log(f"Found '添加' at ({ax:.3f}, {ay:.3f}), clicking...")
            ctx.click(ax, ay, after_sleep=1.5)
            ocr_dump('add_expanded', 0.55, 0.30, 1.0, 0.95)
            shot('09_add_expanded')

    # ===== STEP 9: Look for COST buttons (1/3/4) =====
    log("=== STEP 9: Find COST selectors ===")
    ocr_dump('cost_area', 0.55, 0.30, 1.0, 0.75)
    # Try to find and click COST 4
    cost_match = ctx.ocr(0.55, 0.30, 1.0, 0.75, match='4')
    if cost_match:
        b = cost_match[0] if isinstance(cost_match, list) else cost_match
        cx = b.get('x', 0) + b.get('width', 0) / 2
        cy = b.get('y', 0) + b.get('height', 0) / 2
        log(f"Found '4' (cost) at ({cx:.3f}, {cy:.3f}), clicking...")
        ctx.click(cx, cy, after_sleep=1.0)
        results['cost_found'] = True
    else:
        log("Cost '4' not found")
        results['cost_found'] = False

    shot('10_after_cost_select')

    # ===== STEP 10: Look for main stat options (暴击伤害, 攻击力百分比, etc.) =====
    log("=== STEP 10: Find main stat options ===")
    ocr_dump('stat_options', 0.55, 0.40, 1.0, 0.90)

    # Try clicking 暴击伤害
    stat_match = ctx.ocr(0.55, 0.40, 1.0, 0.90, match='暴击伤害')
    if stat_match:
        b = stat_match[0] if isinstance(stat_match, list) else stat_match
        stx = b.get('x', 0) + b.get('width', 0) / 2
        sty = b.get('y', 0) + b.get('height', 0) / 2
        log(f"Found '暴击伤害' at ({stx:.3f}, {sty:.3f}), clicking...")
        ctx.click(stx, sty, after_sleep=1.0)
        results['main_stat_found'] = True
    else:
        log("'暴击伤害' not found, listing all visible stat options...")
        results['main_stat_found'] = False

    shot('11_after_stat_select')

    # ===== STEP 11: Check if filter is applied (look for filtered results) =====
    log("=== STEP 11: Verify filter effect ===")
    ocr_dump('left_panel_after', 0, 0.05, 0.55, 0.30)
    shot('12_filter_applied_result')

    # ===== STEP 12: Find and click 重置 (reset) button =====
    log("=== STEP 12: Reset filter ===")
    ocr_dump('reset_area', 0.55, 0.80, 1.0, 1.0)
    reset_btn = ctx.ocr(0.55, 0.75, 1.0, 1.0, match='重置')
    if reset_btn:
        b = reset_btn[0] if isinstance(reset_btn, list) else reset_btn
        rx = b.get('x', 0) + b.get('width', 0) / 2
        ry = b.get('y', 0) + b.get('height', 0) / 2
        log(f"Found '重置' at ({rx:.3f}, {ry:.3f}), clicking...")
        ctx.click(rx, ry, after_sleep=1.0)
        results['reset_found'] = True
    else:
        log("'重置' not found")
        results['reset_found'] = False

    shot('13_after_reset')

    # ===== STEP 13: Close filter panel =====
    log("=== STEP 13: Close filter panel ===")
    # Try clicking outside the filter panel (left side)
    ctx.click(0.3, 0.3, after_sleep=1.0)
    shot('14_filter_closed')

    # ===== Summary =====
    log("")
    log("========= FILTER TEST SUMMARY =========")
    log(f"  Backpack:         {results.get('in_backpack')}")
    log(f"  Filter opened:    {results.get('filter_open_position', 'via OCR' if True else 'UNKNOWN')}")
    log(f"  Set found:        {results.get('set_found')}")
    log(f"  Main stat found:  {results.get('main_stat_found')}")
    log(f"  Cost found:       {results.get('cost_found')}")
    log(f"  Reset found:      {results.get('reset_found')}")

    return results
