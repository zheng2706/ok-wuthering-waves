"""Test ESC menu navigation using compiled task methods (same as FiveToOneTask)."""

def execute(ctx):
    import time
    task = ctx.executor.onetime_tasks[0]
    results = {}

    # Step 1: Close any menus and return to main world
    print("[1] Return to main world...")
    for _ in range(4):
        task.send_key('esc', after_sleep=0.5)
    task.sleep(0.5)

    # Verify main world (no menu headers)
    top = task.ocr(0, 0, 0.3, 0.1)
    texts = [b.name for b in (top or [])]
    print(f"    Top text: {texts}")
    if any('终端' in t for t in texts):
        task.send_key('esc', after_sleep=0.5)

    # Step 2: Open ESC menu (same as BaseWWTask.open_esc_menu)
    print("[2] Opening ESC menu (ALT + click 0.95, 0.04)...")
    task.send_key_down('alt')
    task.sleep(0.05)
    task.click_relative(0.95, 0.04)
    task.send_key_up('alt')
    task.sleep(1)

    # Check what opened
    top = task.ocr(0, 0, 0.3, 0.1)
    texts = [b.name for b in (top or [])]
    results['after_open'] = texts
    print(f"    Header: {texts}")

    # Step 3: Full OCR of the menu
    print("[3] Full menu OCR...")
    full = task.ocr(0, 0, 1, 1)
    all_text = [(b.name, round(b.x + b.width / 2, 3), round(b.y + b.height / 2, 3))
                for b in (full or [])]
    for name, cx, cy in sorted(all_text, key=lambda t: (t[2], t[1])):
        print(f"    ({cx:.3f}, {cy:.3f}) [{name}]")
    results['menu_items'] = all_text

    # Step 4: Try clicking 共鸣者 using wait_click_ocr (same as FiveToOneTask)
    print("[4] Attempting wait_click_ocr('共鸣者')...")
    try:
        result = task.wait_click_ocr(0.5, 0.5, 1, 1, match='共鸣者', raise_if_not_found=True, settle_time=0.5)
        results['click_result'] = str(result)
        print(f"    Click result: {result}")
    except Exception as e:
        results['click_error'] = str(e)
        print(f"    Error: {e}")

    task.sleep(2)

    # Check what opened after click
    top = task.ocr(0, 0, 0.3, 0.15)
    texts = [b.name for b in (top or [])]
    results['after_click_header'] = texts
    print(f"[5] After click header: {texts}")

    # Screenshot
    shot = ctx.screenshot()
    results['screenshot'] = shot.get('path', '')

    return results
