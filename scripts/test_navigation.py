"""
Test echo backpack navigation steps individually.
Run via: POST /script/run {"name": "test_navigation"}

Tests each step of SmartEnhanceTask's navigation flow:
1. ESC spam → main world
2. B key → open backpack
3. Click echo tab
4. Click first echo
5. Check for 培养 button
"""

import re
import time


def execute(ctx):
    results = {}

    # Step 1: ESC spam to return to main world
    print("[Step 1] ESC x5 to close menus...")
    for _ in range(5):
        ctx.send_key('esc', after_sleep=0.5)
    time.sleep(0.5)
    results['step1_esc'] = 'done'

    # Take screenshot of current state
    shot = ctx.screenshot()
    results['step1_screenshot'] = shot.get('path', '')

    # Step 2: Open backpack
    print("[Step 2] Press B to open backpack...")
    ctx.send_key('b', after_sleep=2)

    header_ocr = ctx.ocr(0, 0, 0.5, 0.15)
    results['step2_header_ocr'] = [b.get('name', '') for b in header_ocr]
    backpack_open = any(
        any(kw in b.get('name', '') for kw in ['武器', '声骸', '补给', '资源'])
        for b in header_ocr
    )
    results['step2_backpack_open'] = backpack_open

    shot2 = ctx.screenshot()
    results['step2_screenshot'] = shot2.get('path', '')

    if not backpack_open:
        print("[Step 2] FAILED - backpack not detected")
        return results

    # Step 3: Click echo tab (sidebar y=0.30)
    print("[Step 3] Click echo tab at (0.02, 0.30)...")
    ctx.click(0.02, 0.30, after_sleep=1)

    echo_header = ctx.ocr(0, 0, 0.4, 0.12)
    results['step3_header_ocr'] = [b.get('name', '') for b in echo_header]
    echo_tab = any('声骸' in b.get('name', '') for b in echo_header)
    results['step3_echo_tab'] = echo_tab

    if not echo_tab:
        # Try adjacent y positions
        print("[Step 3] Trying adjacent positions...")
        for y in [0.27, 0.32, 0.28, 0.29, 0.31]:
            ctx.click(0.02, y, after_sleep=0.5)
            echo_header = ctx.ocr(0, 0, 0.4, 0.12)
            echo_tab = any('声骸' in b.get('name', '') for b in echo_header)
            if echo_tab:
                results['step3_echo_tab'] = True
                results['step3_working_y'] = y
                break

    shot3 = ctx.screenshot()
    results['step3_screenshot'] = shot3.get('path', '')

    # Step 4: Click first echo in grid
    print("[Step 4] Click first echo at (0.10, 0.22)...")
    ctx.click(0.10, 0.22, after_sleep=1.5)

    shot4 = ctx.screenshot()
    results['step4_screenshot'] = shot4.get('path', '')

    # Step 5: Check for 培养 button
    print("[Step 5] Check for 培养 button...")
    enhance_ocr = ctx.ocr(0.82, 0.86, 0.97, 0.96)
    results['step5_enhance_ocr'] = [b.get('name', '') for b in enhance_ocr]
    enhance_found = any('培养' in b.get('name', '') for b in enhance_ocr)
    results['step5_enhance_found'] = enhance_found

    if not enhance_found:
        # Try adjacent grid positions
        print("[Step 5] 培养 not found, trying adjacent echo positions...")
        for dx, dy in [(0.05, 0), (-0.02, 0), (0, 0.05), (0.05, 0.05)]:
            x, y = 0.10 + dx, 0.22 + dy
            ctx.click(x, y, after_sleep=1.5)
            enhance_ocr = ctx.ocr(0.82, 0.86, 0.97, 0.96)
            enhance_found = any('培养' in b.get('name', '') for b in enhance_ocr)
            if enhance_found:
                results['step5_enhance_found'] = True
                results['step5_working_pos'] = f'({x}, {y})'
                break

    shot5 = ctx.screenshot()
    results['step5_screenshot'] = shot5.get('path', '')

    # Summary
    all_pass = (results.get('step2_backpack_open') and
                results.get('step3_echo_tab') and
                results.get('step5_enhance_found'))
    results['all_pass'] = all_pass
    print(f"\n=== Results: {'ALL PASS' if all_pass else 'SOME FAILED'} ===")
    for k, v in results.items():
        if not k.endswith('_screenshot') and not k.endswith('_ocr'):
            print(f"  {k}: {v}")

    return results
