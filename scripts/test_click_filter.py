"""
Try clicking filter icon using task.click_relative (compiled interaction).
Also try all bottom-bar positions systematically.
"""
import time


def execute(ctx):
    task = ctx.executor.onetime_tasks[0]
    results = {}

    # Verify echo page
    boxes = ctx.ocr(0, 0, 0.25, 0.08)
    h = ''.join(b.get('name', '') for b in (boxes or []))
    print(f"Header: {h}")
    if '声骸' not in h:
        return {'error': 'not on echo page'}

    # Try each position with BOTH ctx.click and task.click_relative
    positions = [
        # Bottom bar icons (OCR found as [7], [A], [Y])
        (0.026, 0.904, "icon_7"),
        (0.056, 0.903, "icon_A"),
        (0.115, 0.902, "icon_Y"),
        # Between icons
        (0.08, 0.90, "between_A_Y"),
        (0.10, 0.90, "near_Y_left"),
        (0.13, 0.90, "near_Y_right"),
        # 声骸管理方案 header button
        (0.49, 0.04, "manage_btn"),
        (0.52, 0.04, "manage_btn2"),
    ]

    for x, y, name in positions:
        # Use task.click_relative (compiled PostMessage)
        print(f"\n--- task.click_relative({x}, {y}) [{name}] ---")
        task.click_relative(x, y, after_sleep=1.5)
        time.sleep(0.5)

        # Check for filter panel
        for kw in ['筛选', '合鸣', '重置', '主属性']:
            match = ctx.ocr(0.3, 0, 1.0, 1.0, match=kw)
            if match:
                print(f"  FOUND '{kw}'!")
                results['found'] = name
                results['position'] = (x, y)
                s = ctx.screenshot()
                results['screenshot'] = s.get('path', '')
                print(f"  Screenshot: {results['screenshot']}")
                return results

        # Check header still valid
        boxes = ctx.ocr(0, 0, 0.25, 0.08)
        h = ''.join(b.get('name', '') for b in (boxes or []))
        if '声骸' not in h:
            print(f"  Tab changed! Switching back...")
            ctx.click(0.02, 0.30, after_sleep=1.5)

    print("\n=== No filter found with task.click_relative ===")

    # Last resort: try 等级顺序 and 批量管理 with task.click_relative
    print("\n--- Trying 等级顺序 center ---")
    task.click_relative(0.207, 0.911, after_sleep=1.5)
    s = ctx.screenshot()
    print(f"Screenshot: {s.get('path', '')}")

    print("\n--- Trying 批量管理 center ---")
    task.click_relative(0.429, 0.910, after_sleep=1.5)
    s = ctx.screenshot()
    print(f"Screenshot: {s.get('path', '')}")

    results['status'] = 'not_found'
    s = ctx.screenshot()
    results['final_screenshot'] = s.get('path', '')
    return results
