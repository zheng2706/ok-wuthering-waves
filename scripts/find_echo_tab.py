"""Find echo tab position by clicking and checking header."""

def execute(ctx):
    task = ctx.executor.onetime_tasks[0]
    import time

    # Open backpack
    task.send_key('b', after_sleep=2)
    task.sleep(1)

    # Check initial tab
    boxes = task.ocr(0, 0, 600, 200)
    current = next((b.name for b in (boxes or []) if len(b.name) > 3), '?')

    transitions = [{"pos": "initial", "tab": current}]
    prev = current

    # Scan key positions with x=0.02 (confirmed working from earlier)
    for y in [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]:
        task.click_relative(0.02, y, after_sleep=0.4)
        task.sleep(0.2)
        boxes = task.ocr(0, 0, 600, 200)
        tab = next((b.name for b in (boxes or []) if len(b.name) > 3), '?')
        if tab != prev:
            transitions.append({"pos": f"0.02,{y}", "tab": tab})
            prev = tab

    return transitions
