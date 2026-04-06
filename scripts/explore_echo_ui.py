"""Explore echo backpack UI controls."""

def execute(ctx):
    import time
    task = ctx.executor.onetime_tasks[0]

    # Full OCR using compiled task method
    boxes = task.ocr(0, 0, 1, 1)
    elements = []
    for b in (boxes or []):
        elements.append({"name": b.name, "x": round(b.x, 3), "y": round(b.y, 3)})

    # Try clicking bottom-left icon area
    task.click_relative(0.025, 0.85, after_sleep=1)
    time.sleep(0.5)
    boxes2 = task.ocr(0, 0, 1, 1)
    after_click = [{"name": b.name, "x": round(b.x, 3), "y": round(b.y, 3)} for b in (boxes2 or [])]

    old_names = set(b.name for b in (boxes or []))
    new_names = set(e["name"] for e in after_click) - old_names

    return {
        "initial_elements": elements,
        "after_bottom_click": list(new_names),
        "total_after": len(after_click)
    }
