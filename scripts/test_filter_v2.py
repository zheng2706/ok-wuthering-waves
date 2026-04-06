"""Filter test v2: select visible set, test main stat, verify filter effect."""
import time


def execute(ctx):
    results = {}
    log_lines = []
    def log(msg):
        log_lines.append(str(msg))
        results['_log'] = log_lines[-10:]  # keep last 10 lines
    def shot(label):
        s = ctx.screenshot()
        results[label] = s.get('path', '')

    # 1. Open filter panel
    log("1. Open filter panel")
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    if not ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选'):
        ctx.dbl_click(0.115, 0.900, after_sleep=2)
    shot('01')

    # 2. Open 合鸣 dropdown
    log("2. Open dropdown")
    ctx.real_click(0.85, 0.454, after_sleep=2)
    shot('02')

    # 3. Select first visible set (any set with >3 char name below header)
    log("3. Select a visible set")
    dd = ctx.ocr(0.6, 0.48, 1.0, 0.85)
    selected = None
    for b in (dd or []):
        name = b.get('name', '')
        if len(name) > 3 and '全部' not in name and '筛选' not in name:
            cx = b.get('x', 0) + b.get('width', 0) / 2
            cy = b.get('y', 0) + b.get('height', 0) / 2
            log(f"  Selecting [{name}] at ({cx:.3f},{cy:.3f})")
            ctx.real_click(cx, cy, after_sleep=2)
            selected = name
            results['set'] = name
            break
    shot('03')

    if not selected:
        log("  No set found to select!")
        return results

    # 4. Verify dropdown closed and set is shown
    log("4. Verify set selected")
    panel = ctx.ocr(0.6, 0.4, 1.0, 0.5)
    for b in (panel or []):
        log(f"  [{b.get('name','')}]")
    shot('04')

    # 5. Click 添加主属性筛选 + button
    log("5. Add main stat filter")
    add = ctx.ocr(0.6, 0.5, 1.0, 0.7, match='添加')
    if add:
        b = add[0] if isinstance(add, list) else add
        # Click the + button at the right end
        ay = b.get('y', 0) + b.get('height', 0) / 2
        log(f"  Found at y={ay:.3f}, clicking + at (0.96, {ay:.3f})")
        ctx.real_click(0.96, ay, after_sleep=2)
    else:
        log("  Trying position (0.96, 0.592)")
        ctx.real_click(0.96, 0.592, after_sleep=2)
    shot('05')

    # 6. Map cost/stat options
    log("6. Map options after clicking +")
    opts = ctx.ocr(0.6, 0.5, 1.0, 0.9)
    for b in (opts or []):
        n = b.get('name', '')
        cx = b.get('x',0) + b.get('width',0)/2
        cy = b.get('y',0) + b.get('height',0)/2
        log(f"  [{n}] ({cx:.3f},{cy:.3f})")

    # 7. Try to click cost "4" if visible
    log("7. Select cost 4")
    c4 = ctx.ocr(0.6, 0.5, 1.0, 0.85, match='4')
    if c4:
        b = c4[0] if isinstance(c4, list) else c4
        cx = b.get('x',0) + b.get('width',0)/2
        cy = b.get('y',0) + b.get('height',0)/2
        log(f"  cost 4 at ({cx:.3f},{cy:.3f})")
        ctx.real_click(cx, cy, after_sleep=1.5)
    shot('07')

    # 8. Try to click a main stat if visible
    log("8. Select main stat")
    for stat in ['暴击伤害', '暴击率', '攻击力', '生命值', '防御力']:
        sm = ctx.ocr(0.6, 0.55, 1.0, 0.9, match=stat)
        if sm:
            b = sm[0] if isinstance(sm, list) else sm
            cx = b.get('x',0) + b.get('width',0)/2
            cy = b.get('y',0) + b.get('height',0)/2
            log(f"  stat [{stat}] at ({cx:.3f},{cy:.3f})")
            ctx.real_click(cx, cy, after_sleep=1.5)
            results['stat'] = stat
            break
    shot('08')

    # 9. Check echo count (should be filtered)
    log("9. Verify filter")
    h = ctx.ocr(0, 0, 0.25, 0.08)
    for b in (h or []):
        log(f"  Header: [{b.get('name','')}]")
    shot('09')

    # 10. Reset
    log("10. Reset")
    reset = ctx.ocr(0.6, 0.8, 1.0, 0.92, match='重置')
    if reset:
        b = reset[0] if isinstance(reset, list) else reset
        ctx.real_click(b.get('x',0)+b.get('width',0)/2, b.get('y',0)+b.get('height',0)/2, after_sleep=1.5)
    shot('10')

    # 11. Close
    log("11. Close")
    ctx.dbl_click(0.115, 0.900, after_sleep=1)
    shot('11')

    return results
