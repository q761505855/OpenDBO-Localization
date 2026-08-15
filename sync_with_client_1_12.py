#!/usr/bin/python3
"""Align the Simplified Chinese resources with the OpenDBO 1.12 client.

The client RDF and language files are the canonical source for keys and order.
Existing Simplified Chinese values are retained for matching keys. Missing
translations fall back to the client text, and keys absent from the client are
removed.
"""

import argparse
import shutil
import struct
import xml.etree.ElementTree as ET
from pathlib import Path


TABLE_TEXT = "table_text_all_data"
TABLE_QUEST = "table_quest_text_data"
DATA_FILES = ("local_data.dat", "local_sync_data.dat")
ALM_FILES = ("local_msg_type.alm", "local_sync_msg_type.alm")


# Strings present in the 1.12 client but absent from the newer CN resource set.
# The Korean resources are the semantic source; established CN terminology is
# used for item and system names.
TABLE_TRANSLATIONS = {
    TABLE_TEXT: {
        "111900060": "神秘时装胶囊 2",
        "111900061": "打开后可随机获得一套时装！",
        "111900070": "神秘时装胶囊 3",
        "111900071": "打开后可随机获得一套时装！",
    }
}

DATA_TRANSLATIONS = {
    "local_data.dat": {
        # An empty value terminates CNtlTokenizerW parsing because the client
        # mistakes the empty token for EOF.  The Korean/TW files leave this
        # entry blank, but the English client supplies the intended meaning.
        "DST_SKILL_RPBONUS_TOOLTIP_RESULT_PERCENT": "技能威力提高 %d%%。",
        "DST_POPUP_ITEMBOX_LVTWO": "[font size = \"9\" color=\"269eff\"]等级礼盒[/font][font size = \"9\" color=\"#323232\"]内含赠送道具。[br]打开胶囊盒（快捷键 I），右键单击等级礼盒即可使用。[/font]",
        "DST_POPUP_CONTENT_ITEM_SKYSKILL": "[font size = \"9\" color=\"269eff\"]EV 舞空术体验卷轴[/font][font size = \"9\" color=\"#323232\"]连续按两次空格键升空，然后使用方向键移动。持续时间共 3 分钟，详情请查看帮助（H）。[/font]",
        "DST_POPUP_CONTENT_ITEM_VEHICLE": "[font size = \"9\" color=\"269eff\"]飞天松鼠喷射器·试用型 [7天][/font][font size = \"9\" color=\"#323232\"]右键单击即可乘坐，按 ESC 键下车。有效期为 7 天。[/font]",
        "DST_POPUP_CONTENT_ITEM_VEHICLEFUEL": "[font size = \"9\" color=\"269eff\"]EV 液体燃料 S2 [7天][/font][font size = \"9\" color=\"#323232\"]载具专用燃料，使用后可提高行驶速度。有效期为 7 天。[/font]",
        "DST_POPUP_CONTENT_ITEM_EXP": "[font size = \"9\" color=\"269eff\"]EV 初级修炼卷轴 [2小时][/font][font size = \"9\" color=\"#323232\"]使用后获得的经验值提高 50%，仅限 1～30 级角色使用，效果持续 2 小时。[/font]",
        "DST_POPUP_CONTENT_ITEM_LIFE": "[font size = \"9\" color=\"269eff\"]EV 生命药剂 X[/font][font size = \"9\" color=\"#323232\"]用于恢复 LP。LP 代表生命值，归零后角色会昏厥。可在屏幕左上角的角色状态栏查看当前 LP。[/font]",
        "DST_POPUP_CONTENT_ITEM_ENERGY": "[font size = \"9\" color=\"269eff\"]EV 能量药剂 X[/font][font size = \"9\" color=\"#323232\"]用于恢复 EP。EP 是施放技能所需的能量，EP 不足时无法使用技能。可在屏幕左上角的角色状态栏查看当前 EP。[/font]",
        "DST_POPUP_CONTENT_ITEM_CAPSULEKIT": "[font size = \"9\" color=\"269eff\"]红心胶囊盒 N20 [15天][/font][font size = \"9\" color=\"#323232\"]使用后增加 20 格储物空间，有效期为 15 天。右键单击后会自动装备到胶囊盒栏位。[/font]",
        "DST_POPUP_CONTENT_ITEM_WEAPONINTENSIFY": "[font size = \"9\" color=\"269eff\"]+12 武器强化券 Lv11 [2天][/font][font size = \"9\" color=\"#323232\"]可将尚未强化的武器临时强化至 +12，且不会失败。效果仅持续 2 天，请注意使用期限。[/font]",
        "DST_POPUP_CONTENT_ITEM_DEFENSEINTENSIFY": "[font size = \"9\" color=\"269eff\"]+12 防具强化券 Lv11 [2天][/font][font size = \"9\" color=\"#323232\"]可将尚未强化的防具临时强化至 +12，且不会失败。效果仅持续 2 天，请注意使用期限。[/font]",
        "DST_POPUP_CONTENT_ITEM_POPOJEWELRYBOX": "[font size = \"9\" color=\"269eff\"]波波的饰品箱 Lv11[/font][font size = \"9\" color=\"#323232\"]内含适合 11 级角色使用的饰品。右键单击后可随机获得戒指、耳环或项链。[/font]",
        "DST_POPUP_CONTENT_ITEM_AUTOMATICLIFE": "[font size = \"9\" color=\"269eff\"]EV 自动 LP 恢复盒 100000[/font][font size = \"9\" color=\"#323232\"]LP 降至 30% 以下时会自动恢复至 100%，最多可恢复 100000 点 LP。[/font]",
        "DST_POPUP_CONTENT_ITEM_AUTOMATICENERGY": "[font size = \"9\" color=\"269eff\"]EV 自动 EP 恢复盒 100000[/font][font size = \"9\" color=\"#323232\"]EP 降至 30% 以下时会自动恢复至 100%，最多可恢复 100000 点 EP。[/font]",
        "DST_POPUP_CONTENT_ITEM_POPOPIECE": "[font size = \"9\" color=\"269eff\"]EV 波波碎片[/font][font size = \"9\" color=\"#323232\"]角色昏厥后可选择使用，使自己在原地复活。[/font]",
        "DST_POPUP_CONTENT_ITEM_TELEPOPOP": "[font size = \"9\" color=\"269eff\"]EV 无线波波[/font][font size = \"9\" color=\"#323232\"]可将自己传送到已登记的波波石所在地。[/font]",
        "DST_POPUP_CONTENT_ITEM_SPEEDINCREASE": "[font size = \"9\" color=\"269eff\"]EV 移动速度提升药剂[/font][font size = \"9\" color=\"#323232\"]使用后移动速度提高 20%，持续 10 分钟。[/font]",
        "DST_SHUTDOWN_WARNING": "根据未成年人防沉迷规定，当前时段无法进行游戏。请于上午 6 点后再试。",
        "DST_SHUTDOWN_WARNING_MSG": "[align = \"center\"][font size = \"12\" color=\"f4d762\"]游戏时段限制[/font][br][br][font size = \"10\" color=\"ffffff\"]根据未成年人防沉迷规定，当前时段无法进行游戏。请于上午 6 点后再试。[/font][br][br][font size = \"10\" color=\"ffffff\"][/font]",
        "DST_COMMERCIAL_WAGU1ST": "%s 从现金扭蛋机中获得了 %s。",
        "DST_DELIBERATION_RANK_MESSAGE_0": "登录游戏已满 %d 小时。",
        "DST_DELIBERATION_RANK_MESSAGE_LASTMSG": "过度游戏会影响正常生活，请合理安排游戏时间。",
    },
    "local_sync_data.dat": {
        "GAME_TRADE_BLACKLIST": "无法与该玩家进行交易。",
        "SHUTDOWN_SELECT_WARNING_1HOUR": "根据账号设置的游戏时段限制，距离强制下线还有 1 小时，请合理安排游戏时间。",
        "SHUTDOWN_SELECT_WARNING_30MINUTE": "根据账号设置的游戏时段限制，距离强制下线还有 30 分钟，请合理安排游戏时间。",
        "SHUTDOWN_SELECT_WARNING_MSG": "[align = \"center\"][font size = \"12\" color=\"f4d762\"]游戏时间限制[/font][br][br][font size = \"10\" color=\"ffffff\"]当前账号受到游戏时段限制，只能在允许的时段内进行游戏。如有疑问，请联系客户服务。[/font][br][br][font size = \"10\" color=\"ffffff\"][/font]",
    },
}


def read_text_rdf(path):
    payload = path.read_bytes()
    sections = []
    position = 0

    while position < len(payload):
        if position + 9 > len(payload):
            raise ValueError("truncated text RDF section header: {}".format(path))

        section_index, section_size = struct.unpack_from("<II", payload, position)
        section_start = position + 8
        section_end = section_start + section_size
        if section_end > len(payload) or section_size < 1:
            raise ValueError("invalid text RDF section size: {}".format(path))

        record_position = section_start + 1  # one padding byte
        records = []
        while record_position < section_end:
            if record_position + 6 > section_end:
                raise ValueError("truncated text RDF record: {}".format(path))
            record_id, text_size = struct.unpack_from("<IH", payload, record_position)
            record_position += 6
            text_end = record_position + text_size * 2
            if text_end > section_end:
                raise ValueError("invalid text RDF string size: {}".format(path))
            text = payload[record_position:text_end].decode("utf-16le")
            record_position = text_end
            records.append((str(record_id), text))

        if section_index != len(sections):
            raise ValueError(
                "unexpected section index {} at position {}".format(section_index, len(sections))
            )
        sections.append(records)
        position = section_end

    return sections


def read_quest_rdf(path):
    payload = path.read_bytes()
    if not payload:
        raise ValueError("empty quest RDF: {}".format(path))

    records = []
    position = 1  # one leading padding byte
    while position < len(payload):
        if position + 6 > len(payload):
            raise ValueError("truncated quest RDF record: {}".format(path))
        record_id, text_size = struct.unpack_from("<IH", payload, position)
        position += 6
        text_end = position + text_size * 2
        if text_end > len(payload):
            raise ValueError("invalid quest RDF string size: {}".format(path))
        text = payload[position:text_end].decode("utf-16le")
        position = text_end
        records.append((str(record_id), text))
    return [records]


def read_xml_sections(path):
    root = ET.parse(str(path)).getroot()
    return [
        [(text.get("id"), text.text or "") for text in table_data.findall("text")]
        for table_data in root.findall("table_data")
    ]


def assert_unique(records, label):
    keys = [record_id for record_id, _ in records]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate IDs in {}".format(label))


def valid_xml_character(character):
    value = ord(character)
    return (
        value in (0x09, 0x0A, 0x0D)
        or 0x20 <= value <= 0xD7FF
        or 0xE000 <= value <= 0xFFFD
        or 0x10000 <= value <= 0x10FFFF
    )


def sanitize_xml_text(text):
    return "".join(character for character in text if valid_xml_character(character))


def indent(element, level=0):
    whitespace = "\n" + "  " * level
    if len(element):
        if not element.text or not element.text.strip():
            element.text = whitespace + "  "
        for child in element:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = whitespace
    if level and (not element.tail or not element.tail.strip()):
        element.tail = whitespace


def synchronize_table(client_sections, localized_path, translations=None):
    translations = translations or {}
    localized_sections = read_xml_sections(localized_path)
    output_sections = []
    translated = 0
    fallback = 0
    removed = 0

    for section_index, client_records in enumerate(client_sections):
        assert_unique(client_records, "client section {}".format(section_index))
        localized_records = (
            localized_sections[section_index]
            if section_index < len(localized_sections)
            else []
        )
        assert_unique(localized_records, "localized section {}".format(section_index))
        localized_values = dict(localized_records)
        client_keys = {record_id for record_id, _ in client_records}
        removed += sum(record_id not in client_keys for record_id, _ in localized_records)

        output_records = []
        for record_id, client_text in client_records:
            if record_id in translations:
                value = translations[record_id]
                if record_id in localized_values:
                    translated += 1
                else:
                    fallback += 1
            elif record_id in localized_values:
                value = localized_values[record_id]
                translated += 1
            else:
                value = sanitize_xml_text(client_text)
                fallback += 1
            output_records.append((record_id, value))
        output_sections.append(output_records)

    removed += sum(len(section) for section in localized_sections[len(client_sections):])

    root = ET.Element("table")
    for records in output_sections:
        table_data = ET.SubElement(root, "table_data")
        for record_id, value in records:
            text = ET.SubElement(table_data, "text", id=record_id)
            text.text = value
    indent(root)
    ET.ElementTree(root).write(
        str(localized_path), encoding="utf-8", xml_declaration=True
    )

    written_sections = read_xml_sections(localized_path)
    expected_keys = [[record_id for record_id, _ in section] for section in client_sections]
    written_keys = [[record_id for record_id, _ in section] for section in written_sections]
    if written_keys != expected_keys:
        raise RuntimeError("written table keys do not match the client: {}".format(localized_path))

    return translated, fallback, removed


def decode_text_file(path):
    payload = path.read_bytes()
    if payload.startswith(b"\xff\xfe"):
        return payload[2:].decode("utf-16le")
    if payload.startswith(b"\xef\xbb\xbf"):
        return payload.decode("utf-8-sig")
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        return payload.decode("gb18030")


def read_data_rows(path):
    rows = []
    for line_number, line in enumerate(decode_text_file(path).splitlines(), 1):
        if not line.strip():
            continue
        if "=" not in line:
            raise ValueError("invalid data line {} in {}".format(line_number, path))
        key, value = line.split("=", 1)
        rows.append((key.strip(), value))
    return rows


def encode_data_value(value):
    return '"{}"'.format(value.replace('"', '""'))


def synchronize_data_file(client_path, localized_path, translations=None):
    translations = translations or {}
    client_rows = read_data_rows(client_path)
    localized_rows = read_data_rows(localized_path)
    assert_unique(client_rows, "client {}".format(client_path.name))

    localized_values = {}
    for key, value in localized_rows:
        localized_values[key] = value  # matches the client's last-value-wins parser

    client_keys = {key for key, _ in client_rows}
    removed = sum(key not in client_keys for key in localized_values)
    translated = 0
    fallback = 0
    output_lines = []
    for key, client_value in client_rows:
        if key in translations:
            value = encode_data_value(translations[key])
            if key in localized_values:
                translated += 1
            else:
                fallback += 1
        elif key in localized_values:
            value = localized_values[key]
            translated += 1
        else:
            value = client_value
            fallback += 1
        output_lines.append("{}={}".format(key, value))

    output = "\r\n".join(output_lines) + "\r\n"
    localized_path.write_bytes(b"\xff\xfe" + output.encode("utf-16le"))

    written_keys = [key for key, _ in read_data_rows(localized_path)]
    expected_keys = [key for key, _ in client_rows]
    if written_keys != expected_keys:
        raise RuntimeError("written data keys do not match the client: {}".format(localized_path))

    return translated, fallback, removed, len(localized_rows) - len(localized_values)


def main():
    repository = Path(__file__).resolve().parent
    default_client = repository.parent / "OpenDBO-Core-1.12" / "DboClient" / "DragonBall"

    argument_parser = argparse.ArgumentParser(
        description="Synchronize Simplified Chinese keys with an OpenDBO 1.12 client"
    )
    argument_parser.add_argument(
        "client_root",
        nargs="?",
        type=Path,
        default=default_client,
        help="DragonBall client directory",
    )
    arguments = argument_parser.parse_args()

    client_root = arguments.client_root.resolve()
    localized_root = repository / "Simplified Chinese (CN)"
    data_root = localized_root / "data"
    language_root = localized_root / "language"

    text_stats = synchronize_table(
        read_text_rdf(client_root / "data" / (TABLE_TEXT + ".rdf")),
        data_root / (TABLE_TEXT + ".xml"),
        TABLE_TRANSLATIONS.get(TABLE_TEXT),
    )
    quest_stats = synchronize_table(
        read_quest_rdf(client_root / "data" / (TABLE_QUEST + ".rdf")),
        data_root / (TABLE_QUEST + ".xml"),
    )

    print("{}: kept={}, fallback={}, removed={}".format(TABLE_TEXT, *text_stats))
    print("{}: kept={}, fallback={}, removed={}".format(TABLE_QUEST, *quest_stats))

    for filename in DATA_FILES:
        stats = synchronize_data_file(
            client_root / "language" / filename,
            language_root / filename,
            DATA_TRANSLATIONS.get(filename),
        )
        print(
            "{}: kept={}, fallback={}, removed={}, duplicate_inputs={}".format(
                filename, *stats
            )
        )

    for filename in ALM_FILES:
        client_path = client_root / "language" / filename
        localized_path = language_root / filename
        shutil.copyfile(str(client_path), str(localized_path))
        if localized_path.read_bytes() != client_path.read_bytes():
            raise RuntimeError("ALM copy verification failed: {}".format(filename))
        print("{}: copied exact client structure".format(filename))


if __name__ == "__main__":
    main()
