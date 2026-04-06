"""Quick filter test - assumes already on echo backpack page."""
import time
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def execute(ctx):
    results = {}
    def log(msg): print(str(msg))
    def shot(label):
        s = ctx.screenshot()
        results[label] = s.get('path', '')

    # Step 1: Open filter panel
    log("1. Open filter (dbl_click)")
    ctx.dbl_click(0.115, 0.900, after_sleep=2)
    if not ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选'):
        ctx.dbl_click(0.115, 0.900, after_sleep=2)
    shot('01_panel')

    # Step 2: Open 合鸣 dropdown
    log("2. Open dropdown (real_click)")
    ctx.real_click(0.85, 0.454, after_sleep=2)
    shot('02_dropdown')

    # Step 3: Map and select a set (scroll to find known ones)
    log("3. Select set")
    # Map all visible text in dropdown
    dd = ctx.ocr(0.6, 0.45, 1.0, 0.95)
    for b in (dd or []):
        n = b.get('name', '')
        if len(n) > 3:
            log(f"  [{n}]")

    # Scroll down to find known sets
    for attempt in range(5):
        for sn in ['凝夜白霜', '熔山裂谷', '啸谷长风', '不绝余音', '浮星祛暗',
                    '轻云出月', '隐世回光', '彻空冥雷', '沉日劫明']:
            match = ctx.ocr(0.6, 0.4, 1.0, 0.95, match=sn)
            if match:
                b = match[0] if isinstance(match, list) else match
                sx = b.get('x', 0) + b.get('width', 0) / 2
                sy = b.get('y', 0) + b.get('height', 0) / 2
                log(f"  FOUND '{sn}' at ({sx:.3f},{sy:.3f})")
                ctx.real_click(sx, sy, after_sleep=1.5)
                results['set'] = sn
                shot('03_set')
                break
        if 'set' in results:
            break
        log(f"  Scroll down #{attempt+1}")
        # Scroll inside dropdown area
        ctx.scroll(0.85, 0.70, -3)
        time.sleep(1)

    # Step 4: 添加主属性筛选
    log("4. Add main stat")
    add = ctx.ocr(0.6, 0.35, 1.0, 0.65, match='添加')
    if add:
        b = add[0] if isinstance(add, list) else add
        ay = b.get('y', 0) + b.get('height', 0) / 2
        ctx.real_click(0.96, ay, after_sleep=2)
    shot('04_main_stat')

    # Map cost/stat options
    opts = ctx.ocr(0.6, 0.5, 1.0, 0.9)
    for b in (opts or []):
        n = b.get('name', '')
        if len(n) >= 1:
            cx = b.get('x',0) + b.get('width',0)/2
            cy = b.get('y',0) + b.get('height',0)/2
            log(f"  opt: [{n}] ({cx:.3f},{cy:.3f})")

    # Step 5: Select cost 4
    log("5. Select cost 4")
    c4 = ctx.ocr(0.6, 0.5, 1.0, 0.8, match='4')
    if c4:
        b = c4[0] if isinstance(c4, list) else c4
        ctx.real_click(b.get('x',0)+b.get('width',0)/2, b.get('y',0)+b.get('height',0)/2, after_sleep=1.5)
    shot('05_cost')

    # Step 6: Select main stat
    log("6. Select stat")
    for stat in ['暴击伤害', '攻击力', '暴击率']:
        sm = ctx.ocr(0.6, 0.5, 1.0, 0.9, match=stat)
        if sm:
            b = sm[0] if isinstance(sm, list) else sm
            ctx.real_click(b.get('x',0)+b.get('width',0)/2, b.get('y',0)+b.get('height',0)/2, after_sleep=1.5)
            results['stat'] = stat
            break
    shot('06_stat')

    # Step 7: Reset
    log("7. Reset")
    r = ctx.ocr(0.6, 0.8, 1.0, 0.92, match='重置')
    if r:
        b = r[0] if isinstance(r, list) else r
        ctx.real_click(b.get('x',0)+b.get('width',0)/2, b.get('y',0)+b.get('height',0)/2, after_sleep=1.5)
    shot('07_reset')

    # Step 8: Close
    log("8. Close")
    ctx.dbl_click(0.115, 0.900, after_sleep=1)
    shot('08_closed')

    return results
