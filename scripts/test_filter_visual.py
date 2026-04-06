"""
Click bottom-bar icon candidates ONE AT A TIME.
Take screenshot BEFORE and AFTER each click for visual comparison.
No OCR-based detection - just screenshots.
"""
import time


def execute(ctx):
    results = {}

    # Screenshot before any clicks
    s = ctx.screenshot()
    results['before'] = s.get('path', '')
    print(f"BEFORE: {results['before']}")

    # Candidates: bottom bar icons + 等级顺序 + 声骸管理方案
    # Based on OCR: [Y] at (0.1151, 0.9023), [A/个] at (0.0557, 0.9032)
    # 等级顺序 center at (0.207, 0.911)
    candidates = [
        (0.115, 0.900, "Y_icon"),
        (0.115, 0.895, "Y_icon_higher"),
        (0.090, 0.900, "between_A_Y"),
        (0.056, 0.900, "A_icon"),
        (0.140, 0.900, "right_of_Y"),
        (0.207, 0.911, "等级顺序_center"),
    ]

    for i, (x, y, name) in enumerate(candidates):
        print(f"\n=== [{i+1}] Click {name} at ({x}, {y}) ===")
        ctx.click(x, y, after_sleep=2)
        time.sleep(0.5)
        s = ctx.screenshot()
        path = s.get('path', '')
        results[f'after_{name}'] = path
        print(f"  Screenshot: {path}")

        # Quick check: did something visually change?
        # If a panel opened, there should be new text in right area
        check = ctx.ocr(0.3, 0.05, 0.95, 0.95)
        texts = [b.get('name', '') for b in (check or [])]
        interesting = [t for t in texts if any(kw in t for kw in ['筛选','合鸣','重置','主属性','确认','排序','费用'])]
        if interesting:
            print(f"  INTERESTING TEXT: {interesting}")
            results['found'] = name
            return results

        # Press ESC to close any panel that might have opened
        # (in case the panel opened but we didn't detect it)
        # Actually, DON'T press ESC - just check visually later

    return results
