"""Debug character switching on 属性详情 page.
Diagnose why portrait clicks don't switch characters."""
import time

def execute(ctx):
    task = ctx.executor.onetime_tasks[0]

    # 1. Navigate to character page
    # Detection-based ensure main
    menu_kw = ['终端', '武器', '声骸', '补给', '资源', '设置', '数据坞', '背包', '摩托', '属性', '共鸣者列']
    for _ in range(10):
        top = task.ocr(0, 0, 0.2, 0.08)
        texts = [b.name for b in (top or [])]
        if not any(any(kw in t for kw in menu_kw) for t in texts):
            break
        task.send_key('esc', after_sleep=0.8)
    task.sleep(0.5)
    print("Main world reached")

    # Open ESC menu → click 共鸣者
    task.send_key('esc', after_sleep=2)
    task.wait_click_ocr(0.3, 0.3, 0.7, 0.7, match='共鸣者',
                        raise_if_not_found=True, settle_time=0.5)
    print("共鸣者 clicked, waiting for page load...")
    task.sleep(5)

    # Switch to 属性详情 tab
    task.click_relative(0.015, 0.15, after_sleep=1)

    # Read current character name
    name_ocr = task.ocr(0.10, 0.08, 0.30, 0.16)
    current = [b.name for b in (name_ocr or []) if len(b.name) >= 2 and '属性' not in b.name]
    print(f"Current character: {current}")

    # 2. Test portrait clicks - use COMPILED click_relative
    # Portraits are on the RIGHT side at x ≈ 0.935
    print("\n=== Testing compiled click_relative on portraits ===")
    for py in [0.18, 0.28, 0.38, 0.48, 0.58]:
        task.click_relative(0.935, py, after_sleep=1)
        name_ocr = task.ocr(0.10, 0.08, 0.30, 0.16)
        names = [b.name for b in (name_ocr or []) if len(b.name) >= 2 and '属性' not in b.name]
        print(f"  click_relative(0.935, {py}): {names}")

    # 3. Test using API click (ctx.click) instead
    print("\n=== Testing API ctx.click on portraits ===")
    for py in [0.18, 0.28, 0.38, 0.48, 0.58]:
        ctx.click(0.935, py, after_sleep=1)
        name_ocr = task.ocr(0.10, 0.08, 0.30, 0.16)
        names = [b.name for b in (name_ocr or []) if len(b.name) >= 2 and '属性' not in b.name]
        print(f"  ctx.click(0.935, {py}): {names}")

    # 4. Test using wait_click_ocr on portrait numbers (01, 02, 03)
    print("\n=== Testing wait_click_ocr on portrait labels ===")
    for label in ['01', '02', '03']:
        try:
            task.wait_click_ocr(0.85, 0.1, 1, 0.9, match=label,
                                raise_if_not_found=True, settle_time=0.3)
            task.sleep(1)
            name_ocr = task.ocr(0.10, 0.08, 0.30, 0.16)
            names = [b.name for b in (name_ocr or []) if len(b.name) >= 2 and '属性' not in b.name]
            print(f"  wait_click_ocr('{label}'): {names}")
        except Exception as e:
            print(f"  wait_click_ocr('{label}'): ERROR {e}")

    shot = ctx.screenshot()
    return {'screenshot': shot.get('path', '')}
