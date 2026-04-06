"""Test clicking 共鸣者 from ESC menu."""
import re

def execute(ctx):
    task = ctx.executor.onetime_tasks[0]

    # Detection-based ensure main
    menu_kw = ['终端', '武器', '声骸', '补给', '资源', '设置', '数据坞', '背包', '摩托', '属性']
    for _ in range(10):
        top = task.ocr(0, 0, 0.2, 0.08)
        texts = [b.name for b in (top or [])]
        if not any(any(kw in t for kw in menu_kw) for t in texts):
            break
        task.send_key('esc', after_sleep=0.8)
    task.sleep(0.5)
    print("Main world reached")

    # Open ESC menu
    task.send_key('esc', after_sleep=2)
    top = task.ocr(0, 0, 0.15, 0.08)
    print(f"Menu header: {[b.name for b in (top or [])]}")

    # Click 共鸣者
    print("Clicking 共鸣者...")
    result = task.wait_click_ocr(0.3, 0.3, 0.7, 0.7, match='共鸣者',
                                  raise_if_not_found=True, settle_time=0.5)
    print(f"Click result: {result}")
    task.sleep(2)

    # Check what page opened
    top2 = task.ocr(0, 0, 0.2, 0.08)
    h2 = [b.name for b in (top2 or [])]
    print(f"After click: {h2}")

    shot = ctx.screenshot()
    print(f"Screenshot: {shot.get('path', '')}")
    return {'header_after': h2, 'screenshot': shot.get('path', '')}
