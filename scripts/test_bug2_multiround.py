"""Bug 2 验证: 多轮筛选面板开关 + Cost tab 切换 + 主属性选择。
3轮完整流程: 打开面板->选套装->选主属性->确认->关闭->重置->重开。"""
import re
import time


def _ensure_echo_backpack(ctx):
    """Navigate to echo backpack, handling popups first."""
    menu_kw = ['终端', '活动', '商城', '共鸣者']
    backpack_kw = ['武器', '声骸', '补给', '资源']

    for attempt in range(10):
        # Check for popup/dialog FIRST — click 取消 button (ESC may close backpack)
        cancel = ctx.ocr(0.1, 0.3, 0.9, 0.9, match='取消')
        if cancel:
            b = cancel[0] if isinstance(cancel, list) else cancel
            ctx.click(b.get('x',0)+b.get('width',0)/2,
                      b.get('y',0)+b.get('height',0)/2, after_sleep=1.5)
            continue

        top = ctx.ocr(0, 0, 0.5, 0.12)
        texts = ' '.join(b.get('name', '') for b in (top or []))

        if any(kw in texts for kw in backpack_kw):
            ctx.click(0.02, 0.30, after_sleep=2)
            return True
        if any(kw in texts for kw in menu_kw):
            ctx.send_key('esc', after_sleep=1)
            continue
        ctx.send_key('b', after_sleep=3)
    return False


def _is_filter_panel_open(ctx):
    return bool(ctx.ocr(0.55, 0.0, 1.0, 0.10, match='筛选'))


def _is_overlay_open(ctx):
    return bool(ctx.ocr(0.0, 0.0, 1.0, 0.25, match='Cost'))


def execute(ctx):
    results = {}
    step = [0]
    def shot(label):
        step[0] += 1
        s = ctx.screenshot()
        results[f'{step[0]:02d}_{label}'] = s.get('path', '')

    if not _ensure_echo_backpack(ctx):
        return {'error': 'nav failed'}
    shot('echo_page')

    # 3 rounds: same set (避免滚动问题), different cost/stat
    rounds = [
        ('听唤', 4, '暴击伤害'),       # Cost4 default, skip tab click
        ('听唤', 4, '暴击率'),          # Cost4 again, different stat
        ('听唤', 3, '气动伤害加成'),     # Cost3, must switch tab
    ]

    for ri, (set_short, cost, main_stat) in enumerate(rounds):
        rl = f'R{ri+1}'
        results[f'{rl}_params'] = f'{set_short} Cost{cost} {main_stat}'

        # 1. Open filter panel
        if not _is_filter_panel_open(ctx):
            ctx.dbl_click(0.115, 0.900, after_sleep=2)
            if not _is_filter_panel_open(ctx):
                ctx.dbl_click(0.115, 0.900, after_sleep=3)
        results[f'{rl}_panel'] = _is_filter_panel_open(ctx)
        shot(f'{rl}_panel')

        if not results[f'{rl}_panel']:
            results['stopped'] = ri + 1
            break

        # 2. Select set
        ctx.real_click(0.85, 0.454, after_sleep=2)
        match = ctx.ocr(0.6, 0.45, 1.0, 0.95, match=set_short)
        if match:
            b = match[0] if isinstance(match, list) else match
            ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                           b.get('y',0)+b.get('height',0)/2, after_sleep=2)
            results[f'{rl}_set'] = True
        else:
            results[f'{rl}_set'] = False
        shot(f'{rl}_set')

        # 3. Open overlay
        add = ctx.ocr(0.6, 0.4, 1.0, 0.65, match='添加')
        if add:
            b = add[0] if isinstance(add, list) else add
            ctx.real_click(b.get('x',0)+b.get('width',0)+0.02,
                           b.get('y',0)+b.get('height',0)/2, after_sleep=3)
        results[f'{rl}_overlay'] = _is_overlay_open(ctx)
        shot(f'{rl}_overlay')

        if not results[f'{rl}_overlay']:
            results['stopped'] = ri + 1
            break

        # 4+5. Search stat first, switch Cost tab only if needed
        # Cost tab: PostMessage click (real_click unreliable on overlay tabs)
        stat = ctx.ocr(0.0, 0.1, 1.0, 0.8, match=main_stat)
        if not stat and cost != 4:
            # Verified tab positions from full-screen OCR dump
            COST_TAB = {3: (0.400, 0.216), 1: (0.645, 0.216)}
            pos = COST_TAB.get(cost)
            if pos:
                results[f'{rl}_tab_pos'] = f'{pos[0]},{pos[1]}'
                ctx.click(pos[0], pos[1], after_sleep=2)  # PostMessage click
            stat = ctx.ocr(0.0, 0.1, 1.0, 0.8, match=main_stat)

        if stat:
            b = stat[0] if isinstance(stat, list) else stat
            ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                           b.get('y',0)+b.get('height',0)/2, after_sleep=1)
            results[f'{rl}_stat'] = True
        else:
            results[f'{rl}_stat'] = False
        results[f'{rl}_overlay_after'] = _is_overlay_open(ctx)
        shot(f'{rl}_stat')

        # 6. Confirm
        confirm = ctx.ocr(0.0, 0.7, 1.0, 1.0, match='确认')
        if confirm:
            b = confirm[0] if isinstance(confirm, list) else confirm
            ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                           b.get('y',0)+b.get('height',0)/2, after_sleep=2)
            results[f'{rl}_confirm'] = True
        else:
            results[f'{rl}_confirm'] = False
        shot(f'{rl}_confirm')

        # 7. Close filter panel (verified)
        for _ in range(3):
            ctx.dbl_click(0.115, 0.900, after_sleep=1.5)
            if not _is_filter_panel_open(ctx):
                break
        results[f'{rl}_closed'] = not _is_filter_panel_open(ctx)
        shot(f'{rl}_closed')
        time.sleep(2)

        # 8. Reset (reopen -> reset -> close)
        ctx.dbl_click(0.115, 0.900, after_sleep=2)
        results[f'{rl}_reopen'] = _is_filter_panel_open(ctx)
        if results[f'{rl}_reopen']:
            reset = ctx.ocr(0.6, 0.75, 1.0, 0.95, match='重置')
            if reset:
                b = reset[0] if isinstance(reset, list) else reset
                ctx.real_click(b.get('x',0)+b.get('width',0)/2,
                               b.get('y',0)+b.get('height',0)/2, after_sleep=1.5)
            for _ in range(3):
                ctx.dbl_click(0.115, 0.900, after_sleep=1.5)
                if not _is_filter_panel_open(ctx):
                    break
        shot(f'{rl}_reset')
        time.sleep(1)

    results['rounds_ok'] = sum(1 for i in range(1,4)
                                if results.get(f'R{i}_stat'))
    return results
