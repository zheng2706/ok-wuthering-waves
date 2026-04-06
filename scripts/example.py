"""
Example script: takes a screenshot and runs OCR on the full screen.
"""


def execute(ctx):
    # Take screenshot
    result = ctx.screenshot()
    print(f"Screenshot saved to: {result.get('path')}")

    # Run OCR on full screen
    boxes = ctx.ocr(0, 0, 1, 1)
    print(f"OCR found {len(boxes)} text regions:")
    for box in boxes[:10]:
        print(f"  [{box['name']}] at ({box['x']}, {box['y']})")

    return {"screenshot": result.get('path'), "ocr_count": len(boxes)}
