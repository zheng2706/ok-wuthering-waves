"""批量顺序强化多个角色的声骸。
通过API依次启动SmartEnhanceTask，等待完成后启动下一个。"""
import time
import urllib.request
import json

API = "http://127.0.0.1:8270"

CHARACTERS = [
    '弗洛洛', '奥古斯塔', '卡提希娅', '赞妮', '尤诺',
    '坎特蕾拉', '琳奈', '莫宁', '千咲', '守岸人', '菲比',
]


def api(path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def wait_task_done(timeout=600):
    """Wait for current task to finish. Returns last status info."""
    start = time.time()
    last_info = {}
    while time.time() - start < timeout:
        status = api("/task/status")
        if not status.get("running"):
            return last_info
        last_info = status.get("info", {})
        time.sleep(5)
    return {"error": "timeout"}


def run_character(name):
    print(f"\n{'='*50}")
    print(f"开始: {name}")
    print(f"{'='*50}")

    result = api("/task/start", {"name": "SmartEnhanceTask", "config": {"角色名": name}})
    if not result.get("ok"):
        print(f"  启动失败: {result}")
        return False

    # Monitor progress
    start = time.time()
    while True:
        time.sleep(6)
        status = api("/task/status")
        if not status.get("running"):
            elapsed = int(time.time() - start)
            print(f"  完成 ({elapsed}s)")
            return True

        info = status.get("info", {})
        log = info.get("Log", "")
        task = info.get("current task", "")
        print(f"  [{int(time.time()-start):3d}s] {task} | {log}")

        if time.time() - start > 600:
            print(f"  超时，停止任务")
            api("/task/stop", {})
            time.sleep(3)
            return False


def main():
    print(f"批量强化 {len(CHARACTERS)} 个角色")
    print(f"角色列表: {', '.join(CHARACTERS)}")

    results = {}
    for i, name in enumerate(CHARACTERS):
        print(f"\n[{i+1}/{len(CHARACTERS)}]", end="")
        ok = run_character(name)
        results[name] = "OK" if ok else "FAIL"

        # Brief pause between characters
        if i < len(CHARACTERS) - 1:
            time.sleep(2)

    print(f"\n{'='*50}")
    print("全部完成！")
    for name, status in results.items():
        print(f"  {name}: {status}")


if __name__ == "__main__":
    main()
