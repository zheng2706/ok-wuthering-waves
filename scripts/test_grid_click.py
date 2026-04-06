"""Test clicking echo grid items via compiled task method."""

def execute(ctx):
    import time
    task = ctx.executor.onetime_tasks[0]

    results = {}

    # Current state - should be in echo backpack
    header = task.ocr(0, 0, 0.4, 0.12)
    header_text = [b.name for b in (header or [])]
    results['current_header'] = header_text

    # Try clicking different grid positions using compiled click_relative
    positions = [
        (0.12, 0.20, "center"),
        (0.12, 0.17, "top"),
        (0.12, 0.24, "bottom"),
        (0.09, 0.20, "left"),
        (0.15, 0.20, "right"),
        (0.12, 0.15, "very_top"),
        (0.18, 0.20, "col2_left"),
    ]

    for x, y, label in positions:
        task.click_relative(x, y, after_sleep=1)
        task.sleep(0.5)

        # Check for enhance button
        enhance = task.ocr(0.82, 0.86, 0.97, 0.96, match='培养')
        # Also check right panel for any echo detail text
        right_panel = task.ocr(0.6, 0.1, 1.0, 0.5)
        right_text = [b.name for b in (right_panel or [])]

        results[f'pos_{label}'] = {
            'x': x, 'y': y,
            'enhance': bool(enhance),
            'right_panel': right_text[:5],
        }
        print(f"  ({x}, {y}) [{label}]: enhance={bool(enhance)}, right={right_text[:3]}")

        if enhance:
            results['working_position'] = (x, y)
            print(f"  >>> FOUND at ({x}, {y})!")
            # Take screenshot
            shot = ctx.screenshot()
            results['detail_screenshot'] = shot.get('path', '')
            # ESC back
            task.send_key('esc', after_sleep=1)
            break

    return results
