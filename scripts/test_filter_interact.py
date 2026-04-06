"""
Test filter panel INTERNAL interactions.
Prerequisite: filter panel already open (or will open it).
Focus on: 合鸣 dropdown, 添加主属性筛选, 重置.
Try both single-click and double-click on each element.
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
        results[f'{label}'] = s.get('path', '')
        return results[f'{label}']

    def dbl_click(x, y, after=1.0):
        ctx.click(x, y, after_sleep=0.1)
        ctx.click(x, y, after_sleep=after)

    def find_and_report(label, x, y, to_x, to_y):
        boxes = ctx.ocr(x, y, to_x, to_y)
        for b in (boxes or []):
            cx = b.get('x', 0) + b.get('width', 0) / 2
            cy = b.get('y', 0) + b.get('height', 0) / 2
            log(f"  [{b.get('name','')}] center=({cx:.3f}, {cy:.3f})")
        return boxes

    # === Ensure filter panel is open ===
    log("Checking if filter panel is open...")
    fcheck = ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选')
    if not fcheck:
        log("Opening filter panel...")
        # Navigate to echo backpack first
        for _ in range(5):
            ctx.send_key('esc', after_sleep=0.7)
        time.sleep(0.5)
        ctx.send_key('b', after_sleep=2.5)
        ctx.send_key('esc', after_sleep=1)
        ctx.click(0.02, 0.30, after_sleep=2)
        dbl_click(0.115, 0.900, after=2)
        fcheck = ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选')
        if not fcheck:
            return {'error': 'cannot open filter'}

    log("Filter panel confirmed open")
    shot('00_panel_open')

    # === Map panel with precise OCR ===
    log("=== Full panel OCR ===")
    find_and_report('panel', 0.6, 0.02, 1.0, 0.95)

    # === Test 合鸣 dropdown ===
    log("=== Testing 合鸣 dropdown ===")

    # Find the dropdown arrow (∨) for 合鸣
    hemming_area = ctx.ocr(0.6, 0.25, 1.0, 0.45)
    for b in (hemming_area or []):
        log(f"  合鸣 area: [{b.get('name','')}] x={b.get('x',0):.3f} y={b.get('y',0):.3f} w={b.get('width',0):.3f}")

    # Try clicking the dropdown arrow (right side of the dropdown, near the ∨)
    # Based on user screenshot: dropdown row is at y≈0.28, arrow at x≈0.96
    strategies = [
        # (x, y, description, use_double)
        (0.96, 0.285, "dropdown_arrow_dbl", True),
        (0.90, 0.285, "dropdown_center_dbl", True),
        (0.85, 0.285, "dropdown_left_dbl", True),
        (0.96, 0.285, "dropdown_arrow_single", False),
        (0.90, 0.285, "dropdown_center_single", False),
    ]

    for x, y, desc, use_dbl in strategies:
        log(f"Trying {desc} at ({x}, {y})...")
        if use_dbl:
            dbl_click(x, y, after=1.5)
        else:
            ctx.click(x, y, after_sleep=1.5)

        # Check if dropdown expanded (should show set names)
        expanded = ctx.ocr(0.6, 0.3, 1.0, 0.85)
        texts = [b.get('name', '') for b in (expanded or [])]
        # Look for set names or "全部" options that indicate dropdown expanded
        set_indicators = [t for t in texts if any(kw in t for kw in ['凝夜', '熔山', '彻空', '啸谷', '浮星', '全部', '冰伤', '不绝'])]
        if len(set_indicators) > 1:  # Multiple set-related texts = dropdown expanded
            log(f"  DROPDOWN EXPANDED! Found: {set_indicators[:5]}")
            results['dropdown_method'] = desc
            shot(f'01_dropdown_{desc}')
            # Map dropdown contents
            log("Mapping dropdown contents...")
            find_and_report('dropdown', 0.6, 0.3, 1.0, 0.85)
            break
        else:
            log(f"  Not expanded. Texts: {texts[:3]}")

    if 'dropdown_method' not in results:
        log("All dropdown strategies failed")
        shot('01_dropdown_fail')

    # === If dropdown is open, select a set ===
    if 'dropdown_method' in results:
        log("=== Selecting a set ===")
        for sn in ['凝夜白霜', '熔山裂谷', '彻空冥雷']:
            match = ctx.ocr(0.6, 0.3, 1.0, 0.85, match=sn)
            if match:
                b = match[0] if isinstance(match, list) else match
                sx = b.get('x', 0) + b.get('width', 0) / 2
                sy = b.get('y', 0) + b.get('height', 0) / 2
                log(f"Selecting '{sn}' at ({sx:.3f}, {sy:.3f})...")
                dbl_click(sx, sy, after=1.5)
                results['selected_set'] = sn
                shot('02_set_selected')
                break

    # === Test 添加主属性筛选 ===
    log("=== Testing 添加主属性筛选 ===")
    add_btn = ctx.ocr(0.6, 0.35, 1.0, 0.55, match='添加')
    if add_btn:
        b = add_btn[0] if isinstance(add_btn, list) else add_btn
        ax = b.get('x', 0) + b.get('width', 0) / 2
        ay = b.get('y', 0) + b.get('height', 0) / 2
        log(f"Found 添加 at ({ax:.3f}, {ay:.3f})")

        # Try double-click on the + button (right side)
        log("Double-clicking + button area...")
        dbl_click(0.96, ay, after=1.5)
        shot('03_add_main_stat')

        # Check if expanded
        log("Checking for cost/stat options...")
        find_and_report('cost_stat', 0.6, 0.35, 1.0, 0.85)

    # === Test 重置 ===
    log("=== Testing 重置 ===")
    reset = ctx.ocr(0.6, 0.75, 1.0, 0.92, match='重置')
    if reset:
        b = reset[0] if isinstance(reset, list) else reset
        rx = b.get('x', 0) + b.get('width', 0) / 2
        ry = b.get('y', 0) + b.get('height', 0) / 2
        log(f"Found 重置 at ({rx:.3f}, {ry:.3f})")
        dbl_click(rx, ry, after=1.5)
        shot('04_after_reset')

    log("=== DONE ===")
    return results
