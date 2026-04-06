"""Explore character page: find echo tab and character selector."""
import time


def execute(ctx):
    results = {}

    # Current state should be character page (属性详情)
    header = ctx.ocr(0, 0, 0.2, 0.08)
    results['current_header'] = [b.get('name', '') for b in header]
    print(f"Current: {results['current_header']}")

    # Scan left sidebar icons by clicking at x=0.025, various y
    # Look for icons below the stats area
    print("\n=== Scanning sidebar tabs ===")
    tab_results = []
    for y in [0.56, 0.58, 0.60, 0.62, 0.64, 0.66, 0.68, 0.70, 0.72]:
        ctx.click(0.025, y, after_sleep=0.8)
        header = ctx.ocr(0, 0, 0.25, 0.08)
        h_text = [b.get('name', '') for b in header]
        print(f"  y={y:.2f}: header={h_text}")
        tab_results.append({'y': y, 'header': h_text})
        if h_text and h_text != results.get('last_header', []):
            results[f'tab_y{y}'] = h_text
            results['last_header'] = h_text

    # Find which y opened 声骸 tab
    echo_y = None
    for t in tab_results:
        if any('声骸' in h for h in t['header']):
            echo_y = t['y']
            break
    results['echo_tab_y'] = echo_y

    # If echo tab found, take screenshot and OCR the equipped echoes
    if echo_y:
        print(f"\n=== Echo tab at y={echo_y} ===")
        ctx.click(0.025, echo_y, after_sleep=1)
        shot = ctx.screenshot()
        results['echo_screenshot'] = shot.get('path', '')

        # OCR the echo page to find set names
        echo_ocr = ctx.ocr(0, 0.1, 0.8, 0.9)
        echo_text = [(b.get('name', ''), round(b.get('x', 0), 3), round(b.get('y', 0), 3))
                     for b in echo_ocr]
        results['echo_page_text'] = echo_text
        print("Echo page OCR:")
        for name, x, y in sorted(echo_text, key=lambda t: (t[2], t[1])):
            print(f"  ({x:.3f}, {y:.3f}) [{name}]")

    # Also check character list - scroll and OCR
    print("\n=== Character portraits (right side) ===")
    char_ocr = ctx.ocr(0.85, 0, 1, 1)
    results['char_list'] = [b.get('name', '') for b in char_ocr]
    print(f"Characters: {results['char_list']}")

    return results
