from qfluentwidgets import FluentIcon

from ok import Logger
from src.task.BaseCombatTask import BaseCombatTask
from src.task.WWOneTimeTask import WWOneTimeTask

logger = Logger.get_logger(__name__)


class TacetTask(WWOneTimeTask, BaseCombatTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.group_name = "Dungeon"
        self.group_icon = FluentIcon.HOME
        self.description = "Farms the selected Tacet Suppression. Supports custom run count and auto condensed stamina."
        self.name = "Tacet Suppression"
        self.support_schedule_task = True
        default_config = {
            'Which Tacet Suppression to Farm': 1,  # starts with 1
            'Farm Count': 1,
        }
        self.total_number = 16
        self.target_enemy_time_out = 10
        default_config.update(self.default_config)
        self.config_description = {
            'Which Tacet Suppression to Farm': 'The Tacet Suppression number in the F2 list.',
            'Farm Count': 'Number of runs. Auto uses condensed stamina when regular stamina is empty.',
        }
        self.default_config = default_config
        self.door_walk_method = {  # starts with 0
            0: [],
            1: [],
            2: [],
            3: [],
            4: [],
            5: [],
            6: [["a", 0.3]],
            7: [["d", 0.6]],
            8: [["a", 1.5], ["w", 3], ["a", 2.5]],
        }
        self.stamina_once = 60

    def run(self):
        super().run()
        self.ensure_main(time_out=180)
        self.wait_in_team_and_world(esc=True)
        self.farm_tacet()

    def farm_tacet(self, daily=False, used_stamina=0, config=None):
        if config is None:
            config = self.config
        if daily:
            must_use = 180 - used_stamina
            max_count = 999999
        else:
            must_use = 0
            max_count = config.get('Farm Count', 1)
        count = 0
        self.info_incr('used stamina', 0)
        while count < max_count:
            self.sleep(1)
            gray_book_boss = self.openF2Book("gray_book_boss")
            self.click_box(gray_book_boss, after_sleep=1)
            current, back_up, total = self.get_stamina()
            if current == -1:
                self.click_relative(0.04, 0.4, after_sleep=1)
                current, back_up, total = self.get_stamina()
            if daily and total < self.stamina_once:
                return self.not_enough_stamina()

            self.click_relative(0.18, 0.48, after_sleep=1)
            index = config.get('Which Tacet Suppression to Farm', 1) - 1
            self.teleport_to_tacet(index)
            self.wait_click_travel()
            self.wait_in_team_and_world(time_out=120)
            self.sleep(2)
            if self.door_walk_method.get(index) is not None:
                for method in self.door_walk_method.get(index):
                    self.send_key_down(method[0])
                    self.sleep(method[1])
                    self.send_key_up(method[0])
                    self.sleep(0.05)
                in_combat = self.run_until(self.in_combat, 'w', time_out=10, running=True,
                                           target=False, post_walk=1)
                if not in_combat:
                    raise Exception('Tacet can not walk to combat')
            else:
                self.walk_until_f(time_out=4, backward_time=0, raise_if_not_found=True)
                self.pick_f(handle_claim=False)
            self.combat_once()
            self.sleep(3)
            self.walk_to_treasure()
            self.pick_f(handle_claim=False)
            can_continue, used = self.use_stamina(once=self.stamina_once, must_use=must_use)
            self.info_incr('used stamina', used)
            self.sleep(4)
            self.click(0.51, 0.84, after_sleep=3)
            count += 1
            self.log_info(f"Tacet run {count}/{max_count} done, used {used} stamina")
            if not can_continue:
                return self.not_enough_stamina()
            must_use -= used

    def use_stamina(self, once, must_use=0):
        """Override: always double reward, handle stamina exchange with 结晶溶剂.
        When stamina is insufficient, exchange popup appears with material options.
        Uses OCR to find confirm/cancel buttons instead of hardcoded coordinates."""
        self.sleep(1)
        used = once * 2
        x, y = 0.67, 0.62
        # Verify reward screen is open by reading stamina first
        current, back_up, total = self.get_stamina()
        if current == -1:
            self.log_info("Reward screen not open, retrying pick_f")
            self.send_key('f', after_sleep=2)
            current, back_up, total = self.get_stamina()
            if current == -1:
                self.log_info("Still no reward screen, skipping claim")
                return False, 0
        self.log_info(f"Tacet: stamina={current}/{total}, always double, clicking ({x}, {y}), cost={used}")
        self.click(x, y, after_sleep=1)

        # Loop: select 结晶溶剂 (item 2) and confirm, repeat until enough or max 5 tries.
        # NEVER use item 3 (star currency).
        for attempt in range(5):
            if not self.wait_feature('gem_add_stamina', horizontal_variance=0.4,
                                     vertical_variance=0.05, time_out=2):
                break  # No popup = claim succeeded
            self.log_info(f"Stamina exchange popup (attempt {attempt+1}): selecting 结晶溶剂")
            self.click(0.46, 0.39, after_sleep=0.5)  # Click item 2 (结晶溶剂)

            # Step 1: Click 确认 on first popup (confirm item selection)
            if not self.wait_click_ocr(0.3, 0.65, 0.8, 0.85, match='确认',
                                       time_out=3, after_sleep=2):
                self.log_info("第一步确认按钮未找到，尝试固定坐标")
                self.click(0.50, 0.71, after_sleep=2)

            # Step 2: Quantity selection page — click confirm at the BOTTOM
            # +/- buttons are in the middle (~y=0.5-0.6), confirm button is below
            self.sleep(2)
            self.screenshot('stamina_exchange_step2')
            # Debug: dump what's on screen
            all_boxes = self.ocr(0, 0, 1, 1)
            all_texts = [(b.name, b.x, b.y, b.width, b.height) for b in (all_boxes or [])]
            self.log_info(f"兑换第二步 OCR全文: {all_texts}")

            step2_done = False
            bottom_boxes = self.ocr(0.25, 0.70, 0.75, 0.95)
            for keyword in ['兑换', '确认', '确定', '交换', '购买']:
                matches = [b for b in (bottom_boxes or []) if keyword in b.name]
                if matches:
                    btn = matches[0]
                    self.log_info(f"兑换第二步: 底部找到 '{btn.name}' y={btn.y}")
                    self.click_box(btn, after_sleep=2)
                    step2_done = True
                    break
            if not step2_done:
                self.log_info("兑换第二步: 未找到按钮，尝试底部点击")
                self.click(0.50, 0.85, after_sleep=2)

            # After exchange, dismiss any result popup and wait for reward screen
            self.sleep(2)
            self.back(after_sleep=2)  # ESC to close exchange result/popup
            # Wait for reward screen to reappear before re-clicking
            self.log_info("兑换完成，等待奖励界面恢复")
            self.sleep(2)
            self.click(x, y, after_sleep=1)           # Re-click double reward to claim
        else:
            # Still not enough after 5 attempts — cancel
            if self.wait_feature('gem_add_stamina', horizontal_variance=0.4,
                                 vertical_variance=0.05, time_out=1):
                self.log_info("结晶溶剂 exhausted, cancelling")
                if not self.wait_click_ocr(0.2, 0.5, 0.6, 0.8, match='取消',
                                           time_out=2, after_sleep=1):
                    self.back(after_sleep=1)
                return False, 0

        self.sleep(1)
        # Re-read stamina after exchange to decide if we can continue
        new_current, new_back_up, new_total = self.get_stamina()
        self.log_info(f"After claim: current={new_current}, back_up={new_back_up}, total={new_total}")
        if new_total == -1:
            # Screen already transitioned, can't read stamina.
            # Continue anyway — next run's use_stamina will handle exchange if needed.
            self.log_info(f"Stamina read failed after claim, continuing (exchange may handle next run)")
            return True, used
        if new_total < once:
            self.log_info("Not enough stamina for next run")
            return False, used
        return True, used

    def not_enough_stamina(self, back=True):
        self.log_info(f"used all stamina")
        if back:
            self.back(after_sleep=1)

    def teleport_to_tacet(self, index):
        self.info_set('Teleport to Tacet Suppression', index)
        if index >= self.total_number:
            raise IndexError(f'Index out of range, max is {self.total_number}')
        self.click_on_book_target(index + 1, self.total_number)
