import json
import re
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Tuple, Union

# 固定映射，支持前缀与正则，顺序代表优先级
RawRule = Tuple[str, str, str]
Rule = Tuple[str, Union[str, Pattern[str]], str]

RAW_RULES: List[RawRule] = [
    ("prefix", "deceasedcraft.advancement", "en_us_advancement.json"),
    ("prefix", "tooltip.translation.spacecatasb", "en_us_armors.json"),
    ("prefix", "armors", "en_us_armors.json"),
    ("prefix", "quest.combat", "en_us_combat.json"),
    ("prefix", "quest.guide", "en_us_guide.json"),
    ("prefix", "item.deceasedcraft", "en_us_items.json"),
    ("prefix", "itemGroup.deceasedTab", "en_us_items.json"),
    ("prefix", "lore.deceasedcraft", "en_us_lore.json"),
    ("prefix", "quest.main", "en_us_main.json"),
    ("prefix", "login.message", "en_us_misc.json"),
    ("prefix", "building.haunted", "en_us_misc.json"),
    ("prefix", "deceasedcraft.horde", "en_us_misc.json"),
    ("prefix", "deceasedcraft.survivor", "en_us_misc.json"),
    ("prefix", "item.minecraft", "en_us_misc.json"),
    ("prefix", "deceasedcraft.flyer", "en_us_misc.json"),
    ("prefix", "npc.deceasedcraft", "en_us_npc.json"),
    ("prefix", "skills", "en_us_skills.json"),
    ("prefix", "quest.storage", "en_us_storage.json"),
    ("prefix", "quest.technology", "en_us_tech.json"),
    ("prefix", "quest.tech", "en_us_tech.json"),
    ("prefix", "deceasedcraft.tip", "en_us_tips.json"),
    ("prefix", "quest.transport", "en_us_trans.json"),
    ("prefix", "quest.collection", "en_us_trans.json"),
    ("regex", r"^suffuse\.gun\.", "en_us_item.json"),
    ("regex", r"^gz\.gun\.", "en_us_item.json"),
    ("prefix", "quest.intro", "en_us_intro.json"),
    ("prefix", "quest.credits", "en_us_credits.json"),
]

RULES: List[Rule] = []
for kind, value, filename in RAW_RULES:
    if kind == "regex":
        RULES.append((kind, re.compile(value), filename))
    else:
        RULES.append((kind, value, filename))

SOURCE_PATH = Path("Source/original_lang/en_us.json")
OUTPUT_DIR = Path("split_output")
DEFAULT_FILE = "unassigned.json"


def load_json(path: Path) -> "OrderedDict[str, str]":
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=OrderedDict)


def pick_file(key: str) -> Optional[str]:
    for kind, matcher, filename in RULES:
        if kind == "prefix":
            if isinstance(matcher, str) and (
                key == matcher or key.startswith(matcher + ".")
            ):
                return filename
        else:  # regex
            if isinstance(matcher, re.Pattern) and matcher.search(key):
                return filename
    return None


def write_json(path: Path, data: OrderedDict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"写出 {path}，共 {len(data)} 条")


def main() -> None:
    if not SOURCE_PATH.is_file():
        raise FileNotFoundError(f"未找到源文件：{SOURCE_PATH}")

    combined = load_json(SOURCE_PATH)
    buckets: Dict[str, OrderedDict[str, str]] = defaultdict(OrderedDict)

    for key, value in combined.items():
        target = pick_file(key) or DEFAULT_FILE
        buckets[target][key] = value

    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, data in sorted(buckets.items()):
        write_json(output_dir / filename, data)

    total = len(combined)
    assigned = total - len(buckets.get(DEFAULT_FILE, {}))
    print(
        f"共处理 {total} 条，其中 {assigned} 条命中映射，"
        f"{total - assigned} 条落入 {DEFAULT_FILE}。"
    )


if __name__ == "__main__":
    main()
