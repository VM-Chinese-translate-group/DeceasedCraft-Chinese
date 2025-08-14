import json

# 文件路径
file_path = 'CNPack\\kubejs\\assets\\deceasedcraft\\lang\\zh_cn.json'

try:
    # 读取JSON文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 遍历JSON数据，移除以'npc.deceasedcraft'开头的键对应的值中的换行符
    for key, value in data.items():
        if key.startswith('npc.deceasedcraft') and isinstance(value, str):
            data[key] = value.replace('\n', '')

    # 将修改后的内容写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"文件 '{file_path}' 已成功处理，换行符已被移除。")

except FileNotFoundError:
    print(f"错误：找不到文件 '{file_path}'。请确保文件存在于当前目录中。")
except json.JSONDecodeError:
    print(f"错误：文件 '{file_path}' 不是一个有效的JSON文件。")
except Exception as e:
    print(f"处理文件时发生未知错误：{e}")