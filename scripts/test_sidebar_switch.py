"""
Test switching backpack tabs via sidebar clicks.
Uses task.click_relative for compiled interaction.
"""
import time


def execute(ctx):
    results = {}

    # Get a task object for compiled click_relative
    task = ctx.executor.onetime_tasks[0]

    # Take initial screenshot
    s = ctx.screenshot()
    print(f"Initial: {s.get('path','')}")

    # Check current header
    boxes = ctx.ocr(0, 0, 0.20, 0.08)
    header = [b.get('name', '') for b in (boxes or [])]
    print(f"Current header: {header}")

    # Try clicking sidebar with task.click_relative at different positions
    # The sidebar icons in the backpack should be at x ≈ 0.015-0.04
    # Try both ctx.click and task.click_relative

    print("\n=== Testing ctx.click on sidebar ===")
    for x in [0.01, 0.02, 0.03, 0.04]:
        for y in [0.10, 0.15, 0.20, 0.25]:
            ctx.click(x, y, after_sleep=0.5)
            time.sleep(0.3)
            boxes = ctx.ocr(0, 0, 0.20, 0.08)
            h = ''.join(b.get('name', '') for b in (boxes or []))
            if '声骸' in h or '武器' in h or '补给' in h or '资源' in h:
                print(f"  ctx.click({x}, {y}) -> CHANGED: {h}")
                results[f'ctx_{x}_{y}'] = h
                if '声骸' in h:
                    results['echo_found_via_ctx'] = f"{x},{y}"
                    s = ctx.screenshot()
                    results['echo_screenshot'] = s.get('path', '')
                    return results
            # Don't print if still same

    print("\n=== Testing task.click_relative on sidebar ===")
    for x in [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04]:
        for y in [0.10, 0.15, 0.20, 0.25]:
            task.click_relative(x, y, after_sleep=0.5)
            time.sleep(0.3)
            boxes = ctx.ocr(0, 0, 0.20, 0.08)
            h = ''.join(b.get('name', '') for b in (boxes or []))
            if '声骸' in h or '武器' in h or '补给' in h or '资源' in h:
                print(f"  task.click_relative({x}, {y}) -> CHANGED: {h}")
                results[f'task_{x}_{y}'] = h
                if '声骸' in h:
                    results['echo_found_via_task'] = f"{x},{y}"
                    s = ctx.screenshot()
                    results['echo_screenshot'] = s.get('path', '')
                    return results

    # If nothing worked, try clicking header tab text area
    print("\n=== Testing header click ===")
    for x_off in [0.05, 0.06, 0.07, 0.08]:
        ctx.click(x_off, 0.05, after_sleep=0.5)
        time.sleep(0.3)
        boxes = ctx.ocr(0, 0, 0.20, 0.08)
        h = ''.join(b.get('name', '') for b in (boxes or []))
        print(f"  header click ({x_off}, 0.05) -> {h}")

    s = ctx.screenshot()
    results['final_screenshot'] = s.get('path', '')
    results['status'] = 'no_echo_tab_found'
    return results
