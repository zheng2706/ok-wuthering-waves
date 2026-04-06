"""
SmartEnhanceTask - 指定角色自动强化声骸

流程:
1. 从 wutheringlab 获取配装方案（套装结构、每费主属性、副词条）
2. 进入角色声骸页读取当前装备套装，匹配推荐方案
3. 打开背包声骸页，使用游戏筛选器（套装+费用+主属性）
4. 对筛选后的声骸逐个强化，评估副词条
5. 对每种费用+主属性组合重复步骤3-4
"""

import json
import os
import re
import time
import urllib.request

from ok import FindFeature, Logger
from src.task.BaseWWTask import BaseWWTask
from src.task.EnhanceEchoTask import EnhanceEchoTask

logger = Logger.get_logger(__name__)

# ===== EN→CN Mappings =====

# Echo set names: verified from ok-ww i18n + user confirmed
SET_NAME_MAP = {
    # From ok-ww i18n (authoritative)
    'Freezing Frost': '凝夜白霜',
    'Celestial Light': '浮星祛暗',
    'Molten Rift': '熔山裂谷',
    'Void Thunder': '彻空冥雷',
    'Sierra Gale': '啸谷长风',
    'Rejuvenating Glow': '隐世回光',
    'Moonlit Clouds': '轻云出月',
    'Lingering Tunes': '不绝余音',
    'Frosty Resolve': '凌冽决断之心',
    'Eternal Radiance': '此间永驻之光',
    'Midnight Veil': '幽夜隐匿之帷',
    'Empyrean Anthem': '高天共奏之曲',
    'Tidebreaking Courage': '无惧浪涛之勇',
    # User confirmed
    'Havoc Eclipse': '沉日劫明',
    'Crown of Valor': '荣斗铸锋之冠',
    'Windward Pilgrimage': '愿戴荣光之旅',
    "Flamewing's Shadow": '焚羽猎魔之影',
    'Flaming Clawprint': '奔狼燎原之焰',
    'Dream of the Lost': '失序彼岸之梦',
    'Gusts of Welkin': '流云逝尽之空',
    'Trailblazing Star': '长路启航之星',
}
# Echo creature names EN→CN (Cost 4 boss echoes from Fandom Wiki)
ECHO_NAME_MAP = {
    # Calamity Class (Cost 4, Weekly Bosses)
    'Sigillum': '辛吉勒姆', 'Dreamless': '无妄者', 'Jue': '角',
    'Bell-Borne Geochelone': '鸣钟之龟', 'Hecate': '赫卡忒',
    # Overlord Class (Cost 4, World Bosses)
    'Crownless': '无冠者', 'Lampylumen Myriad': '辉萤军势',
    'Impermanence Heron': '无常凶鹭', 'Thundering Mephis': '云闪之鳞',
    'Inferno Rider': '燎照之骑', 'Feilian Beringal': '飞廉之猩',
    'Mourning Aix': '哀声鸷', 'Tempest Mephis': '朔雷之鳞',
    'Mech Abomination': '聚械机偶', 'Sentry Construct': '异构武装',
    'Dragon of Dirge': '叹息古龙', 'Fallacy of No Return': '无归的谬误',
    'The False Sovereign': '伪作的神王', 'Lorelei': '罗蕾莱',
    'Lioness of Glory': '荣耀狮像', 'Reactor Husk': '炉芯机骸',
    'Hyvatia': '海维夏', 'Lady of the Sea': '海之女',
    'Nameless Explorer': '无铭探索者',
}

# Reverse map for CN→EN lookup
SET_NAME_MAP_REV = {v: k for k, v in SET_NAME_MAP.items()}

# Sub-stat names (wutheringlab EN → game CN)
SUBSTAT_MAP = {
    'CRIT Rate': '暴击', 'Crit Rate': '暴击',
    'CRIT Dmg': '暴击伤害', 'CRIT DMG': '暴击伤害', 'Crit DMG': '暴击伤害',
    'ATK%': '攻击百分比', 'ATK': '攻击',
    'HP%': '生命百分比', 'HP': '生命',
    'DEF%': '防御百分比', 'DEF': '防御',
    'Energy Regen': '共鸣效率', 'Energy Regen%': '共鸣效率',
    'Resonance Skill DMG': '共鸣技能伤害加成', 'Resonance Skill DMG Bonus': '共鸣技能伤害加成',
    'Resonance Liberation DMG': '共鸣解放伤害加成', 'Resonance Liberation DMG Bonus': '共鸣解放伤害加成',
    'Basic Attack DMG': '普攻伤害加成', 'Basic Attack DMG Bonus': '普攻伤害加成',
    'Heavy Attack DMG': '重击伤害加成', 'Heavy Attack DMG Bonus': '重击伤害加成',
    'Flat ATK': '攻击',
}

# Main stat names (wutheringlab EN → game CN for filter)
# Source: FiveToOneTask.main_stats (authoritative game data)
MAIN_STAT_MAP = {
    'CRIT Rate': '暴击率', 'Crit Rate': '暴击率',
    'CRIT Dmg': '暴击伤害', 'CRIT DMG': '暴击伤害', 'Crit DMG': '暴击伤害',
    'ATK': '攻击力百分比', 'ATK%': '攻击力百分比',
    'HP': '生命值百分比', 'HP%': '生命值百分比',
    'DEF': '防御力百分比', 'DEF%': '防御力百分比',
    'Energy Regen': '共鸣效率', 'Energy Regen%': '共鸣效率',
    'Healing': '治疗效果加成', 'Healing Bonus': '治疗效果加成',
    'Aero DMG': '气动伤害加成', 'Aero DMG Bonus': '气动伤害加成',
    'Glacio DMG': '冷凝伤害加成', 'Glacio DMG Bonus': '冷凝伤害加成',
    'Fusion DMG': '热熔伤害加成', 'Fusion DMG Bonus': '热熔伤害加成',
    'Electro DMG': '导电伤害加成', 'Electro DMG Bonus': '导电伤害加成',
    'Spectro DMG': '衍射伤害加成', 'Spectro DMG Bonus': '衍射伤害加成',
    'Havoc DMG': '湮灭伤害加成', 'Havoc DMG Bonus': '湮灭伤害加成',
}

# Character name → wutheringlab URL slug
CHAR_SLUG_MAP = {
    '尤诺': 'iuno', '今汐': 'jinhsi', '忌炎': 'jiyan', '卡卡罗': 'calcharo',
    '安可': 'encore', '凌阳': 'lingyang', '维里奈': 'verina', '白芷': 'baizhi',
    '秧秧': 'yangyang', '丹瑾': 'danjin', '散华': 'sanhua', '莫特斐': 'mortefi',
    '鉴心': 'jianxin', '炽霞': 'chixia', '桃祈': 'taoqi', '渊武': 'yuanwu',
    '秋水': 'aalto', '椿': 'camellya', '折枝': 'zhezhi', '相里要': 'xiangli_yao',
    '长离': 'changli', '洛可可': 'roccia', '守岸人': 'shorekeeper', '布兰特': 'brant',
    '灯灯': 'phrolova', '漂泊者': 'rover', '吟霖': 'yinlin',
    '爱弥斯': 'aemeath', '弗洛洛': 'phrolova', '奥古斯塔': 'augusta',
    '卡提希娅': 'cartethyia', '赞妮': 'zani', '坎特蕾拉': 'cantarella',
    '琳奈': 'lynae', '莫宁': 'mornye', '千咲': 'chisa', '菲比': 'phoebe',
    '嘉贝莉娜': 'galbrena', '珂莱塔': 'carlotta',
}

# Backpack UI constants
SIDEBAR_X = 0.025
SIDEBAR_ECHO_Y = 0.30

# Build config files — relative to project root (configs/ directory)
_CONFIGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'configs')
CHARACTER_BUILDS_PATH = os.path.join(_CONFIGS_DIR, 'CharacterBuilds.json')
BUILD_CACHE_PATH = os.path.join(_CONFIGS_DIR, 'SmartEnhanceBuildCache.json')


class SmartEnhanceTask(BaseWWTask, FindFeature):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "智能强化声骸"
        self.description = "选择角色，自动获取配装方案并按顺序强化声骸"
        self.default_config = {
            '角色列表': [],
            '双爆总计>=': 13.8,
            '首条双爆>=': 6.9,
            '有效词条>=': 3,
        }
        self.config_type = {
            '角色列表': {
                'type': 'multi_selection',
                'options': list(CHAR_SLUG_MAP.keys()),
            },
            '清除配装缓存': {
                'type': 'button',
                'buttons': [{'text': '清除全部缓存', 'callback': self._clear_all_cache}],
            },
        }
        self.config_description = {
            '角色列表': '勾选要强化声骸的角色，按勾选顺序依次执行',
            '清除配装缓存': '清除本地配装缓存，下次强化时重新从网站获取并进入共鸣者页面确认',
        }
        self._build_data = None

    # ===== Character Build Config (human-readable) =====

    def _load_character_build(self, char_name):
        """Load character build from CharacterBuilds.json (user-editable file).
        Returns dict with keys: sets_cn, cost_main_stats, substats_cn, echo_per_cost. Or None."""
        if not os.path.exists(CHARACTER_BUILDS_PATH):
            return None
        try:
            with open(CHARACTER_BUILDS_PATH, 'r', encoding='utf-8') as f:
                builds = json.load(f)
            entry = builds.get(char_name)
            if not entry or '套装' not in entry:
                return None
            # Convert human-readable format to internal format
            result = {
                'matched': {'sets_cn': entry['套装'], 'matched_build': None},
                'cost_main_stats': entry.get('费用主属性', {}),
                'substats_cn': entry.get('副词条优先级', ['暴击', '暴击伤害', '攻击百分比']),
                'echo_per_cost': entry.get('指定声骸', {}),
            }
            logger.info(f'[配装] 从 CharacterBuilds.json 读取 {char_name}')
            return result
        except Exception as e:
            logger.warning(f'[配装] 读取 CharacterBuilds.json 失败: {e}')
        return None

    def _save_character_build(self, char_name, matched, cost_main_stats, substats_cn, echo_per_cost):
        """Save character build to CharacterBuilds.json in human-readable format."""
        builds = {}
        if os.path.exists(CHARACTER_BUILDS_PATH):
            try:
                with open(CHARACTER_BUILDS_PATH, 'r', encoding='utf-8') as f:
                    builds = json.load(f)
            except Exception:
                builds = {}

        # Convert to human-readable format with Chinese keys
        sets_cn = matched.get('sets_cn', {})
        cost_stats_str = {str(k): v for k, v in cost_main_stats.items()}
        echo_str = {}
        for k, v in echo_per_cost.items():
            echo_str[str(k)] = v

        builds[char_name] = {
            '套装': sets_cn,
            '费用主属性': cost_stats_str,
            '副词条优先级': substats_cn,
            '指定声骸': echo_str,
        }

        os.makedirs(os.path.dirname(CHARACTER_BUILDS_PATH), exist_ok=True)
        with open(CHARACTER_BUILDS_PATH, 'w', encoding='utf-8') as f:
            json.dump(builds, f, ensure_ascii=False, indent=2)
        logger.info(f'[配装] 已保存 {char_name} 到 CharacterBuilds.json')

    def _clear_all_cache(self):
        """Clear all cached build data (GUI button callback). Removes both files."""
        removed = False
        for path in [CHARACTER_BUILDS_PATH, BUILD_CACHE_PATH]:
            if os.path.exists(path):
                os.remove(path)
                removed = True
        if removed:
            logger.info('[配装] 已清除配装缓存')
        else:
            logger.info('[配装] 无缓存需要清除')

    # ===== Main Flow =====

    def ensure_main(self):
        """Override: detection-based ESC loop to return to main world."""
        self.info_set('current task', '返回主界面')
        menu_kw = ['终端', '武器', '声骸', '补给', '资源', '设置', '数据坞', '背包', '共鸣者', '编队', '属性', '筛选']
        for attempt in range(10):
            top = self.ocr(0, 0, 0.3, 0.1)
            texts = [b.name for b in (top or [])] if top else []
            in_menu = any(any(kw in t for kw in menu_kw) for t in texts)
            if not in_menu:
                center = self.ocr(0.2, 0.3, 0.8, 0.7, match=re.compile('确认|取消|弃置|提示'))
                if not center:
                    break
            self.send_key('esc', after_sleep=0.8)
        self.sleep(0.3)
        self.log_info('ensure_main: 完成')

    def run(self):
        char_list = self.config.get('角色列表', [])
        # Backward compat: old config had '角色名' as string
        if not char_list:
            old_name = self.config.get('角色名')
            if old_name:
                char_list = [old_name]
        if not char_list:
            raise Exception('请在配置中勾选至少一个角色')

        self.log_info(f'=== 智能强化声骸: {len(char_list)} 个角色 {char_list} ===')
        grand_success = 0
        grand_fail = 0

        for idx, char_name in enumerate(char_list):
            self.log_info(f'--- [{idx+1}/{len(char_list)}] 开始: {char_name} ---')
            s, f = self._run_for_character(char_name)
            grand_success += s
            grand_fail += f
            self.log_info(f'--- [{idx+1}/{len(char_list)}] {char_name} 完成: 成功={s}, 失败={f} ---')

        self.log_info(f'=== 全部角色完成: 成功={grand_success}, 失败={grand_fail} ===')

    def _run_for_character(self, char_name):
        """Run the full enhance flow for a single character. Returns (success, fail) counts."""

        # Priority: CharacterBuilds.json (user-editable) > web fetch + resonator page
        cached = self._load_character_build(char_name)
        if cached:
            self.log_info(f'[配装] 使用 CharacterBuilds.json 中 {char_name} 的数据')
            matched = cached['matched']
            cost_stats = cached['cost_main_stats']
            substats_cn = cached['substats_cn']
            echo_per_cost = cached.get('echo_per_cost', {})
        else:
            # First time: full flow — fetch from website + read resonator page
            self.info_set('current task', f'获取 {char_name} 配装数据')
            build_data = self.fetch_build_data(char_name)
            if not build_data:
                self.log_info(f'无法获取 {char_name} 的配装数据，跳过')
                return 0, 0
            self.log_info(f'推荐配装: {json.dumps(build_data["builds"], ensure_ascii=False)}')
            self.log_info(f'费用主属性: {json.dumps(build_data["cost_main_stats"], ensure_ascii=False)}')
            self.log_info(f'副词条: {build_data["substats_cn"]}')
            echo_per_cost = build_data.get('echo_per_cost', {})
            self.log_info(f'指定声骸: {echo_per_cost}')

            # Read character's current equipped sets
            self.info_set('current task', f'读取 {char_name} 当前配装')
            current_sets = self.read_character_echo_sets(char_name)
            self.log_info(f'当前装备套装: {current_sets}')

            # Match to a recommended build
            matched = self.match_build(build_data['builds'], current_sets)
            self.log_info(f'匹配结果: {json.dumps(matched, ensure_ascii=False)}')

            cost_stats = build_data['cost_main_stats']
            substats_cn = build_data['substats_cn']

            # Save to CharacterBuilds.json for future runs (user can edit)
            self._save_character_build(char_name, matched, cost_stats, substats_cn, echo_per_cost)

        self.log_info(f'配装: sets={json.dumps(matched.get("sets_cn", {}), ensure_ascii=False)}, '
                      f'costs={json.dumps(cost_stats, ensure_ascii=False)}, substats={substats_cn}')

        # Write enhance config (substats)
        self.info_set('current task', '写入强化配置')
        self.write_enhance_config(substats_cn)

        # Navigate to echo backpack
        self.navigate_to_echo_backpack()

        # For each COST+main_stat combo, filter and enhance
        total_success = 0
        total_fail = 0

        for cost_str, main_stats_list in cost_stats.items():
            cost = int(cost_str) if isinstance(cost_str, str) else cost_str
            sets_to_search = self._get_sets_for_cost(matched, cost)
            required_echo = echo_per_cost.get(cost) or echo_per_cost.get(str(cost))

            for set_cn in sets_to_search:
              for main_stat_cn in main_stats_list:
                self.info_set('current task', f'{char_name}: 筛选 {set_cn} {cost}C {main_stat_cn}')
                self.log_info(f'--- 筛选: 套装={set_cn}, COST={cost}, 主属性={main_stat_cn} ---')
                if required_echo:
                    self.log_info(f'需要特定声骸: {required_echo}')

                filter_result = self.apply_backpack_filter(set_cn, cost, main_stat_cn)
                if not filter_result:
                    self.log_info(f'筛选器设置失败，跳过此组合（安全保护）')
                    self.reset_filter()
                    continue

                filtered_count = filter_result if isinstance(filter_result, int) else -1

                self.sleep(1)
                self._click_echo_at(0, 0)
                self.sleep(1)
                if not self._wait_enhance_button(timeout=3):
                    self.log_info(f'筛选后无可强化声骸，跳过')
                    self.reset_filter()
                    continue

                if required_echo:
                    if not self._verify_echo_name(required_echo):
                        self.log_info(f'声骸名不匹配，跳过此组合')
                        self.reset_filter()
                        continue

                strict = True
                self.info_set('current task',
                              f'{char_name}: 强化 {cost}C {main_stat_cn} ({"严格" if strict else "宽松"}, {filtered_count}个)')
                s, f = self.run_enhance_loop(substats_cn, strict=strict)
                total_success += s
                total_fail += f

                self.reset_filter()

        self.log_info(f'{char_name} 完成: 成功={total_success}, 失败={total_fail}')
        return total_success, total_fail

    def _get_sets_for_cost(self, matched_build, cost):
        """Determine which set names (CN) to search for a given COST.
        4C: fixed to the primary set (usually has specific echo too).
        3C/1C: search ALL sets — these slots are flexible in 3+2 builds."""
        sets = matched_build.get('sets_cn', {})
        if len(sets) <= 1:
            return list(sets.keys())

        if cost == 4:
            # 4C is always the primary (most pieces) set
            primary = max(sets, key=lambda k: sets[k])
            return [primary]
        else:
            # 3C and 1C are flexible — search all sets
            return list(sets.keys())

    # ===== Build Data Parsing =====

    def fetch_build_data(self, char_name):
        """Fetch and parse complete build data from wutheringlab.
        Returns: {"builds": [...], "cost_main_stats": {4: [...], 3: [...], 1: [...]}, "substats_cn": [...]}"""
        slug = CHAR_SLUG_MAP.get(char_name)
        if not slug:
            self.log_error(f'未知角色: {char_name}')
            return None

        url = f'https://wutheringlab.com/characters/{slug}'
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8')
        except Exception as e:
            self.log_error(f'获取配装数据失败: {e}')
            return None

        # 1. Parse build structures: "SetName (N)" patterns
        builds = self._parse_builds_from_html(html)

        # 2. Parse cost→main_stat mapping from hp-value divs
        cost_main_stats = self._parse_cost_main_stats(html)

        # 3. Parse substat priority
        substats_cn = self._parse_substats_from_html(html)
        if not substats_cn:
            substats_cn = ['暴击', '暴击伤害', '攻击百分比']

        # 4. Parse main echo name per cost slot
        echo_per_cost = self._parse_echo_names(html)

        if not builds:
            self.log_info('未解析到配装')
            return None

        return {
            'builds': builds,
            'cost_main_stats': cost_main_stats,
            'substats_cn': substats_cn,
            'echo_per_cost': echo_per_cost,
        }

    def _parse_builds_from_html(self, html):
        """Parse build structures from HTML. Supports three formats:
        Old: 'Moonlit Clouds (5)', 'Crown of Valor (3)'
        New: 'Eternal Radiance X 5', 'Dream of the Lost X 3'
        Newest: '<em><strong>Windward Pilgrimage</strong></em>' (no count)"""
        # Strip HTML tags for text parsing
        text = re.sub(r'<[^>]+>', '\n', html)

        # Match both formats: "SetName (N)" and "SetName X N"
        set_pattern = re.compile(
            r'([A-Z][a-z]+(?:[\s\'-][A-Za-z]+)*)\s*(?:\((\d)\)|[Xx]\s*(\d))'
        )

        # Find all matches that are known set names
        all_matches = []
        for m in set_pattern.finditer(text):
            name = m.group(1)
            count = int(m.group(2) or m.group(3))
            if name in SET_NAME_MAP:
                all_matches.append((m.start(), name, count))

        # Fallback: newest format shows set names in <em><strong> without counts
        if not all_matches:
            em_pattern = re.compile(
                r'<em>\s*<strong>\s*'
                r'([A-Z][a-z]+(?:[\s\'-][A-Za-z]+)*)'
                r'\s*</strong>\s*</em>'
            )
            found_sets = []
            for m in em_pattern.finditer(html):
                name = m.group(1).strip()
                if name in SET_NAME_MAP:
                    found_sets.append((m.start(), name))
            if len(found_sets) == 1:
                all_matches.append((found_sets[0][0], found_sets[0][1], 5))
            elif len(found_sets) >= 2:
                # Most common multi-set split: first set gets 3, second gets 2
                all_matches.append((found_sets[0][0], found_sets[0][1], 3))
                all_matches.append((found_sets[1][0], found_sets[1][1], 2))

        if not all_matches:
            return []

        # Group consecutive matches into builds
        # Matches within 500 chars of each other belong to the same build
        builds = []
        current_build = {'sets': {}, 'has_flex': False}
        last_pos = all_matches[0][0]

        for pos, name, count in all_matches:
            if pos - last_pos > 500 and current_build['sets']:
                builds.append(current_build)
                current_build = {'sets': {}, 'has_flex': False}
            current_build['sets'][name] = count
            last_pos = pos

        if current_build['sets']:
            builds.append(current_build)

        # Check for Flex text near each build's region
        for i, build in enumerate(builds):
            region_start = all_matches[0][0] if i == 0 else all_matches[sum(len(b['sets']) for b in builds[:i])][0]
            region = text[region_start:region_start + 1000]
            if 'Flex' in region or 'flex' in region:
                build['has_flex'] = True

        # Calculate Flex pieces
        for build in builds:
            if build['has_flex']:
                total_pieces = sum(build['sets'].values())
                build['sets']['Flex'] = 5 - total_pieces
            del build['has_flex']

        return builds

    def _parse_cost_main_stats(self, html):
        """Parse cost→main_stat from hp-value divs.
        Each div has 'Cost N' text within 500 chars before it.
        Returns: {4: ["暴击伤害"], 3: ["气动伤害加成", "攻击力百分比"], 1: ["攻击力百分比"]}"""
        pattern = r'id="hp-value"[^>]*>(.*?)</div>'
        matches = list(re.finditer(pattern, html, re.DOTALL))
        cost_stats = {}

        for m in matches:
            text = re.sub(r'<[^>]*>', '', m.group(1)).strip()
            text = text.replace('&gt;', '>').replace('&amp;', '&').replace('\xa0', ' ')
            if not text:
                continue

            # Look for "Cost N" in the 500 chars before this div
            pre = html[max(0, m.start() - 500):m.start()]
            pre_clean = re.sub(r'<[^>]*>', ' ', pre)
            cost_match = re.search(r'Cost\s*(\d)', pre_clean)
            if not cost_match:
                continue

            cost = int(cost_match.group(1))
            stats = self._parse_main_stat_text(text, cost)
            if stats:
                cost_stats[cost] = stats

        return cost_stats

    def _parse_main_stat_text(self, text, cost):
        """Parse a main stat recommendation text into Chinese stat names.
        E.g., '22% CRIT Rate or 44% CRIT Dmg' → ['暴击伤害'] (4C rule: only CRIT DMG)
        E.g., 'Double 30% Aero DMG Bonus or 30% Aero DMG plus 30% ATK' → ['气动伤害加成', '攻击力百分比']"""
        results = []

        # Split by 'or' / 'plus' to get alternatives
        parts = re.split(r'\bor\b|\bplus\b|\+', text, flags=re.IGNORECASE)

        for part in parts:
            part = part.strip()
            # Remove percentage numbers
            clean = re.sub(r'[\d.]+%?\s*', '', part).strip()
            clean = re.sub(r'^Double\s+', '', clean, flags=re.IGNORECASE).strip()

            # Map to Chinese
            mapped = MAIN_STAT_MAP.get(clean)
            if not mapped:
                # Try partial match
                for en, cn in MAIN_STAT_MAP.items():
                    if en.lower() in clean.lower() or clean.lower() in en.lower():
                        mapped = cn
                        break
            if mapped and mapped not in results:
                results.append(mapped)

        # 4C rule: if both 暴击率 and 暴击伤害, keep only 暴击伤害
        if cost == 4 and '暴击率' in results and '暴击伤害' in results:
            results.remove('暴击率')

        return results

    def _parse_substats_from_html(self, html):
        """Parse substat priority from last hp-value div with '>' separators.
        Uses same (.*?)</div> approach as _parse_cost_main_stats, then strips tags."""
        pattern = r'id="hp-value"[^>]*>(.*?)</div>'
        matches = list(re.finditer(pattern, html, re.DOTALL))
        if not matches:
            return []

        # Use the LAST match (substats are after cost main stats)
        # Strip all HTML tags to get full text (handles nested divs)
        raw = matches[-1].group(1)
        priority_str = re.sub(r'<[^>]*>', '', raw).strip()
        priority_str = priority_str.replace('&gt;', '>').replace('&amp;', '&').replace('\xa0', ' ')

        parts = re.split(r'\s*[>=/]\s*', priority_str)
        valid_cn = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Remove parenthetical like "(10%)"
            part = re.sub(r'\([^)]*\)', '', part).strip()
            mapped = SUBSTAT_MAP.get(part)
            if mapped:
                if mapped not in valid_cn:
                    valid_cn.append(mapped)
            else:
                for en, cn in SUBSTAT_MAP.items():
                    if en.lower() in part.lower():
                        if cn not in valid_cn:
                            valid_cn.append(cn)
                        break
        return valid_cn

    def _parse_echo_names(self, html):
        """Parse which specific echo is needed per cost slot.
        Returns: {4: '辛吉勒姆', 3: None, 1: None} (None = any echo from set).
        'Any Cost N Echo' overrides specific names (means any echo at that cost is fine)."""
        result = {}

        # First: mark "Any" slots — these take priority
        any_costs = set()
        for m in re.finditer(r'Any Cost (\d) Echo', html):
            any_costs.add(int(m.group(1)))

        # Find specific echo images with cost class: "cost-cost-4 effect-xxx"
        pattern = r'cost-cost-(\d)[^>]*>.*?data-src="[^"]*?/([^/"]+)\.webp"'
        for m in re.finditer(pattern, html, re.DOTALL):
            cost = int(m.group(1))
            if cost in any_costs:
                continue  # This cost accepts any echo, skip
            if cost in result:
                continue  # Already found for this cost

            filename = m.group(2)
            clean_name = re.sub(r'-\d+x\d+$', '', filename)
            # Map to Chinese
            cn_name = ECHO_NAME_MAP.get(clean_name)
            if not cn_name:
                for en, cn in ECHO_NAME_MAP.items():
                    if en.lower().replace(' ', '-') == clean_name.lower().replace(' ', '-'):
                        cn_name = cn
                        break
            if cn_name:
                result[cost] = cn_name
                self.log_info(f'Cost{cost} 指定声骸: {clean_name} → {cn_name}')
            else:
                self.log_info(f'Cost{cost} 声骸 [{clean_name}] 未在映射中')

        # Any costs get None (no name restriction)
        for cost in any_costs:
            if cost not in result:
                result[cost] = None

        return result

    # ===== Character Set Reading =====

    def read_character_echo_sets(self, char_name):
        """Navigate to character echo page and read equipped set names.
        Returns dict: {"套装名": 件数} e.g. {"荣斗铸锋之冠": 3, "流云逝尽之空": 2}"""
        self.ensure_main()

        # Open ESC menu → click 共鸣者 (with retry)
        entered = False
        for attempt in range(3):
            self.send_key('esc', after_sleep=2)
            # Verify menu is open by checking for menu keywords
            menu_ocr = self.ocr(0.3, 0.3, 0.7, 0.7)
            menu_texts = [b.name for b in (menu_ocr or [])]
            if not any('共鸣者' in t or '设置' in t or '编队' in t for t in menu_texts):
                self.log_info(f'菜单未打开 (attempt {attempt+1}), OCR: {menu_texts}')
                self.sleep(1)
                continue
            try:
                self.wait_click_ocr(0.3, 0.3, 0.7, 0.7, match='共鸣者',
                                    raise_if_not_found=True, settle_time=0.5)
                self.log_info('共鸣者已点击，等待页面加载...')
                self.sleep(5)
                entered = True
                break
            except Exception:
                self.log_info(f'共鸣者按钮未找到 (attempt {attempt+1})')
                self.send_key('esc', after_sleep=1)
                self.sleep(1)

        if not entered:
            self.log_info('共鸣者页面进入失败，使用默认配装')
            return {}

        # Check if correct character, switch if needed
        name_ocr = self.ocr(0.10, 0.08, 0.25, 0.16)
        current = next((b.name for b in (name_ocr or [])
                         if len(b.name) >= 2 and b.name not in ['属性详情', '声骸']), '')
        self.log_info(f'当前角色: {current}')

        if not self._fuzzy_char_match(char_name, current):
            self.log_info(f'需要切换到 {char_name}')
            if not self._select_from_char_list(char_name):
                self.log_info(f'未找到 {char_name}')

        # Switch to echo tab
        self.click_relative(0.015, 0.40, after_sleep=2)

        # Read 合鸣效果 section
        # Strategy 1: Find (N/N) boxes, take PREVIOUS box and validate against known set names
        # Strategy 2: If strategy 1 fails, scan all text for known set names
        sets_ocr = self.ocr(0.05, 0.45, 0.50, 0.80)
        boxes = [(b.name.strip(), b.y, b.x) for b in (sets_ocr or [])]
        self.log_info(f'合鸣效果 OCR ({len(boxes)} boxes): {[b[0] for b in boxes]}')

        # Known set names (all values from SET_NAME_MAP)
        known_sets = set(SET_NAME_MAP.values())

        result = {}

        def _match_set_name(candidate):
            """Match candidate text to a known set name. Returns (set_name, True) or (None, False)."""
            candidate = candidate.strip()
            if not candidate:
                return None, False
            if candidate in known_sets:
                return candidate, True
            # Substring match
            for ks in known_sets:
                if candidate in ks or ks in candidate:
                    return ks, True
            # Edit-distance 1 match for OCR typos (e.g. 凌列决断之心 → 凌冽决断���心)
            if len(candidate) >= 4:
                for ks in known_sets:
                    if len(ks) == len(candidate) and sum(a != b for a, b in zip(candidate, ks)) == 1:
                        return ks, True
            return None, False

        # Find (N/N) pattern anywhere in each box (handles noise like ".(3/3)" or "失序彼岸之梦(3/3)")
        for i, (text, y, x) in enumerate(boxes):
            m = re.search(r'(\d)/\d', text)
            if not m:
                continue
            count = int(m.group(1))

            # Check if set name is in the same box (merged case: "失序彼岸之梦(3/3)")
            name_part = text[:m.start()].rstrip('(（.）) ')
            matched_name, found = _match_set_name(name_part)
            if found:
                result[matched_name] = count
                continue

            # Search backwards through previous boxes for set name
            for j in range(i - 1, max(-1, i - 5), -1):
                candidate = boxes[j][0]
                matched_name, found = _match_set_name(candidate)
                if found:
                    result[matched_name] = count
                    break

        self.log_info(f'解析到套装: {result}')
        self.ensure_main()
        return result

    @staticmethod
    def _fuzzy_char_match(target, ocr_text):
        """Match character name allowing common OCR errors (希→西, 娅→亚, etc.).
        Returns True if target is a substring, OR if all-but-one characters match in order."""
        if target in ocr_text:
            return True
        if len(target) < 2:
            return False
        # Check if first 2 chars match (rarely misread, enough to identify uniquely)
        if target[:2] in ocr_text:
            return True
        # Check if dropping any single char from target still matches
        for i in range(len(target)):
            partial = target[:i] + target[i + 1:]
            if partial in ocr_text:
                return True
        return False

    def _select_from_char_list(self, char_name):
        """Navigate to 共鸣者列表 and select character."""
        # Open character list
        self.click_relative(0.935, 0.89, after_sleep=1.5)
        header = self.ocr(0, 0, 0.15, 0.08)
        if not any('列表' in b.name for b in (header or [])):
            for y in [0.85, 0.92, 0.95]:
                self.click_relative(0.935, y, after_sleep=1)
                header = self.ocr(0, 0, 0.15, 0.08)
                if any('列表' in b.name for b in (header or [])):
                    break
            else:
                return False

        self.log_info('角色列表已打开')
        self.scroll_relative(0.2, 0.4, 20)
        self.sleep(0.5)

        cols = [0.04, 0.12, 0.19, 0.27]
        rows = [0.15, 0.30, 0.45, 0.60, 0.75]
        for _ in range(3):
            for ry in rows:
                for cx in cols:
                    self.click_relative(cx, ry, after_sleep=0.4)
                    name_ocr = self.ocr(0.70, 0.40, 0.95, 0.55)
                    ocr_names = [b.name for b in (name_ocr or []) if len(b.name) >= 2]
                    if any(self._fuzzy_char_match(char_name, name) for name in ocr_names):
                        self.log_info(f'找到角色 {char_name} (OCR: {ocr_names})')
                        self.send_key('esc', after_sleep=3)
                        return True
            self.scroll_relative(0.2, 0.4, -5)
            self.sleep(0.5)

        self.send_key('esc', after_sleep=2)
        return False

    def match_build(self, builds, current_sets):
        """Match current equipped sets to a recommended build.
        Uses count-structure matching: {3,2} matches {Crown(3), Flex(2)}.
        Returns: {"sets_cn": {"荣斗铸锋之冠": 3, "流云逝尽之空": 2}, "matched_build": ...}"""
        if not builds:
            raise Exception('无推荐配装')

        if not current_sets:
            self.log_info('未读取到当前套装，使用第一个推荐')
            first = builds[0]
            sets_cn = {}
            for en, count in first['sets'].items():
                cn = SET_NAME_MAP.get(en, en)
                if cn != 'Flex':
                    sets_cn[cn] = count
            return {'sets_cn': sets_cn, 'matched_build': first}

        # Try to match each build's count structure (v2 with Flex support)
        current_counts = sorted(current_sets.values(), reverse=True)
        current_set_names_cn = set(current_sets.keys())
        self.log_info(f'匹配v2: counts={current_counts} names={current_set_names_cn}')

        for build in builds:
            # Include Flex in count comparison (Flex matches any set)
            build_counts_full = sorted(build['sets'].values(), reverse=True)
            build_counts_no_flex = sorted(
                [c for name, c in build['sets'].items() if name != 'Flex'],
                reverse=True
            )

            # Match 1: Exact structure match including Flex
            # e.g., build {Crown(3), Flex(2)} → [3,2] matches current [3,2]
            if current_counts == build_counts_full:
                # Also verify the non-Flex set names match
                build_set_names_cn = {SET_NAME_MAP.get(n, n) for n in build['sets'] if n != 'Flex'}
                if build_set_names_cn.issubset(current_set_names_cn):
                    sets_cn = dict(current_sets)
                    self.log_info(f'套装结构匹配: 游戏{current_counts} ↔ 推荐{build_counts_full} (含Flex)')
                    return {'sets_cn': sets_cn, 'matched_build': build}

            # Match 2: Pure single-set build (e.g., 5-piece)
            # Only match if the set name is actually equipped
            if len(build_counts_no_flex) == 1 and len(build['sets']) == 1:
                set_en = list(build['sets'].keys())[0]
                set_cn = SET_NAME_MAP.get(set_en, set_en)
                if set_cn in current_set_names_cn:
                    sets_cn = dict(current_sets)
                    self.log_info(f'套装名匹配: 游戏含{set_cn} ↔ 推荐{set_en}({build_counts_no_flex[0]})')
                    return {'sets_cn': sets_cn, 'matched_build': build}

        # No structural match, use first build
        self.log_info(f'无结构匹配，使用第一个推荐')
        first = builds[0]
        sets_cn = {}
        for en, count in first['sets'].items():
            cn = SET_NAME_MAP.get(en, en)
            if cn != 'Flex':
                sets_cn[cn] = count
        return {'sets_cn': sets_cn, 'matched_build': first}

    # ===== Backpack Navigation =====

    def navigate_to_echo_backpack(self):
        """Navigate to echo backpack page."""
        self.info_set('current task', '导航到声骸背包')
        self.ensure_main()

        for attempt in range(3):
            self.send_key('b', after_sleep=2.5)

            # Dismiss popup first
            popup = self.ocr(0.2, 0.3, 0.8, 0.8)
            if any('弃置' in b.name for b in (popup or [])):
                self.log_info('弹窗关闭')
                self.send_key('esc', after_sleep=1)

            if self._detect_backpack():
                # Switch to echo tab (sidebar click at verified position)
                self.click_relative(0.02, 0.30, after_sleep=2)
                # Verify echo tab
                header = self.ocr(0, 0, 0.25, 0.08)
                if header and any('声骸' in b.name for b in header):
                    self.log_info('声骸背包已打开')
                    return
                self.log_info('背包已打开但不在声骸tab，重试')
            self.send_key('esc', after_sleep=0.5)
            self.send_key('esc', after_sleep=0.5)

        raise Exception('无法打开声骸背包')

    def _detect_backpack(self):
        """Check if backpack is open."""
        raw = self.ocr(0, 0, 0.5, 0.15)
        texts = [b.name for b in (raw or [])] if raw else []
        return any(any(kw in t for kw in ['武器', '声骸', '补给', '资源', '/3000']) for t in texts)

    # ===== Backpack Filter =====
    # Uses mixed interaction: PostMessage for background ops (filter panel, cost tabs),
    # GenshinInteraction for real mouse ops (dropdowns, overlay selections).
    # Framework OCR returns Box objects with pixel coordinates.

    def _ensure_real_interaction(self):
        """Get or create GenshinInteraction for real mouse operations.
        GenshinInteraction.operate() auto-handles foreground/background:
        saves cursor -> activates window -> blocks input -> operates -> restores."""
        if not hasattr(self, '_real_interaction') or self._real_interaction is None:
            from ok.device.intercation import GenshinInteraction
            dm = self.executor.device_manager
            self._real_interaction = GenshinInteraction(dm.capture_method, dm.hwnd_window)
            logger.info('Created GenshinInteraction for real mouse ops')
        return self._real_interaction

    def _to_pixel(self, x, y):
        """Convert coordinates to pixel. If 0-1 float, multiply by capture size."""
        cap = self.executor.device_manager.capture_method
        if isinstance(x, float) and x <= 1.0 and isinstance(y, float) and y <= 1.0:
            return int(x * cap.width), int(y * cap.height)
        return int(x), int(y)

    def _ctx_ocr(self, x, y, to_x, to_y, match=None):
        """OCR with fresh frame capture and substring matching.
        Framework ocr(match=) may not do substring matching like ww_context does.
        So we fetch all results and filter ourselves."""
        cap = self.executor.device_manager.capture_method
        frame = cap.get_frame() if cap else None
        boxes = self.ocr(x, y, to_x, to_y, frame=frame) or []
        if match and boxes:
            if isinstance(match, str):
                boxes = [b for b in boxes if match in str(b.name if hasattr(b, 'name') else b.get('name', ''))]
            elif isinstance(match, list):
                def matches_any(b):
                    name = str(b.name if hasattr(b, 'name') else b.get('name', ''))
                    return any(m in name for m in match)
                boxes = [b for b in boxes if matches_any(b)]
        return boxes

    def _ctx_click(self, x, y, after_sleep=0):
        """PostMessage click (background, no foreground needed)."""
        self.click_relative(x, y, after_sleep=after_sleep)

    def _ctx_real_click(self, x, y, after_sleep=0):
        """Real OS mouse click (SetCursorPos + mouse_event, not PostMessage).
        GenshinInteraction.click uses PostMessage which dropdowns ignore.
        Wrapped in gi.operate() for auto foreground/background handling."""
        import ctypes
        import win32gui
        gi = self._ensure_real_interaction()
        px, py = self._to_pixel(x, y)
        hwnd = gi.hwnd
        screen_x, screen_y = win32gui.ClientToScreen(hwnd, (px, py))
        logger.info(f'real_click: pixel=({px},{py}) screen=({screen_x},{screen_y}) hwnd={hwnd}')
        def do_real_click():
            ctypes.windll.user32.SetCursorPos(screen_x, screen_y)
            time.sleep(0.1)
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
            time.sleep(0.05)
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
        gi.operate(do_real_click, block=True)
        if after_sleep > 0:
            time.sleep(after_sleep)

    def _ctx_dbl_click(self, x, y, after_sleep=0):
        """Double PostMessage click (background)."""
        self.click_relative(x, y, after_sleep=0.1)
        self.click_relative(x, y, after_sleep=after_sleep)

    def _ctx_real_scroll(self, x, y, clicks=-3):
        """Real scroll via SetCursorPos + mouse_event (no 'mouse' package needed).
        GenshinInteraction.scroll uses 'import mouse' which may not be installed."""
        import ctypes
        import win32gui
        gi = self._ensure_real_interaction()
        px, py = self._to_pixel(x, y)
        hwnd = gi.hwnd
        screen_x, screen_y = win32gui.ClientToScreen(hwnd, (px, py))
        # Use GenshinInteraction.operate() for auto foreground/restore
        def do_scroll():
            ctypes.windll.user32.SetCursorPos(screen_x, screen_y)
            time.sleep(0.1)
            ctypes.windll.user32.mouse_event(0x0800, 0, 0, clicks * 120, 0)
        gi.operate(do_scroll, block=True)

    def _is_filter_panel_open(self):
        """Check if filter panel is open by looking for panel-specific text.
        Note: backpack top bar also has '筛选' text, so we look for panel-only
        elements like '合鸣' or star ratings in the filter panel area."""
        # Filter panel occupies roughly right half (x>0.55), and has '合鸣' text
        # which only appears when the panel is open
        return bool(self._ctx_ocr(0.55, 0.30, 1.0, 0.50, match='合鸣'))

    def _is_overlay_open(self):
        """Check if main stat overlay is open.
        Look for Cost/cost/COST or Chinese cost indicators in wider region."""
        boxes = self._ctx_ocr(0.0, 0.0, 1.0, 0.35)
        for b in (boxes or []):
            text = str(b.name if hasattr(b, 'name') else b.get('name', ''))
            if 'Cost' in text or 'cost' in text or 'COST' in text or 'ost' in text:
                return True
            # Also check for cost tab indicators like "4", "3", "1" near top
            if '主属性' in text or '确认' in text:
                return True
        return False

    def _box_center(self, b):
        """Get center coords from Box object (pixel coords)."""
        if hasattr(b, 'x'):  # Box object from framework OCR
            return b.x + b.width / 2, b.y + b.height / 2
        # dict fallback (ww_context API mode)
        return b.get('x', 0) + b.get('width', 0) / 2, b.get('y', 0) + b.get('height', 0) / 2

    def apply_backpack_filter(self, set_name_cn, cost, main_stat_cn):
        """Apply game filter. EXACT copy of test_bug2_multiround.py verified flow.
        Uses ww_context methods (same code path as test scripts)."""
        self.log_info(f'应用筛选: 套装={set_name_cn}, {cost}C, 主属性={main_stat_cn}')

        if not set_name_cn or len(set_name_cn) < 2:
            self.log_info(f'套装名无效: [{set_name_cn}]')
            return False

        # 1. Open filter panel — single click toggle (dbl_click sends 2 toggles = no change)
        for _ in range(3):
            if self._is_filter_panel_open():
                break
            self._ctx_click(0.115, 0.900, after_sleep=2)
        if not self._is_filter_panel_open():
            self.log_info('筛选面板打开失败')
            return False
        self.log_info('筛选面板已打开')

        # 2. Select set (from test_bug2_multiround.py lines 78-86)
        self._ctx_real_click(0.85, 0.454, after_sleep=2)
        found_set = False
        for scroll_attempt in range(10):
            match = self._ctx_ocr(0.6, 0.45, 1.0, 0.95, match=set_name_cn)
            if match:
                b = match[0] if isinstance(match, list) else match
                cx, cy = self._box_center(b)
                cap = self.executor.device_manager.capture_method
                self.log_info(f'OCR box: x={b.x}, y={b.y}, w={b.width}, h={b.height}, '
                              f'center=({cx},{cy}), cap={cap.width}x{cap.height}')
                self._ctx_real_click(cx, cy, after_sleep=2)
                found_set = True
                self.log_info(f'已选择套装: {set_name_cn}')
                break
            self._ctx_real_scroll(0.85, 0.65, -5)
            self.sleep(1)

        if not found_set:
            self.log_info(f'套装 [{set_name_cn}] 未找到')
            self.send_key('esc', after_sleep=0.5)
            self._close_filter_panel_ctx()
            return False

        # 3. Open overlay — click to the right of "添加" or use fixed coords
        add = self._ctx_ocr(0.6, 0.4, 1.0, 0.65, match='添加')
        if add:
            b = add[0] if isinstance(add, list) else add
            bx = b.x if hasattr(b, 'x') else b.get('x', 0)
            bw = b.width if hasattr(b, 'width') else b.get('width', 0)
            by = b.y if hasattr(b, 'y') else b.get('y', 0)
            bh = b.height if hasattr(b, 'height') else b.get('height', 0)
            cap = self.executor.device_manager.capture_method
            click_x = (bx + bw + int(0.02 * cap.width)) / cap.width
            click_y = (by + bh / 2) / cap.height
            self.log_info(f'点击添加按钮: ({click_x:.3f}, {click_y:.3f})')
            self._ctx_real_click(click_x, click_y, after_sleep=3)
        else:
            self.log_info('未找到添加文字，使用固定坐标')
            self._ctx_real_click(0.96, 0.592, after_sleep=3)

        if not self._is_overlay_open():
            self.log_info('overlay未打开，重试PostMessage click')
            if add:
                self._ctx_click(click_x, click_y, after_sleep=3)
            else:
                self._ctx_click(0.96, 0.592, after_sleep=3)

        if not self._is_overlay_open():
            self.log_info('overlay未打开')
            self._close_filter_panel_ctx()
            return False
        self.log_info('overlay已打开')

        # 4+5. Switch Cost tab FIRST for non-Cost4, then select stat
        # Key fix: stats like 攻击力百分比 appear under ALL cost tabs,
        # so searching first would always match Cost4 (default) and never switch.
        if cost != 4:
            COST_TAB = {3: (0.400, 0.216), 1: (0.645, 0.216)}
            pos = COST_TAB.get(cost)
            if pos:
                self._ctx_click(pos[0], pos[1], after_sleep=2)
                self.log_info(f'切换到 Cost{cost}')
        stat = self._ctx_ocr(0.0, 0.1, 1.0, 0.8, match=main_stat_cn)
        if not stat:
            # Debug: dump what OCR sees on the overlay
            all_overlay = self._ctx_ocr(0.0, 0.0, 1.0, 1.0)
            texts = [f'{b.name}' if hasattr(b, 'name') else str(b) for b in (all_overlay or [])]
            self.log_info(f'overlay全部文字: {texts}')

        if stat:
            b = stat[0] if isinstance(stat, list) else stat
            # Overlay elements: try click_box first (PostMessage), then real_click
            self.click_box(b, after_sleep=1)
            self.log_info(f'已选择主属性: {main_stat_cn}')
        else:
            self.log_info(f'主属性 [{main_stat_cn}] 未找到')

        # 6. Confirm (test_bug2 lines 125-129)
        confirm = self._ctx_ocr(0.0, 0.7, 1.0, 1.0, match='确认')
        if confirm:
            b = confirm[0] if isinstance(confirm, list) else confirm
            self.click_box(b, after_sleep=2)
            self.log_info('确认筛选')

        # 6.5 Read filtered count from "已筛选：N" text on filter panel
        filtered_count = self._read_filtered_count()

        # 7. Close filter panel (test_bug2 lines 136-141)
        self._close_filter_panel_ctx()
        self.sleep(2)
        self.log_info(f'筛选已应用，面板已关闭，已筛选={filtered_count}')
        return filtered_count if filtered_count > 0 else True

    def _read_filtered_count(self):
        """Read '已筛选：N' count from filter panel bottom.
        Location verified: '已筛选：' at ~(0.71,0.83), number at ~(0.75,0.83)."""
        ocr = self._ctx_ocr(0.70, 0.82, 0.90, 0.86)
        for b in (ocr or []):
            text = b.name if hasattr(b, 'name') else b.get('name', '')
            # Extract digits from text like "1", "23", "156"
            digits = ''.join(c for c in str(text) if c.isdigit())
            if digits:
                count = int(digits)
                self.log_info(f'已筛选数量: {count}')
                return count
        # Try wider region
        ocr = self._ctx_ocr(0.65, 0.80, 0.95, 0.88)
        for b in (ocr or []):
            text = b.name if hasattr(b, 'name') else b.get('name', '')
            text = str(text)
            if '筛选' in text:
                digits = ''.join(c for c in text if c.isdigit())
                if digits:
                    count = int(digits)
                    self.log_info(f'已筛选数量(wide): {count}')
                    return count
        self.log_info('未读取到筛选数量')
        return -1

    def _close_filter_panel_ctx(self):
        """Close filter panel — single click toggle, check state first."""
        for _ in range(5):
            if not self._is_filter_panel_open():
                return True
            self._ctx_click(0.115, 0.900, after_sleep=1.5)
        return not self._is_filter_panel_open()

    def reset_filter(self):
        """Reset filters — open panel, click 重置, close panel."""
        # Open panel — single click toggle
        for _ in range(3):
            if self._is_filter_panel_open():
                break
            self._ctx_click(0.115, 0.900, after_sleep=2)

        if self._is_filter_panel_open():
            reset = self._ctx_ocr(0.6, 0.75, 1.0, 0.95, match='重置')
            if reset:
                b = reset[0] if isinstance(reset, list) else reset
                self.click_box(b, after_sleep=1.5)
            # Close
            self._close_filter_panel_ctx()

        self.sleep(1)
        self.log_info('筛选已重置')

    def _read_echo_name(self):
        """Read the currently selected echo's name from the detail panel.
        Region: (0.65, 0.10, 0.85, 0.16)."""
        name_ocr = self._ctx_ocr(0.65, 0.10, 0.85, 0.16)
        for b in (name_ocr or []):
            name = str(b.name if hasattr(b, 'name') else b.get('name', ''))
            if len(name) >= 2 and not name.isdigit():
                return name
        return None

    def _click_echo_at(self, col, row=0):
        """Click echo in the grid at given column (0-based) and row.
        Grid starts at x=0.13, y=0.22 with col_step=0.075, row_step=0.14."""
        x = 0.13 + col * 0.075
        y = 0.22 + row * 0.14
        if x > 0.55:
            return False
        self._ctx_click(x, y, after_sleep=0.8)
        return True

    def _verify_echo_name(self, required_cn):
        """Verify the first filtered echo matches the required name.
        Reads detail panel name and checks substring match (OCR may be partial)."""
        # First echo should already be selected after filter
        actual = self._read_echo_name()
        if not actual:
            self.log_info('无法读取声骸名')
            return False

        # Substring match: OCR might read "異相・辛吉勒姆" while we expect "辛吉勒姆"
        if required_cn in actual or actual in required_cn:
            self.log_info(f'声骸名匹配: {actual} ✓ (期望含 {required_cn})')
            return True

        self.log_info(f'声骸名不匹配: 实际={actual}, 期望含={required_cn}')
        return False

    def _wait_enhance_button(self, timeout=5):
        """Wait for 培养 button. Uses _ctx_ocr for fresh frame + substring match."""
        start = time.time()
        while time.time() - start < timeout:
            if self._ctx_ocr(0.82, 0.86, 0.97, 0.96, match='培养'):
                self.log_info('培养按钮已出现')
                return True
            self.sleep(0.5)
        self.log_info('培养按钮未出现')
        return False

    # ===== Enhancement =====

    def run_enhance_loop(self, valid_substats, strict=True):
        """Configure and delegate to EnhanceEchoTask. Returns (success_count, fail_count).
        strict=True: >20 echoes, require first substat valid + all before crit valid
        strict=False: ≤20 echoes, relaxed — only require crit total and valid count"""
        enhancer = None
        for t in self.executor.onetime_tasks:
            if isinstance(t, EnhanceEchoTask):
                enhancer = t
                break
        if not enhancer:
            raise Exception('找不到 EnhanceEchoTask 实例')

        # Apply config — shared between strict/relaxed
        enhancer.config['有效词条'] = valid_substats
        enhancer.config['双爆总计>='] = self.config.get('双爆总计>=', 13.8)
        enhancer.config['首条双爆>='] = self.config.get('首条双爆>=', 6.9)
        enhancer.config['有效词条>='] = self.config.get('有效词条>=', 3)
        enhancer.config['必须有双爆'] = True

        # Dynamic: strict vs relaxed
        if strict:
            enhancer.config['双爆出现之前必须全有效词条'] = True
            enhancer.config['第一条必须为有效词条'] = True
        else:
            enhancer.config['双爆出现之前必须全有效词条'] = False
            enhancer.config['第一条必须为有效词条'] = False

        mode = '严格' if strict else '宽松'
        self.log_info(f'EnhanceEchoTask 配置({mode}): 副词条={valid_substats}')

        # Use original trash/lock (image-template based state detection) when available.
        # Only patch for API mode where templates (echo_dropped etc.) don't exist.
        original_trash = enhancer.trash_and_esc
        original_lock = enhancer.lock_and_esc
        need_patch = False
        try:
            enhancer.get_box_by_name('echo_dropped')
        except Exception:
            need_patch = True

        if need_patch:
            def patched_trash():
                enhancer.info_incr('失败声骸数量')
                enhancer.send_key('z', after_sleep=1.5)
                enhancer.screenshot_echo(f'failed/{enhancer.info_get("失败声骸数量")}')
                enhancer.esc()
                enhancer.wait_ocr(0.82, 0.86, 0.97, 0.96, match='培养', settle_time=0.1)

            def patched_lock():
                enhancer.info_incr('成功声骸数量')
                enhancer.send_key('c', after_sleep=1.5)
                enhancer.screenshot_echo(f'success/{enhancer.info_get("成功声骸数量")}')
                enhancer.esc()
                enhancer.wait_ocr(0.82, 0.86, 0.97, 0.96, match='培养', settle_time=0.1)

            enhancer.trash_and_esc = patched_trash
            enhancer.lock_and_esc = patched_lock

        enhancer.enable()
        enhancer.unpause()
        old_task = self.executor.current_task
        self.executor.current_task = enhancer
        try:
            enhancer.run()
            self.log_info('强化完成')
        except Exception as e:
            if '培养' in str(e):
                self.log_info(f'本轮处理完毕')
            else:
                self.log_error(f'强化异常: {e}')
        finally:
            if need_patch:
                enhancer.trash_and_esc = original_trash
                enhancer.lock_and_esc = original_lock
            enhancer.disable()
            self.executor.current_task = old_task

        success = enhancer.info.get('成功声骸数量', 0) if hasattr(enhancer, 'info') else 0
        failed = enhancer.info.get('失败声骸数量', 0) if hasattr(enhancer, 'info') else 0
        self.log_info(f'本轮结果: 成功={success}, 失败={failed}')
        return success, failed

    # ===== Config =====

    def write_enhance_config(self, valid_substats):
        """Write substats to EnhanceEchoTask.json."""
        config_path = os.path.join('configs', 'EnhanceEchoTask.json')
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

        config['有效词条'] = valid_substats
        config['双爆总计>='] = self.config.get('双爆总计>=', 13.8)
        config['首条双爆>='] = self.config.get('首条双爆>=', 6.9)
        config['有效词条>='] = self.config.get('有效词条>=', 3)
        config['必须有双爆'] = True
        config['双爆出现之前必须全有效词条'] = True
        config['第一条必须为有效词条'] = True

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        self.log_info(f'配置写入: {valid_substats}')
