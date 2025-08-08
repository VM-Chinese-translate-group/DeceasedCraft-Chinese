import json

def process_npc_dialogue(input_file, output_file, line_length=35):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {input_file}")
        return
    except json.JSONDecodeError:
        print(f"错误：文件 {input_file} 的JSON格式无效。")
        return

    for key, value in data.items():
        if key.startswith('npc.deceasedcraft') and isinstance(value, str):
            cleaned_text = value.replace('\\n', ' ').replace('\n', ' ')
            
            if not cleaned_text:
                continue

            wrapped_text = '\n'.join([cleaned_text[i:i + line_length] for i in range(0, len(cleaned_text), line_length)])
            data[key] = wrapped_text

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"处理完成！已将结果保存到 {output_file}")
    except IOError:
        print(f"错误：无法写入文件 {output_file}")

input_filename = 'CNPack\\kubejs\\assets\\deceasedcraft\\lang\\zh_cn.json'
output_filename = 'CNPack\\kubejs\\assets\\deceasedcraft\\lang\\zh_cn.json'
process_npc_dialogue(input_filename, output_filename)