"""
ok-ww framework initialization and context wrapper.
Initializes the ok-ww framework without GUI, providing API access to all game operations.
"""

import os
import sys
import time
import threading
import importlib
import logging
import ctypes

# CRITICAL: Set DPI awareness BEFORE any window operations.
# Without this, GetClientRect returns scaled logical pixels instead of
# physical pixels, causing PrintWindowCapture to only capture a portion.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import numpy as np

PROJECT_DIR = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))

# Working dir = project root (same directory as server.py, config.py, src/, ok/)
os.chdir(PROJECT_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from ok import og, ExitEvent, GlobalConfig, TaskExecutor
from ok.feature.FeatureSet import FeatureSet
from ok.device.DeviceManager import DeviceManager
from config import config as app_config

logger = logging.getLogger("ww_api")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")


class PrintWindowCapture:
    """Capture method using Win32 PrintWindow API.
    Replaces WGC to avoid COM thread affinity / memory issues in HTTP server.
    Works for background/unfocused windows via PW_RENDERFULLCONTENT.
    """

    def __init__(self, hwnd_window, exit_event=None):
        self.hwnd_window = hwnd_window
        self.exit_event = exit_event
        self._width = 0
        self._height = 0
        self._size = (0, 0)
        self.name = "PrintWindowCapture"
        self.description = "PrintWindow background capture"
        self._lock = threading.Lock()
        self._measure()

    def _get_hwnd(self):
        """Get the game window handle."""
        import win32gui
        if self.hwnd_window:
            hwnd = getattr(self.hwnd_window, 'hwnd', 0)
            if hwnd and win32gui.IsWindow(hwnd):
                return hwnd
        # Fallback: find by class name directly
        hwnd = win32gui.FindWindow('UnrealWindow', None)
        return hwnd or 0

    def _measure(self):
        """Measure window client area size."""
        import win32gui
        hwnd = self._get_hwnd()
        if hwnd:
            try:
                rect = win32gui.GetClientRect(hwnd)
                self._width = rect[2]
                self._height = rect[3]
                self._size = (self._width, self._height)
            except Exception:
                pass

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def connected(self):
        import win32gui
        hwnd = self._get_hwnd()
        return bool(hwnd and win32gui.IsWindow(hwnd))

    def close(self):
        pass

    def get_frame(self):
        return self.do_get_frame()

    def do_get_frame(self):
        import win32gui
        import win32ui

        with self._lock:
            hwnd = self._get_hwnd()
            if not hwnd:
                return None
            try:
                rect = win32gui.GetClientRect(hwnd)
                w, h = rect[2], rect[3]
                if w == 0 or h == 0:
                    return None

                self._width = w
                self._height = h
                self._size = (w, h)

                hwndDC = win32gui.GetDC(hwnd)
                mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                saveDC = mfcDC.CreateCompatibleDC()
                saveBitMap = win32ui.CreateBitmap()
                saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
                saveDC.SelectObject(saveBitMap)

                # PW_RENDERFULLCONTENT = 3: captures DirectX/composited content
                ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

                bmpstr = saveBitMap.GetBitmapBits(True)
                frame = np.frombuffer(bmpstr, dtype='uint8').copy()
                frame = frame.reshape((h, w, 4))[:, :, :3]  # BGRA → BGR

                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwndDC)

                return frame
            except Exception as e:
                logger.error(f"PrintWindow capture failed: {e}")
                return None

    def clickable(self):
        return True

    def measure_if_0(self):
        if self._width == 0 or self._height == 0:
            self._measure()

    def draw_rectangle(self):
        pass

    def get_name(self):
        return self.name

    def get_abs_cords(self, x, y):
        """Convert window-local coords to screen coords."""
        import win32gui
        hwnd = self._get_hwnd()
        if hwnd:
            try:
                return win32gui.ClientToScreen(hwnd, (int(x), int(y)))
            except Exception:
                pass
        return (int(x), int(y))


class WWContext:
    """Wraps ok-ww framework, exposing all game interaction capabilities."""

    def __init__(self, ok_instance=None):
        self._ok = ok_instance
        self.exit_event = None
        self.global_config = None
        self.device_manager = None
        self.feature_set = None
        self.executor = None
        self.scene = None
        self._task_thread = None
        self._current_task = None
        self._initialized = False
        self._lock = threading.Lock()

    def initialize(self):
        """Initialize the ok-ww framework (call once at startup)."""
        if self._ok:
            # Use OK instance's pre-initialized components (same as GUI)
            self.executor = self._ok.task_executor
            self.device_manager = self._ok.device_manager
            self.exit_event = self._ok.exit_event
            self.feature_set = self._ok.feature_set
            self.global_config = self._ok.global_config
            # Connect to game (same as GUI's RefreshAdb thread)
            self._connect_device()
            # Disable onetime tasks, start executor loop
            for t in self.executor.onetime_tasks:
                t.disable()
            self.executor.start()
            self._initialized = True
            logger.info(f"=== OK instance ready, capture={type(self.device_manager.capture_method).__name__} ===")
            return
        logger.info("Initializing ok-ww framework...")

        # 1. ExitEvent
        self.exit_event = ExitEvent()

        # 2. GlobalConfig
        self.global_config = GlobalConfig(app_config.get('global_configs', []))
        logger.info(f"GlobalConfig created: {list(self.global_config.configs.keys())}")

        # 3. Populate og singleton
        og.config = app_config
        og.global_config = self.global_config

        # 4. DeviceManager
        self.device_manager = DeviceManager(app_config, self.exit_event, self.global_config)
        og.device_manager = self.device_manager
        logger.info("DeviceManager created")

        # 5. FeatureSet
        tm = app_config.get('template_matching', {})
        self.feature_set = FeatureSet(
            'assets',
            tm.get('coco_feature_json', 'assets/coco_detection.json'),
            tm.get('default_horizontal_variance', 0.002),
            tm.get('default_vertical_variance', 0.002),
            tm.get('default_threshold', 0.8),
            tm.get('feature_processor'),
            tm.get('vcenter_features', []),
            tm.get('hcenter_features', [])
        )
        logger.info("FeatureSet created")

        # 6. TaskExecutor
        self.executor = TaskExecutor(
            device_manager=self.device_manager,
            exit_event=self.exit_event,
            feature_set=self.feature_set,
            ocr_lib=app_config.get('ocr'),
            config_folder=app_config.get('config_folder', 'configs'),
            debug=app_config.get('debug', False),
            global_config=self.global_config,
            config=app_config
        )
        og.executor = self.executor
        logger.info("TaskExecutor created")

        # 7. Initialize my_app (src.globals.Globals - YOLO model manager)
        my_app_config = app_config.get('my_app')
        if my_app_config:
            module_name, class_name = my_app_config
            mod = importlib.import_module(module_name)
            og.my_app = getattr(mod, class_name)(exit_event=self.exit_event)
            logger.info(f"my_app initialized: {module_name}.{class_name}")

        # 8. Initialize scene
        scene_config = app_config.get('scene')
        if scene_config:
            module_name, class_name = scene_config
            mod = importlib.import_module(module_name)
            self.scene = getattr(mod, class_name)()
            logger.info(f"Scene initialized: {module_name}.{class_name}")

        # 9. Load and register tasks
        self._load_tasks()

        # 10. Connect to game
        self._connect_device()

        # 11. Start executor frame loop (needed for compiled task methods)
        # Disable onetime tasks to prevent auto-execution, but keep trigger tasks
        # enabled - they run in background and are essential for combat state tracking
        # (AutoCombatTask updates scene.in_combat, without which sleep_check fails)
        for t in self.executor.onetime_tasks:
            t.disable()
        self.executor.start()
        logger.info("Executor started (onetime tasks disabled, trigger tasks active)")

        self._initialized = True
        logger.info("=== ok-ww framework initialized ===")

    def _connect_device(self):
        """Find game window and establish capture + interaction."""
        self.device_manager.update_pc_device()
        devices = self.device_manager.get_devices()
        connected = any(d.get('connected') for d in devices)
        if connected:
            self.device_manager.do_start()
            # Use framework's default capture (WGC/BitBlt) for reliable combat detection.
            # PrintWindowCapture was causing intermittent in_combat() detection failures
            # during scene transitions (teleport, entering combat).
            logger.info(f"Connected to game: capture={type(self.device_manager.capture_method).__name__}")
        else:
            logger.warning("Game window not found. Use /refresh when game is running.")

    def _stop_hwnd_thread(self):
        """Stop HwndWindow background monitoring thread."""
        hw = self.device_manager.hwnd_window
        if hw and hasattr(hw, 'stop_event'):
            hw.stop_event.set()
            if hasattr(hw, 'thread') and hw.thread:
                hw.thread.join(timeout=2)
            logger.info("Stopped HwndWindow monitoring thread")

    def _setup_printwindow_capture(self):
        """Replace capture method with PrintWindowCapture."""
        hw = self.device_manager.hwnd_window
        if hw:
            pw_cap = PrintWindowCapture(hw, self.exit_event)
            if pw_cap.connected():
                # Close old WGC capture
                old_cap = self.device_manager.capture_method
                if old_cap:
                    try:
                        old_cap.close()
                    except Exception:
                        pass
                self.device_manager.capture_method = pw_cap
                # Update interaction's capture reference
                if self.device_manager.interaction:
                    self.device_manager.interaction.capture = pw_cap
                logger.info(f"PrintWindowCapture active: {pw_cap.width}x{pw_cap.height}")
            else:
                logger.warning("PrintWindowCapture: game window not found")

    def refresh_connection(self):
        """Retry connecting to the game window."""
        self._stop_hwnd_thread()
        self.device_manager.update_pc_device()
        self.device_manager.do_start()
        self._setup_printwindow_capture()
        self._stop_hwnd_thread()
        devices = self.device_manager.get_devices()
        return any(d.get('connected') for d in devices)

    def _load_tasks(self):
        """Import and register all tasks from config."""
        for task_list_name in ['onetime_tasks', 'trigger_tasks']:
            task_defs = app_config.get(task_list_name, [])
            for module_path, class_name in task_defs:
                try:
                    mod = importlib.import_module(module_path)
                    task_cls = getattr(mod, class_name)
                    task = task_cls(self.executor, self.scene)
                    task.after_init(self.executor, self.scene)
                    if task_list_name == 'onetime_tasks':
                        self.executor.onetime_tasks.append(task)
                    else:
                        self.executor.trigger_tasks.append(task)
                    logger.info(f"Loaded task: {class_name}")
                except Exception as e:
                    logger.error(f"Failed to load task {class_name}: {e}")

        # SmartEnhanceTask is registered in config.py,
        # loaded automatically via the task_defs loop above.

    # ===== Helpers =====

    def _get_frame(self):
        """Get frame from the current capture method."""
        cap = self.device_manager.capture_method
        if cap:
            return cap.get_frame()
        return None

    # ===== Low-level API =====

    def get_status(self):
        """Get current connection status."""
        devices = self.device_manager.get_devices()
        pc = next((d for d in devices if d.get('device') == 'windows'), {})
        return {
            "connected": pc.get('connected', False),
            "resolution": pc.get('resolution', ''),
            "nick": pc.get('nick', ''),
            "capture_method": str(type(self.device_manager.capture_method).__name__) if self.device_manager.capture_method else None,
            "initialized": self._initialized,
        }

    def screenshot(self, x=0, y=0, to_x=1, to_y=1):
        """Capture screenshot, optionally crop to region. Returns saved file path."""
        import cv2
        import numpy as np

        logger.info("screenshot: getting frame...")
        frame = self._get_frame()
        logger.info(f"screenshot: frame={'OK '+str(frame.shape) if frame is not None else 'None'}")
        if frame is None:
            return {"error": "No frame captured. Is the game running?"}

        # Crop to region if specified
        if not (x == 0 and y == 0 and to_x == 1 and to_y == 1):
            h, w = frame.shape[:2]
            x1, y1 = int(x * w), int(y * h)
            x2, y2 = int(to_x * w), int(to_y * h)
            frame = frame[y1:y2, x1:x2]

        # Save to output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filename = f"{int(time.time() * 1000)}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        cv2.imwrite(filepath, frame)
        return {"path": filepath, "shape": list(frame.shape)}

    def _get_task_helper(self):
        """Get a task instance for find_feature methods (lives on BaseTask, not TaskExecutor)."""
        if self.executor.onetime_tasks:
            return self.executor.onetime_tasks[0]
        return None

    def _ensure_ocr(self):
        """Lazily initialize the OCR engine."""
        if not hasattr(self, '_ocr_engine') or self._ocr_engine is None:
            from onnxocr.onnx_paddleocr import ONNXPaddleOcr
            ocr_config = app_config.get('ocr', {}).get('params', {})
            self._ocr_engine = ONNXPaddleOcr(**ocr_config)
            logger.info("OCR engine initialized (ONNXPaddleOcr)")
        return self._ocr_engine

    def ocr(self, x=0, y=0, to_x=1, to_y=1, match=None):
        """Run OCR on a screen region using onnxocr directly."""
        import re

        frame = self._get_frame()
        if frame is None:
            return []

        # Crop to region
        h, w = frame.shape[:2]
        x1, y1 = int(x * w), int(y * h)
        x2, y2 = int(to_x * w), int(to_y * h)
        if not (x1 == 0 and y1 == 0 and x2 == w and y2 == h):
            frame = frame[y1:y2, x1:x2]

        ocr_engine = self._ensure_ocr()
        result = ocr_engine.ocr(frame)

        boxes = []
        if result and result[0]:
            for line in result[0]:
                coords, (text, confidence) = line
                # coords is [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                bx = min(c[0] for c in coords)
                by = min(c[1] for c in coords)
                bw = max(c[0] for c in coords) - bx
                bh = max(c[1] for c in coords) - by
                # Convert back to full-frame relative coords
                boxes.append({
                    "name": text,
                    "x": (bx + x1) / w,
                    "y": (by + y1) / h,
                    "width": bw / w,
                    "height": bh / h,
                    "confidence": float(confidence),
                })

        # Filter by match pattern if specified
        if match and boxes:
            if isinstance(match, str):
                boxes = [b for b in boxes if match in b["name"]]
            elif isinstance(match, list):
                patterns = [re.compile(m) if m.startswith('^') or m.startswith('(') else None for m in match]
                def matches(name):
                    for i, m in enumerate(match):
                        if patterns[i] and patterns[i].search(name):
                            return True
                        elif not patterns[i] and m in name:
                            return True
                    return False
                boxes = [b for b in boxes if matches(b["name"])]

        return boxes

    def click(self, x, y, after_sleep=0):
        """Click at relative coordinates (0-1). Converts to absolute pixel coords."""
        interaction = self.device_manager.interaction
        if not interaction:
            return False
        cap = self.device_manager.capture_method
        if cap and cap.width > 0 and cap.height > 0:
            abs_x = int(x * cap.width)
            abs_y = int(y * cap.height)
        else:
            abs_x, abs_y = int(x), int(y)
        interaction.click(abs_x, abs_y)
        if after_sleep > 0:
            time.sleep(after_sleep)
        return True

    def real_click(self, x, y, after_sleep=0):
        """Click using real OS mouse input (SetCursorPos + mouse_event).
        Required for UI elements that don't respond to PostMessage (e.g., dropdowns).
        Brings game window to foreground first."""
        import ctypes
        import win32gui
        interaction = self.device_manager.interaction
        if not interaction:
            return False
        cap = self.device_manager.capture_method
        if cap and cap.width > 0 and cap.height > 0:
            px = int(x * cap.width)
            py = int(y * cap.height)
        else:
            px, py = int(x), int(y)
        hwnd = interaction.hwnd_window.hwnd
        screen_x, screen_y = win32gui.ClientToScreen(hwnd, (px, py))
        try:
            interaction.hwnd_window.bring_to_front()
        except Exception:
            try:
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass
        time.sleep(0.2)
        ctypes.windll.user32.SetCursorPos(screen_x, screen_y)
        time.sleep(0.1)
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
        if after_sleep > 0:
            time.sleep(after_sleep)
        return True

    def real_scroll(self, x, y, clicks=-3):
        """Scroll using real OS mouse input. Required for dropdowns."""
        import ctypes
        import win32gui
        cap = self.device_manager.capture_method
        interaction = self.device_manager.interaction
        if not interaction:
            return False
        hwnd = interaction.hwnd_window.hwnd
        px, py = int(x * cap.width), int(y * cap.height)
        screen_x, screen_y = win32gui.ClientToScreen(hwnd, (px, py))
        try:
            interaction.hwnd_window.bring_to_front()
        except Exception:
            try:
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass
        time.sleep(0.2)
        ctypes.windll.user32.SetCursorPos(screen_x, screen_y)
        time.sleep(0.1)
        ctypes.windll.user32.mouse_event(0x0800, 0, 0, clicks * 120, 0)
        return True

    def dbl_click(self, x, y, after_sleep=0):
        """Double-click via PostMessage. Required for funnel icon etc."""
        self.click(x, y, after_sleep=0.1)
        self.click(x, y, after_sleep=after_sleep)

    # Common key aliases → names used by PostMessageInteraction's vk_key_dict
    KEY_ALIASES = {
        'escape': 'esc', 'return': 'enter', 'spacebar': 'space',
        'ctrl': 'control', 'lctrl': 'lcontrol', 'rctrl': 'rcontrol',
        'pageup': 'pageup', 'pagedown': 'pagedown',
    }

    def send_key(self, key, after_sleep=0, down_time=0.02):
        """Send keyboard key via PostMessage."""
        interaction = self.device_manager.interaction
        if not interaction:
            return False
        # Normalize key aliases
        normalized = self.KEY_ALIASES.get(str(key).lower(), str(key))
        interaction.send_key(normalized, down_time)
        if after_sleep > 0:
            time.sleep(after_sleep)
        return True

    def scroll(self, x, y, count=3):
        """Scroll at relative coordinates."""
        interaction = self.device_manager.interaction
        if not interaction:
            return False
        cap = self.device_manager.capture_method
        if cap and cap.width > 0 and cap.height > 0:
            abs_x = int(x * cap.width)
            abs_y = int(y * cap.height)
        else:
            abs_x, abs_y = int(x), int(y)
        interaction.scroll(abs_x, abs_y, count)
        return True

    def find_feature(self, name, threshold=0.8):
        """Find a template feature on screen."""
        task = self._get_task_helper()
        if not task:
            return []
        frame = self._get_frame()
        if frame is None:
            return []
        boxes = task.find_feature(name, threshold=threshold, frame=frame)
        return [{"name": b.name, "x": b.x, "y": b.y, "width": b.width, "height": b.height,
                 "confidence": b.confidence} for b in (boxes or [])]

    # ===== Task API =====

    def list_tasks(self):
        """List all available tasks."""
        result = []
        for i, task in enumerate(self.executor.onetime_tasks):
            result.append({"index": i, "name": type(task).__name__, "display_name": task.name,
                           "enabled": task.enabled})
        return result

    def _focus_game_window(self):
        """Bring game window to foreground for reliable input."""
        try:
            import win32gui
            import win32con
            hw = self.device_manager.hwnd_window
            hwnd = getattr(hw, 'hwnd', 0) if hw else 0
            if hwnd and win32gui.IsWindow(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                logger.info(f"Game window focused: hwnd={hwnd}")
        except Exception as e:
            logger.warning(f"Could not focus game window: {e}")

    def start_task(self, task_name, config=None):
        """Start a registered task via executor's own thread (avoids OCR contention)."""
        if self._current_task:
            return {"error": "A task is already running", "task": type(self._current_task).__name__}
        # Bring game to foreground for reliable combat targeting
        self._focus_game_window()

        task = None
        for t in self.executor.onetime_tasks:
            if type(t).__name__ == task_name:
                task = t
                break
        if not task:
            return {"error": f"Task '{task_name}' not found"}

        # Apply config overrides if provided
        if config and isinstance(config, dict):
            for k, v in config.items():
                task.config[k] = v
            logger.info(f"Task config updated: {config}")

        # Give task access to ww_context for direct OCR/click (same path as test scripts)
        task._ww_ctx = self

        self._current_task = task
        # Let executor's own thread run the task (same thread = no OCR contention)
        task.enable()
        task.unpause()
        self.executor.current_task = task
        logger.info(f"Task queued for executor: {task_name}")
        return {"ok": True, "task": task_name}

    def stop_task(self):
        """Stop the currently running task."""
        if self._current_task:
            name = type(self._current_task).__name__
            self._current_task.disable()
            try:
                self.executor.stop_current_task()
            except Exception:
                pass
            self._current_task = None
            self.executor.current_task = None
            return {"ok": True, "stopped": name}
        return {"ok": True, "stopped": None}

    def task_status(self):
        """Get current task execution status."""
        # Check executor's current_task (might be cleared by executor thread)
        current = self.executor.current_task if self.executor else None
        if current is None and self._current_task:
            # Task finished, executor cleared it
            self._current_task = None

        if self._current_task:
            info = {}
            try:
                info = dict(self._current_task.info) if hasattr(self._current_task, 'info') else {}
            except:
                pass
            return {
                "running": True,
                "task": type(self._current_task).__name__,
                "info": {k: str(v) for k, v in info.items()},
            }
        return {"running": False, "task": None}

    # ===== Script API =====

    def list_scripts(self):
        """List available scripts in scripts/ directory."""
        scripts = []
        if os.path.isdir(SCRIPTS_DIR):
            for f in os.listdir(SCRIPTS_DIR):
                if f.endswith('.py') and not f.startswith('_'):
                    scripts.append(f[:-3])
        return scripts

    def run_script(self, script_name):
        """Load and execute a script from scripts/ directory."""
        script_path = os.path.join(SCRIPTS_DIR, f"{script_name}.py")
        if not os.path.exists(script_path):
            return {"error": f"Script '{script_name}' not found"}

        spec = importlib.util.spec_from_file_location(f"scripts.{script_name}", script_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        if not hasattr(mod, 'execute'):
            return {"error": f"Script '{script_name}' has no execute(ctx) function"}

        try:
            result = mod.execute(self)
            return {"ok": True, "result": str(result) if result else None}
        except Exception as e:
            logger.error(f"Script '{script_name}' failed: {e}")
            return {"error": str(e)}

    def start_game(self):
        """Launch the game using ok-ww's device manager."""
        import subprocess
        try:
            # Try start_device on a task first (ok-ww built-in method)
            task = self._get_task_helper()
            if task:
                try:
                    result = task.start_device()
                    if result:
                        return {"ok": True, "method": "start_device"}
                except Exception as e:
                    logger.warning(f"start_device failed: {e}")

            # Fallback: find and launch the game exe
            preferred = self.device_manager.get_preferred_device()
            if preferred:
                exe_path = self.device_manager.get_exe_path(preferred)
                if exe_path and os.path.exists(exe_path):
                    logger.info(f"Launching game: {exe_path}")
                    subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
                    return {"ok": True, "method": "exe", "path": exe_path}

            # Last resort: use known launcher path
            launcher = r"E:\Wuthering Waves\launcher.exe"
            if os.path.exists(launcher):
                logger.info(f"Launching via launcher: {launcher}")
                subprocess.Popen([launcher], cwd=os.path.dirname(launcher))
                return {"ok": True, "method": "launcher", "path": launcher}

            return {"error": "No game executable found"}
        except Exception as e:
            logger.error(f"start_game failed: {e}")
            return {"error": str(e)}

    def get_logs(self, lines=50):
        """Read recent log entries from ok-ww log file."""
        log_file = os.path.join(PROJECT_DIR, "logs", "ok-script.log")
        if not os.path.exists(log_file):
            return []
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            all_lines = f.readlines()
        return [l.rstrip() for l in all_lines[-lines:]]
