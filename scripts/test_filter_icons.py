"""
Phase 1b: Test bottom-bar small icons to find filter entry.
Must already be on echo backpack page.
Click each candidate icon ONE AT A TIME, check if filter panel opens.
"""
import time


def execute(ctx):
    results = {}
    step = 0

    def log(msg):
        nonlocal step
        step += 1
        print(f"[{step}] {msg}")

    def check_filter_opened():
        """Check if a filter/panel opened on the right side."""
        # Look for filter-related keywords anywhere
        for kw in ['筛选', '合鸣', '重置', '主属性', '确认']:
            match = ctx.ocr(0.4, 0, 1.0, 1.0, match=kw)
            if match:
                return kw
        # Also check if the right panel changed (no longer shows echo detail)
        return None

    # Verify we're on echo page
    header = ctx.ocr(0, 0, 0.25, 0.08)
    h = ''.join(b.get('name', '') for b in (header or []))
    log(f"Header: {h}")
    if '声骸' not in h:
        log("NOT on echo page! Aborting.")
        return {'error': 'not on echo page'}

    # Screenshot before any clicks
    s = ctx.screenshot()
    log(f"Before: {s.get('path', '')}")

    # === Test each candidate position ===
    # OCR found these small items in the bottom bar:
    # [7] at x=0.0263 y=0.9037
    # [A]/[个] at x=0.0557 y=0.9032
    # [Y] at x=0.1151 y=0.9023

    candidates = [
        (0.115, 0.903, "Y_icon (x=0.115)"),
        (0.056, 0.903, "A_icon (x=0.056)"),
        (0.026, 0.903, "7_icon (x=0.026)"),
        # Also try 声骸管理方案 button in header
        (0.490, 0.044, "声骸管理方案 header button"),
        # And the icon that OCR saw as 血/目 at x=0.583
        (0.583, 0.894, "trash_area icon (x=0.583)"),
    ]

    for x, y, desc in candidates:
        log(f"--- Testing: {desc} at ({x}, {y}) ---")
        ctx.click(x, y, after_sleep=1.5)
        time.sleep(0.5)

        # Check if anything filter-like appeared
        kw = check_filter_opened()
        if kw:
            log(f"FOUND! Keyword '{kw}' appeared after clicking {desc}")
            results['filter_entry'] = desc
            results['filter_position'] = {'x': x, 'y': y}
            results['trigger_keyword'] = kw

            # Map the panel that opened
            log("Mapping opened panel...")
            panel = ctx.ocr(0.4, 0, 1.0, 1.0)
            for b in (panel or []):
                print(f"  [{b.get('name','')}] x={b.get('x',0):.4f} y={b.get('y',0):.4f}")

            s = ctx.screenshot()
            results['filter_screenshot'] = s.get('path', '')
            log(f"Filter panel screenshot: {results['filter_screenshot']}")
            return results

        # Check header still says 声骸 (didn't change tab)
        header = ctx.ocr(0, 0, 0.25, 0.08)
        h = ''.join(b.get('name', '') for b in (header or []))
        if '声骸' not in h:
            log(f"WARNING: Tab changed to {h}! Switching back...")
            ctx.click(0.02, 0.30, after_sleep=1.5)
            time.sleep(0.5)

        # Take screenshot to see what happened
        s = ctx.screenshot()
        log(f"After {desc}: {s.get('path', '')}")

    log("No filter entry found from any candidate")
    results['status'] = 'not_found'
    return results
