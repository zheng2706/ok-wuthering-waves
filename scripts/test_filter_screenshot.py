"""Apply filter with SmartEnhanceTask's actual conditions and take screenshots."""
import time


def execute(ctx):
    results = {}

    # Navigate to echo backpack
    for _ in range(5):
        ctx.send_key('esc', after_sleep=0.7)
    time.sleep(1)
    ctx.send_key('b', after_sleep=3)
    ctx.send_key('esc', after_sleep=1)
    ctx.click(0.02, 0.30, after_sleep=2)

    # Open filter panel
    ctx.dbl_click(0.115, 0.900, after_sleep=2)

    # Open dropdown and select 荣斗铸锋之冠
    ctx.real_click(0.85, 0.454, after_sleep=2)

    # Scroll to find 荣斗铸锋之冠
    for i in range(10):
        match = ctx.ocr(0.6, 0.4, 1.0, 0.95, match='荣斗')
        if match:
            b = match[0] if isinstance(match, list) else match
            ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                           b.get('y',0)+b.get('height',0)/2, after_sleep=2)
            break
        ctx.real_click(0.85, 0.65, after_sleep=0.2)  # Position cursor in dropdown
        time.sleep(0.1)
        import ctypes
        ctypes.windll.user32.mouse_event(0x0800, 0, 0, -5 * 120, 0)  # scroll down
        time.sleep(1)

    # Click 添加主属性筛选 +
    add = ctx.ocr(0.6, 0.5, 1.0, 0.65, match='添加')
    if add:
        b = add[0] if isinstance(add, list) else add
        ctx.real_click(b.get('x',0)+b.get('width',0)+0.02,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)

    # Select Cost4 (should be default/first tab)
    c4 = ctx.ocr(0, 0, 1.0, 0.5, match='Cost4')
    if c4:
        b = c4[0] if isinstance(c4, list) else c4
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)

    # Select 暴击伤害
    stat = ctx.ocr(0, 0.2, 1.0, 0.7, match='暴击伤害')
    if stat:
        b = stat[0] if isinstance(stat, list) else stat
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)

    # Screenshot BEFORE confirm (showing conditions)
    s = ctx.screenshot()
    results['conditions'] = s.get('path', '')

    # Confirm
    confirm = ctx.ocr(0.3, 0.7, 1.0, 1.0, match='确认')
    if confirm:
        b = confirm[0] if isinstance(confirm, list) else confirm
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=2)

    # Screenshot AFTER confirm (showing filtered results)
    s = ctx.screenshot()
    results['result'] = s.get('path', '')

    # Reset
    reset = ctx.ocr(0.6, 0.8, 1.0, 0.92, match='重置')
    if reset:
        b = reset[0] if isinstance(reset, list) else reset
        ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                       b.get('y',0)+b.get('height',0)/2, after_sleep=1)

    ctx.dbl_click(0.115, 0.900, after_sleep=1)
    return results
