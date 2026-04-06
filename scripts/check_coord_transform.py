"""Diagnose coordinate transformation in PostMessageInteraction."""

def execute(ctx):
    dm = ctx.device_manager
    interaction = dm.interaction
    hw = interaction.hwnd_window
    cap = dm.capture_method

    print(f"Capture: {cap.width}x{cap.height}")
    print(f"Interaction: {type(interaction).__name__}")
    print(f"hwnd: {hw.hwnd}, top_hwnd: {getattr(hw, 'top_hwnd', 'N/A')}")
    print(f"Window: x={getattr(hw, 'x', '?')}, y={getattr(hw, 'y', '?')}, "
          f"w={getattr(hw, 'width', '?')}, h={getattr(hw, 'height', '?')}")

    # Test get_top_window_cords if available
    if hasattr(hw, 'get_top_window_cords'):
        test_points = [
            (0, 0), (100, 100), (500, 500),
            (1920, 1080), (3840, 2160),
            # The filter icon area: relative (0.115, 0.90) -> pixel (441, 1944)
            (441, 1944),
            # Grid echo: relative (0.167, 0.165) -> pixel (641, 356)
            (641, 356),
            # Grid echo: relative (0.60, 0.165) -> pixel (2304, 356)
            (2304, 356),
        ]
        print(f"\n=== get_top_window_cords transformation ===")
        for px, py in test_points:
            tx, ty = hw.get_top_window_cords(px, py)
            print(f"  ({px:5d}, {py:5d}) -> ({tx:5d}, {ty:5d})  delta=({tx-px:+5d}, {ty-py:+5d})")
    else:
        print("get_top_window_cords NOT available")

    # Also check if there's a frame offset
    for attr in ['x', 'y', 'width', 'height', 'real_x', 'real_y',
                 'real_width', 'real_height', 'frame_width', 'frame_height',
                 'border_left', 'border_top', 'title_height']:
        val = getattr(hw, attr, 'N/A')
        if val != 'N/A':
            print(f"  hw.{attr} = {val}")

    results = {}
    if hasattr(hw, 'get_top_window_cords'):
        for px, py in [(0,0),(100,100),(641,356),(2304,356),(441,1944),(1920,1080)]:
            tx, ty = hw.get_top_window_cords(px, py)
            results[f'{px},{py}'] = f'{tx},{ty} (d={tx-px},{ty-py})'

    for attr in ['x','y','width','height','real_x','real_y','real_width','real_height',
                 'border_left','border_top','title_height','frame_width','frame_height']:
        val = getattr(hw, attr, None)
        if val is not None:
            results[f'hw.{attr}'] = val

    results['cap'] = f'{cap.width}x{cap.height}'
    results['interaction'] = type(interaction).__name__
    return results
