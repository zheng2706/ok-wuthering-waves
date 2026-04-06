"""
End-to-end test for SmartEnhanceTask flow (DPI-aware version).
Usage: POST /script/run {"name": "test_full_flow"}
Prerequisite: Game open, character in main world.
"""
import re
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
        results[f'{label}_screenshot'] = s.get('path', '')

    # ===== Step 1: Connection =====
    log("Checking connection...")
    status = ctx.get_status()
    results['connected'] = status.get('connected', False)
    results['resolution'] = status.get('resolution', '')
    if not status.get('connected'):
        return results
    log(f"OK: {status['resolution']} via {status['capture_method']}")

    # ===== Step 2: Return to main world (detection-based) =====
    log("Returning to main world...")
    menu_kw = ['终端', '武器', '声骸', '补给', '资源', '设置', '数据坞', '背包', '摩托']
    for attempt in range(10):
        top = ctx.ocr(0, 0, 0.2, 0.08)
        texts = [b.get('name', '') for b in top]
        in_menu = any(any(kw in t for kw in menu_kw) for t in texts)
        if not in_menu:
            dialog = ctx.ocr(0.2, 0.3, 0.8, 0.7, match='弃置')
            if not dialog:
                break
        ctx.send_key('esc', after_sleep=0.8)
    time.sleep(0.5)
    log("Main world reached")

    # ===== Step 3: Open backpack =====
    log("Press B to open backpack...")
    ctx.send_key('b', after_sleep=2)

    # Check for popup and dismiss
    popup = ctx.ocr(0.2, 0.3, 0.8, 0.8, match='弃置')
    results['echo_warning'] = bool(popup)
    if popup:
        log("Echo warning popup detected, ESC...")
        ctx.send_key('esc', after_sleep=1)

    # Verify backpack
    header = ctx.ocr(0, 0, 0.15, 0.08)
    header_text = [b.get('name', '') for b in header]
    backpack_open = any('声骸' in t for t in header_text)
    results['backpack_open'] = backpack_open
    results['backpack_header'] = header_text
    log(f"Backpack: {'OPEN' if backpack_open else 'FAIL'} - {header_text}")
    shot('backpack')

    if not backpack_open:
        return results

    # ===== Step 4: Check 培养 button =====
    log("Checking 培养 button (first echo auto-selected)...")
    enhance = ctx.ocr(0.82, 0.86, 0.97, 0.96)
    enhance_text = [b.get('name', '') for b in enhance]
    enhance_found = any('培养' in t for t in enhance_text)
    results['enhance_found'] = enhance_found
    log(f"培养 button: {'FOUND' if enhance_found else 'NOT FOUND'} - {enhance_text}")
    shot('enhance')

    if enhance_found:
        # ===== Step 5: Check echo detail panel =====
        log("Reading echo detail panel...")
        detail = ctx.ocr(0.65, 0.05, 1.0, 0.85)
        detail_text = [(b.get('name', ''), round(b.get('y', 0), 3)) for b in detail]
        results['detail_panel'] = detail_text
        for name, y in detail_text[:10]:
            log(f"  y={y:.3f} [{name}]")

        # Check level 0 indicator
        level = ctx.ocr(0.65, 0.4, 0.85, 0.55)
        level_text = [b.get('name', '') for b in level]
        is_level_0 = any('声骸技能' in t for t in level_text)
        results['is_level_0'] = is_level_0
        log(f"Level 0: {'YES' if is_level_0 else 'NO'} - {level_text}")

    # ===== Summary =====
    all_pass = (results.get('connected') and
                results.get('backpack_open') and
                results.get('enhance_found'))
    results['all_pass'] = all_pass

    log("")
    log(f"========= {'ALL PASS' if all_pass else 'FAILED'} =========")
    log(f"  Resolution:   {results.get('resolution')}")
    log(f"  Backpack:     {results.get('backpack_open')}")
    log(f"  Warning:      {results.get('echo_warning')}")
    log(f"  培养 button:  {results.get('enhance_found')}")
    log(f"  Level 0:      {results.get('is_level_0', 'N/A')}")

    # ESC back to main world
    ctx.send_key('esc', after_sleep=0.5)
    ctx.send_key('esc', after_sleep=0.5)

    return results
