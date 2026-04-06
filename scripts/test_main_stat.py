"""Test main stat filter: after set is selected, click + to add cost+stat."""
import time


def execute(ctx):
    results = {}
    log_lines = []
    def log(msg):
        log_lines.append(str(msg))
        results['_log'] = log_lines[-15:]

    def shot(label):
        s = ctx.screenshot()
        results[label] = s.get('path', '')

    # Ensure filter panel is open with a set selected
    fcheck = ctx.ocr(0.6, 0.02, 1.0, 0.08, match='筛选')
    if not fcheck:
        log("Filter not open. Opening and selecting set...")
        ctx.dbl_click(0.115, 0.900, after_sleep=2)
        ctx.real_click(0.85, 0.454, after_sleep=2)
        # Select first visible set
        dd = ctx.ocr(0.6, 0.48, 1.0, 0.75)
        for b in (dd or []):
            n = b.get('name', '')
            if len(n) > 3 and '全部' not in n and '筛选' not in n and not n.isdigit():
                cx = b.get('x',0) + b.get('width',0)/2
                cy = b.get('y',0) + b.get('height',0)/2
                ctx.real_click(cx, cy, after_sleep=2)
                log(f"Selected set: {n}")
                break

    shot('00_before')

    # Find 添加主属性筛选 precise position
    log("Finding 添加主属性筛选...")
    add = ctx.ocr(0.6, 0.4, 1.0, 0.65, match='添加')
    if add:
        b = add[0] if isinstance(add, list) else add
        ax = b.get('x', 0)
        ay = b.get('y', 0)
        aw = b.get('width', 0)
        ah = b.get('height', 0)
        log(f"  Text at ({ax:.3f},{ay:.3f}) w={aw:.3f} h={ah:.3f}")

        # Click the + button (at the far right of the row)
        plus_x = ax + aw + 0.02  # slightly right of text
        plus_y = ay + ah / 2
        log(f"  Clicking + at ({plus_x:.3f},{plus_y:.3f})")
        ctx.real_click(plus_x, plus_y, after_sleep=2)
        shot('01_after_plus')

        # Map what appeared
        log("Mapping after + click...")
        opts = ctx.ocr(0.6, 0.4, 1.0, 0.9)
        for b in (opts or []):
            n = b.get('name', '')
            cx = b.get('x',0) + b.get('width',0)/2
            cy = b.get('y',0) + b.get('height',0)/2
            log(f"  [{n}] ({cx:.3f},{cy:.3f})")

        # If no new options appeared, try clicking the text itself
        texts = [b.get('name','') for b in (opts or [])]
        if not any(kw in ''.join(texts) for kw in ['费用', '1', '3', '4', '暴击']):
            log("No cost/stat options. Try clicking text itself...")
            ctx.real_click(ax + aw/2, ay + ah/2, after_sleep=2)
            shot('01b_click_text')
            opts = ctx.ocr(0.6, 0.4, 1.0, 0.9)
            for b in (opts or []):
                n = b.get('name', '')
                cx = b.get('x',0) + b.get('width',0)/2
                cy = b.get('y',0) + b.get('height',0)/2
                log(f"  [{n}] ({cx:.3f},{cy:.3f})")
    else:
        log("添加 not found!")

    shot('02_final')
    return results
