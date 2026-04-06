"""Test clicking sidebar with executor already running."""

def execute(ctx):
    import time

    task = ctx.executor.onetime_tasks[0]

    # Click sidebar echo icon using compiled click_relative
    print("Clicking sidebar echo icon at (0.035, 0.35)...")
    task.click_relative(0.035, 0.35, after_sleep=1)
    time.sleep(1)

    # OCR header to check which tab
    boxes = task.ocr(0, 0, 0.25, 0.1)
    header = [b.name for b in (boxes or [])]
    print(f"Header: {header}")
    return {"header": header}
