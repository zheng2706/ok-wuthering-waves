import time

def execute(ctx):
    dm = ctx.device_manager
    cap = dm.capture_method
    interaction = dm.interaction

    print(f"Capture type: {type(cap).__name__}")
    print(f"Capture width: {cap.width}")
    print(f"Capture height: {cap.height}")
    print(f"Interaction type: {type(interaction).__name__}")
    
    # Check hwnd info
    hw = getattr(interaction, 'hwnd_window', None)
    if hw:
        print(f"hwnd: {hw.hwnd}")
        print(f"top_hwnd: {getattr(hw, 'top_hwnd', 'N/A')}")
        print(f"window x,y: {getattr(hw, 'x', 'N/A')}, {getattr(hw, 'y', 'N/A')}")
        print(f"window w,h: {getattr(hw, 'width', 'N/A')}, {getattr(hw, 'height', 'N/A')}")
        # Check get_top_window_cords
        if hasattr(hw, 'get_top_window_cords'):
            tx, ty = hw.get_top_window_cords(100, 100)
            print(f"get_top_window_cords(100,100) = ({tx}, {ty})")
            tx2, ty2 = hw.get_top_window_cords(1920, 1080)
            print(f"get_top_window_cords(1920,1080) = ({tx2}, {ty2})")
    
    # Test: what pixel coord does (0.07, 0.75) map to?
    test_x, test_y = 0.07, 0.75
    abs_x = int(test_x * cap.width)
    abs_y = int(test_y * cap.height)
    print(f"\nRelative ({test_x}, {test_y}) -> pixel ({abs_x}, {abs_y})")
    
    return {"cap_w": cap.width, "cap_h": cap.height, "interaction": type(interaction).__name__}
