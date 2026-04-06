"""
Test filter step 1: Find the filter icon on echo backpack page.
Prerequisite: Must already be on echo backpack page.
This script only maps the full UI - no clicks that could change tabs.
"""
import time


def execute(ctx):
    results = {}
    step = 0

    def log(msg):
        nonlocal step
        step += 1
        print(f"[{step}] {msg}")

    def ocr_region(label, x, y, to_x, to_y):
        boxes = ctx.ocr(x, y, to_x, to_y)
        texts = []
        if boxes:
            for b in boxes:
                name = b.get('name', '')
                bx = round(b.get('x', 0), 4)
                by = round(b.get('y', 0), 4)
                bw = round(b.get('width', 0), 4)
                bh = round(b.get('height', 0), 4)
                texts.append(f"  [{name}] x={bx} y={by} w={bw} h={bh}")
                print(f"  [{name}] x={bx} y={by} w={bw} h={bh}")
        log(f"OCR [{label}] ({x},{y})-({to_x},{to_y}): {len(texts)} boxes")
        results[f'ocr_{label}'] = texts
        return boxes

    # Step 1: Verify we're on echo page
    log("=== Verifying echo page ===")
    ocr_region('header', 0, 0, 0.25, 0.08)

    # Step 2: Map the ENTIRE bottom bar carefully
    log("=== Bottom bar full scan ===")
    ocr_region('bottom_full', 0, 0.85, 0.70, 1.0)

    # Step 3: Map the entire left sidebar
    log("=== Left sidebar scan ===")
    ocr_region('sidebar', 0, 0.05, 0.06, 0.95)

    # Step 4: Map the sort/filter area between sidebar and grid
    log("=== Sort/filter area between sidebar and grid ===")
    ocr_region('sort_area', 0.06, 0.85, 0.30, 1.0)

    # Step 5: Map the grid header area (above echoes, below tab header)
    log("=== Grid header area ===")
    ocr_region('grid_header', 0.03, 0.07, 0.65, 0.14)

    # Step 6: Map the right panel bottom (培养 area)
    log("=== Right panel bottom ===")
    ocr_region('right_bottom', 0.65, 0.85, 1.0, 1.0)

    # Step 7: Full page scan in a grid pattern for completeness
    log("=== Full page text map ===")
    # Scan horizontal strips
    for y_start in [0.0, 0.12, 0.85, 0.90, 0.95]:
        y_end = min(y_start + 0.08, 1.0)
        ocr_region(f'strip_y{y_start:.2f}', 0, y_start, 0.65, y_end)

    # Take full screenshot
    s = ctx.screenshot()
    results['screenshot'] = s.get('path', '')
    log(f"Screenshot: {results['screenshot']}")

    # Step 8: Look specifically for filter-related text
    log("=== Searching for filter keywords ===")
    for kw in ['筛', '过滤', '筛选', '排序', '管理']:
        match = ctx.ocr(0, 0, 1.0, 1.0, match=kw)
        found = bool(match)
        if match and isinstance(match, list):
            for b in match:
                bx = round(b.get('x', 0), 4)
                by = round(b.get('y', 0), 4)
                print(f"  '{kw}' found at x={bx} y={by}")
        log(f"Keyword '{kw}': {'FOUND' if found else 'not found'}")
        results[f'kw_{kw}'] = found

    return results
