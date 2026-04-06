"""
Full filter workflow test using real_click + dbl_click.
1. Open filter panel (dbl_click funnel)
2. Open 合鸣 dropdown (real_click)
3. Select a set
4. Open 添加主属性筛选
5. Select cost + main stat
6. Verify filter applied
7. Reset
"""
import time


def execute(ctx):
    results = {}

    def log(msg):
        print(msg)

    def shot(label):
        s = ctx.screenshot()
        results[label] = s.get('path', '')
        return results[label]

    # === Navigate to echo backpack ===
    log("Step 0: Navigate to echo backpack")
    for _ in range(5):
        ctx.send_key('esc', after_sleep=0.7)
    time.sleep(0.5)
    ctx.send_key('b', after_sleep=2.5)
    ctx.send_key('esc', after_sleep=1)
    ctx.click(0.02, 0.30, after_sleep=2)
    h = ctx.ocr(0, 0, 0.25, 0.08)
    if not any('声骸' in b.get('name', '') for b in (h or [])):
        return {'error': 'not on echo page'}

    # === Step 1: Open filter panel ===
    log("Step 1: Open filter (dbl_click funnel)")
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    if not ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选'):
        ctx.dbl_click(0.115, 0.900, after_sleep=2)
    shot('01_panel')

    # === Step 2: Open 合鸣 dropdown ===
    log("Step 2: Open dropdown (real_click)")
    ctx.real_click(0.85, 0.454, after_sleep=2)
    # Verify dropdown expanded
    dd = ctx.ocr(0.6, 0.45, 1.0, 0.85)
    dd_names = [b.get('name', '') for b in (dd or [])]
    log(f"  Dropdown items: {dd_names[:8]}")
    shot('02_dropdown')

    if not any(len(n) > 3 for n in dd_names if n not in ['合鸣筛选/全部']):
        log("  Dropdown didn't expand, trying arrow position...")
        ctx.real_click(0.95, 0.454, after_sleep=2)
        dd = ctx.ocr(0.6, 0.45, 1.0, 0.85)
        dd_names = [b.get('name', '') for b in (dd or [])]
        log(f"  Retry items: {dd_names[:8]}")

    # === Step 3: Select a set (scroll to find known set names) ===
    log("Step 3: Select set")
    # First, map all visible sets
    all_sets = ctx.ocr(0.6, 0.45, 1.0, 0.95)
    for b in (all_sets or []):
        name = b.get('name', '')
        if len(name) > 3 and name not in ['合鸣筛选/全部', '添加主属性筛选']:
            cx = b.get('x', 0) + b.get('width', 0) / 2
            cy = b.get('y', 0) + b.get('height', 0) / 2
            log(f"  Set: [{name}] center=({cx:.3f},{cy:.3f})")

    # Try to find and click a known set
    known_sets = ['凝夜白霜', '熔山裂谷', '彻空冥雷', '浮星祛暗', '不绝余音',
                  '啸谷长风', '沉日劫明', '隐世回光', '轻云出月']

    selected = None
    # May need to scroll down in the dropdown to find sets
    for attempt in range(3):
        for sn in known_sets:
            match = ctx.ocr(0.6, 0.4, 1.0, 0.95, match=sn)
            if match:
                b = match[0] if isinstance(match, list) else match
                sx = b.get('x', 0) + b.get('width', 0) / 2
                sy = b.get('y', 0) + b.get('height', 0) / 2
                log(f"  Found '{sn}' at ({sx:.3f},{sy:.3f}), real_clicking...")
                ctx.real_click(sx, sy, after_sleep=1.5)
                selected = sn
                break
        if selected:
            break
        # Scroll down in dropdown
        log(f"  Scrolling down (attempt {attempt+1})...")
        ctx.scroll(0.85, 0.70, -3)
        time.sleep(1)

    results['selected_set'] = selected
    shot('03_set_selected')

    # === Step 4: Open 添加主属性筛选 ===
    log("Step 4: Add main stat filter")
    # Find the + button for 添加主属性筛选
    add_btn = ctx.ocr(0.6, 0.4, 1.0, 0.7, match='添加')
    if add_btn:
        b = add_btn[0] if isinstance(add_btn, list) else add_btn
        ay = b.get('y', 0) + b.get('height', 0) / 2
        log(f"  Found 添加 at y={ay:.3f}, real_clicking + button...")
        ctx.real_click(0.96, ay, after_sleep=2)
    else:
        log("  添加 not found, trying position...")
        ctx.real_click(0.96, 0.592, after_sleep=2)

    shot('04_main_stat')
    # Map what appeared
    ms = ctx.ocr(0.6, 0.5, 1.0, 0.9)
    for b in (ms or []):
        name = b.get('name', '')
        cx = b.get('x', 0) + b.get('width', 0) / 2
        cy = b.get('y', 0) + b.get('height', 0) / 2
        log(f"  Main stat area: [{name}] ({cx:.3f},{cy:.3f})")

    # === Step 5: Select cost (e.g., 4) ===
    log("Step 5: Select cost")
    cost_match = ctx.ocr(0.6, 0.5, 1.0, 0.85, match='4')
    if cost_match:
        b = cost_match[0] if isinstance(cost_match, list) else cost_match
        cx = b.get('x', 0) + b.get('width', 0) / 2
        cy = b.get('y', 0) + b.get('height', 0) / 2
        log(f"  Found cost '4' at ({cx:.3f},{cy:.3f})")
        ctx.real_click(cx, cy, after_sleep=1.5)
    shot('05_cost')

    # === Step 6: Select main stat (e.g., 暴击伤害) ===
    log("Step 6: Select main stat")
    stat_match = ctx.ocr(0.6, 0.5, 1.0, 0.9, match='暴击伤害')
    if not stat_match:
        stat_match = ctx.ocr(0.6, 0.5, 1.0, 0.9, match='攻击')
    if stat_match:
        b = stat_match[0] if isinstance(stat_match, list) else stat_match
        cx = b.get('x', 0) + b.get('width', 0) / 2
        cy = b.get('y', 0) + b.get('height', 0) / 2
        log(f"  Found stat at ({cx:.3f},{cy:.3f})")
        ctx.real_click(cx, cy, after_sleep=1.5)
    shot('06_stat')

    # === Step 7: Verify filter applied ===
    log("Step 7: Verify")
    shot('07_result')

    # === Step 8: Reset ===
    log("Step 8: Reset")
    reset = ctx.ocr(0.6, 0.8, 1.0, 0.92, match='重置')
    if reset:
        b = reset[0] if isinstance(reset, list) else reset
        rx = b.get('x', 0) + b.get('width', 0) / 2
        ry = b.get('y', 0) + b.get('height', 0) / 2
        ctx.real_click(rx, ry, after_sleep=1.5)
    shot('08_reset')

    # === Step 9: Close panel ===
    log("Step 9: Close filter panel")
    ctx.dbl_click(0.115, 0.900, after_sleep=1)
    shot('09_closed')

    log("DONE")
    return results
