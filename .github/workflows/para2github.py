import json
import os
import re
from pathlib import Path
from typing import Tuple, Dict, List
import nbtlib
from nbtlib.tag import Compound, String, Int
import requests

TOKEN: str = os.getenv("API_TOKEN", "")
GH_TOKEN: str = os.getenv("GH_TOKEN", "")
PROJECT_ID: str = os.getenv("PROJECT_ID", "")
FILE_URL: str = f"https://paratranz.cn/api/projects/{PROJECT_ID}/files/"

MERGE_SOURCE_PATH: str = "kubejs/assets/vm/lang/"
MERGE_OUTPUT_FILE: str = "CNPack/kubejs/assets/deceasedcraft/lang/zh_cn.json"

if not TOKEN or not PROJECT_ID:
    raise EnvironmentError("环境变量 API_TOKEN 或 PROJECT_ID 未设置。")

file_id_list: list[int] = []
file_path_list: list[str] = []
zh_cn_list: list[dict[str, str]] = []


def fetch_json(url: str, headers: dict[str, str]) -> list[dict[str, str]]:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def translate(file_id: int) -> Tuple[list[str], list[str]]:
    url = f"https://paratranz.cn/api/projects/{PROJECT_ID}/files/{file_id}/translation"
    headers = {"Authorization": TOKEN, "accept": "*/*"}
    translations = fetch_json(url, headers)

    keys, values = [], []
    for item in translations:
        keys.append(item["key"])
        translation = item.get("translation", "")
        original = item.get("original", "")
        values.append(
            original if item["stage"] in [0, -1] or not translation else translation
        )

    return keys, values


def get_files() -> None:
    headers = {"Authorization": TOKEN, "accept": "*/*"}
    files = fetch_json(FILE_URL, headers)
    for file in files:
        file_id_list.append(file["id"])
        file_path_list.append(file["name"])


def set_nested_value(d: dict, path_str: str, value: str, delimiter: str = "->"):
    """
    根据带分隔符的 key 路径（如 "entries->qmp_a.120mm_high.description"）
    递归设置嵌套字典中的值。
    """
    keys = path_str.split(delimiter)
    curr = d
    for key in keys[:-1]:
        if key not in curr or not isinstance(curr[key], dict):
            curr[key] = {}
        curr = curr[key]
    curr[keys[-1]] = value


def build_nested_dict(flat_dict: dict[str, str]) -> dict:
    """
    将带有 '->' 的扁平字典整体还原为层级嵌套字典
    """
    nested_res = {}
    nested_count = 0
    for k, v in flat_dict.items():
        if "->" in k:
            set_nested_value(nested_res, k, v, delimiter="->")
            nested_count += 1
        else:
            nested_res[k] = v
    print(f"[DEBUG] 字典还原完成，共有 {nested_count} 个键使用了 '->' 层级分隔符展开。")
    return nested_res


def save_translation(zh_cn_dict: dict[str, str], path: Path) -> None:
    dir_path = Path("CNPack") / path.parent
    if "vm" in str(dir_path):
        dir_path = Path(str(dir_path).replace("vm", "deceasedcraft"))
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / "zh_cn.json"
    source_path = str(file_path).replace("zh_cn.json", "en_us.json").replace("CNPack", "Source")

    print(f"[DEBUG] 正在处理文件: {path}")
    print(f"[DEBUG] 目标保存位置: {file_path}")
    print(f"[DEBUG] 尝试匹配源文件: {source_path}")

    with open(file_path, "w", encoding="UTF-8") as f:
        try:
            with open(source_path, "r", encoding="UTF-8") as f1:
                source_json: dict = json.load(f1)
            print(f"[DEBUG] 成功读取源文件: {source_path}")

            for key, val in zh_cn_dict.items():
                if "->" in key:
                    set_nested_value(source_json, key, val, delimiter="->")
                else:
                    source_json[key] = val

            json.dump(source_json, f, ensure_ascii=False, indent=4, separators=(",", ":"))
            print(f"[SUCCESS] 已按 Source 原文件层级合并保存: {file_path}")
        except IOError:
            print(f"[WARNING] 源文件不存在: {source_path}，转为自动构建嵌套结构模式")
            nested_data = build_nested_dict(zh_cn_dict)
            json.dump(nested_data, f, ensure_ascii=False, indent=4, separators=(",", ":"))
            print(f"[SUCCESS] 自动嵌套构建完成并保存: {file_path}")


def process_translation(file_id: int, path: Path) -> dict[str, str]:
    keys, values = translate(file_id)

    try:
        with open("Source/" + str(path), "r", encoding="UTF-8") as f:
            zh_cn_dict = json.load(f)
    except IOError:
        zh_cn_dict = {}

    is_quest_file = "vm" in str(path)

    for key, value in zip(keys, values):
        value = re.sub(r'\\"', '"', value)
        if is_quest_file and "image" not in value:
            value = value.replace(" ", "\u00A0")
        zh_cn_dict[key] = value

    return zh_cn_dict


def json_to_nbt(data):
    if isinstance(data, dict):
        return Compound({key: json_to_nbt(value) for key, value in data.items()})
    elif isinstance(data, list):
        return nbtlib.tag.List[nbtlib.tag.String]([json_to_nbt(item) for item in data])
    elif isinstance(data, str):
        return String(data)
    elif isinstance(data, int):
        return Int(data)
    else:
        raise ValueError(f"Unsupported data type: {type(data)}")


def format_snbt(nbt_data, indent=0):
    INDENT_SIZE = 4
    indent_str = ' ' * indent

    if isinstance(nbt_data, Compound):
        formatted = ['{']
        for key, value in nbt_data.items():
            formatted.append(f'\n{indent_str}{" " * INDENT_SIZE}{key}:{format_snbt(value, indent + INDENT_SIZE)}')
        formatted.append(f'\n{indent_str}}}')
        return ''.join(formatted)
    elif isinstance(nbt_data, nbtlib.tag.List):
        formatted = ['[']
        for item in nbt_data:
            formatted.append(f'\n{indent_str}{" " * INDENT_SIZE}{format_snbt(item, indent + INDENT_SIZE)}')
        formatted.append(f'\n{indent_str}]')
        return ''.join(formatted)
    else:
        return f'"{str(nbt_data)}"'


def escape_quotes(data):
    if isinstance(data, dict):
        return {key: escape_quotes(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [escape_quotes(item) for item in data]
    elif isinstance(data, str):
        return data.replace('"', '\\"')
    else:
        return data


def normal_json2_ftb_desc(origin_en_us):
    en_json = json.dumps(origin_en_us, ensure_ascii=False, indent=4, separators=(",", ":"))
    en_json = eval(en_json)
    temp_set = set()
    temp_en_json = {}
    for key, value in list(en_json.items()):
        if "desc" in key:
            key_id = key.split(".")[1]
            temp_json_array = []
            for k in en_json.keys():
                if f"{key_id}.quest_desc" in k:
                    temp_json_array.append(en_json[k])
            new_key = f"quest.{key_id}.quest_desc"
            temp_en_json[new_key] = temp_json_array
            temp_set.add(key)
    for key in temp_set:
        en_json.pop(key, None)
    en_json.update(temp_en_json)

    print("NormalJson2FtbDesc end...")
    return en_json


def main() -> None:
    get_files()
    ftbquests_dict = {}
    merged_translations: Dict[str, str] = {}

    for file_id, path_str in zip(file_id_list, file_path_list):
        if "TM" in path_str:
            continue

        path = Path(path_str)
        zh_cn_dict = process_translation(file_id, path)

        if path_str.startswith(MERGE_SOURCE_PATH) and path_str.endswith(".json"):
            merged_translations.update(zh_cn_dict)
            print(f"[INFO] 已暂存待合并文件：{path_str} (当前累计 key 数: {len(merged_translations)})")
        else:
            zh_cn_list.append(zh_cn_dict)
            if "kubejs/assets/quests/lang/" in path_str:
                ftbquests_dict.update(zh_cn_dict)
            save_translation(zh_cn_dict, path)
            print(f"[INFO] 已完成保存：{re.sub('en_us.json', 'zh_cn.json', str(path))}")

    if merged_translations:
        print(f"\n[INFO] 开始处理合并文件导出 -> {MERGE_OUTPUT_FILE}")
        output_path = Path(MERGE_OUTPUT_FILE)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        source_path = str(output_path).replace("zh_cn.json", "en_us.json").replace("CNPack", "Source")
        print(f"[DEBUG] 合并文件尝试匹配源文件: {source_path}")

        try:
            with open(source_path, "r", encoding="UTF-8") as f1:
                source_json: dict = json.load(f1)
            print(f"[DEBUG] 成功读取合并文件的 Source 源文件: {source_path}")
            for key, val in merged_translations.items():
                if "->" in key:
                    set_nested_value(source_json, key, val, delimiter="->")
                else:
                    source_json[key] = val
            output_data = source_json
        except IOError:
            print(f"[WARNING] 无法找到源文件 {source_path}，将从合并的键自动构建嵌套结构")
            output_data = build_nested_dict(merged_translations)

        with open(output_path, "w", encoding="UTF-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4, separators=(",", ":"))
        print(f"[SUCCESS] 合并文件写入成功：{MERGE_OUTPUT_FILE}\n")

    if len(ftbquests_dict) > 0:
        snbt_dict = normal_json2_ftb_desc(ftbquests_dict)
        json_data = escape_quotes(snbt_dict)
        nbt_data = json_to_nbt(json_data)
        formatted_snbt_string = format_snbt(nbt_data)
        try:
            with open('CNPack/config/ftbquests/quests/lang/zh_cn.snbt', 'w', encoding='utf-8') as snbt_file:
                snbt_file.write(formatted_snbt_string)
        except Exception as e:
            print("该ftbquest版本低于1.21.1")


if __name__ == "__main__":
    main()