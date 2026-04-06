"""
Phase 1: Map echo backpack page layout. NO clicks except ESC and B.
Navigate to echo backpack, then OCR+screenshot everything.
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
        if boxes:
            for b in boxes:
                print(f"  [{b.get('name','')}] x={b.get('x',0):.4f} y={b.get('y',0):.4f} w={b.get('width',0):.4f} h={b.get('height',0):.4f}")
        else:
            print("  (empty)")
        return boxes

    # === Step 1: Return to main world ===
    log("Returning to main world (ESC loop)...")
    menu_kw = ['终端', '武器', '声骸', '补给', '资源', '设置', '数据坞', '背包', '共鸣者', '编队', '属性', '特殊', '筛选']
    for attempt in range(10):
        top = ctx.ocr(0, 0, 0.3, 0.1)
        texts = [b.get('name', '') for b in (top or [])]
        in_menu = any(any(kw in t for kw in menu_kw) for t in texts)
        if not in_menu:
            center = ctx.ocr(0.2, 0.3, 0.8, 0.7, match='弃置')
            if not center:
                break
        ctx.send_key('esc', after_sleep=0.8)
    time.sleep(0.5)
    log("Main world reached")

    # === Step 2: Open backpack with B ===
    log("Opening backpack with B key...")
    ctx.send_key('b', after_sleep=2.5)

    # Dismiss popup if any
    popup = ctx.ocr(0.2, 0.3, 0.8, 0.8, match='弃置')
    if popup:
        log("Popup detected, ESC to dismiss")
        ctx.send_key('esc', after_sleep=1)

    # Verify echo tab
    header = ctx.ocr(0, 0, 0.25, 0.08)
    header_texts = [b.get('name', '') for b in (header or [])]
    log(f"Header: {header_texts}")
    results['header'] = header_texts

    # === Step 3: Take full screenshot ===
    s = ctx.screenshot()
    results['screenshot'] = s.get('path', '')
    log(f"Full screenshot: {results['screenshot']}")

    # === Step 4: Map ALL text on the page ===
    log("=== FULL PAGE OCR MAP ===")

    log("--- Header area (0,0)-(0.65,0.08) ---")
    ocr_region('header_full', 0, 0, 0.65, 0.08)

    log("--- Header buttons (0.30,0)-(0.65,0.06) ---")
    ocr_region('header_buttons', 0.30, 0, 0.65, 0.06)

    log("--- Bottom bar LEFT (0.05,0.87)-(0.40,1.0) ---")
    ocr_region('bottom_left', 0.05, 0.87, 0.40, 1.0)

    log("--- Bottom bar CENTER (0.35,0.87)-(0.70,1.0) ---")
    ocr_region('bottom_center', 0.35, 0.87, 0.70, 1.0)

    log("--- Bottom bar RIGHT (0.65,0.87)-(1.0,1.0) ---")
    ocr_region('bottom_right', 0.65, 0.87, 1.0, 1.0)

    log("--- Right panel detail (0.65,0.05)-(1.0,0.50) ---")
    ocr_region('right_detail', 0.65, 0.05, 1.0, 0.50)

    log("--- Right panel bottom (0.65,0.80)-(1.0,1.0) ---")
    ocr_region('right_panel_bottom', 0.65, 0.80, 1.0, 1.0)

    log("--- Full left side strip (0.04,0.85)-(0.65,0.98) ---")
    ocr_region('left_bottom_strip', 0.04, 0.85, 0.65, 0.98)

    # === Step 5: Search for filter-related keywords ===
    log("=== KEYWORD SEARCH (full page) ===")
    for kw in ['筛', '筛选', '过滤', '管理', '方案', '排序', '顺序', '批量']:
        match = ctx.ocr(0, 0, 1.0, 1.0, match=kw)
        if match:
            for b in (match if isinstance(match, list) else [match]):
                x = b.get('x', 0)
                y = b.get('y', 0)
                w = b.get('width', 0)
                h = b.get('height', 0)
                name = b.get('name', '')
                print(f"  FOUND '{kw}' in [{name}] at x={x:.4f} y={y:.4f} w={w:.4f} h={h:.4f}")
                results[f'found_{kw}'] = {'name': name, 'x': x, 'y': y}
        else:
            print(f"  '{kw}' not found")

    log("=== DONE - Review screenshot and OCR data ===")
    return results
