"""
BOLT ⚡ — Rewards Engine
🎁 Points system — earn by using the bot
🏆 Levels — progress from Bronze to Legend
🔥 Streak — daily check-in bonuses
"""

POINTS = {
    "add_token": 10,
    "change_name": 5,
    "check_info": 2,
    "check_links": 2,
    "validate_token": 1,
}

LEVELS = {
    1: {"name": " Bronze", "name_ar": "🥉 برونزي", "min": 0},
    2: {"name": "🥈 Silver", "name_ar": "🥈 فضي", "min": 50},
    3: {"name": "🥇 Gold", "name_ar": "🥇 ذهبي", "min": 150},
    4: {"name": " Platinum", "name_ar": "💎 بلاتيني", "min": 350},
    5: {"name": "👑 Diamond", "name_ar": "👑 ألماسي", "min": 700},
    6: {"name": "🔥 Master", "name_ar": "🔥 ماستر", "min": 1200},
    7: {"name": " Grandmaster", "name_ar": "⚡ غراند ماستر", "min": 2000},
    8: {"name": "🏆 Legend", "name_ar": "🏆 أسطوري", "min": 3500},
}


def get_level_info(level: int) -> dict:
    return LEVELS.get(level, LEVELS[1])


def get_next_level(level: int) -> dict | None:
    return LEVELS.get(level + 1)


def progress_to_next(points: int, level: int) -> int:
    nxt = get_next_level(level)
    if not nxt:
        return 100
    current_min = LEVELS[level]["min"]
    total_needed = nxt["min"] - current_min
    if total_needed <= 0:
        return 100
    return min(100, int(((points - current_min) / total_needed) * 100))


def format_reward_card(points: int, level: int, streak: int, total_earned: int) -> str:
    info = get_level_info(level)
    nxt = get_next_level(level)
    prog = progress_to_next(points, level)
    filled = prog // 10
    bar = "█" * filled + "░" * (10 - filled)

    lines = [
        f"🏆 <b>بطاقة المكافآت</b>",
        f"━━━━━━━━━━━━━━━━━",
        f"",
        f"📊 المستوى: {info['name_ar']}",
        f"⭐ النقاط: {points}",
        f"🔥 السلسلة: {streak} يوم",
        f"📈 الإجمالي: {total_earned}",
        f"",
    ]

    if nxt:
        lines.extend([
            f"📊 التقدم: [{bar}] {prog}%",
            f"🎯 المطلوب: {nxt['min']} نقطة",
        ])
    else:
        lines.append("🌟 أعلى مستوى! أنت أسطوري!")

    lines.append(f"━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)
