from typing import List, Dict

KEY_WIDTH = 8  # Width of each key in the ASCII layout
LAYER_KEYS = {"MO(1)", "MO(2)", "MO(3)"}
TRANSPARENT_KEYS = {"_______", "TRANSPARENT", "TRNS"}

def format_key(key: str, pressed_keys: List[str] = None) -> str:
    normalized_key = key.strip().upper().replace(" ", "")
    is_pressed = (
        pressed_keys and normalized_key in [k.strip().upper().replace(" ", "") for k in pressed_keys]
    )
    if is_pressed:
        return "  HLD   "  # For held layer keys
    if normalized_key in LAYER_KEYS:
        return f"[{key.center(KEY_WIDTH - 2)}]"
    if normalized_key in TRANSPARENT_KEYS:
        return "  ...   "
    return f"{key:^{KEY_WIDTH}}"  # Center-align with padding

def format_row(row: List[str], max_len: int, pressed_keys: List[str] = None) -> str:
    padded = row + [""] * (max_len - len(row))
    return "| " + " | ".join(format_key(k, pressed_keys) for k in padded) + " |"

def generate_ascii_layer(
    name: str,
    rows: List[List[str]],
    thumbs: List[str] = None,
    pressed_keys: List[str] = None
) -> str:
    layout = [f"/*", f" * {name}"]

    if not rows and not thumbs:
        layout.append(" * No keys defined for this layer")
        layout.append(" */")
        return "\n".join(layout)

    all_rows = rows + ([thumbs] if thumbs else [])

    if all_rows and any(r for r in all_rows):
        max_length = max(len(row) for row in all_rows if row)
    else:
        max_length = 1

    # Calculate exact width by formatting a sample row
    if rows and rows[0]:
        sample_row = format_row(rows[0], max_length, pressed_keys)
        actual_width = len(sample_row)
    else:
        actual_width = (KEY_WIDTH + 3) * max_length - 1

    # Add curved borders
    top_border = " * ," + "-" * (actual_width - 2) + "."
    layout.append(top_border)

    for i, row in enumerate(rows):
        layout.append(" * " + format_row(row, max_length, pressed_keys))

        if i < len(rows) - 1:
            separator = " * |" + "-" * (actual_width - 2) + "|"
            layout.append(separator)

    bottom_border = " * `" + "-" * (actual_width - 2) + "'"
    layout.append(bottom_border)

    # Add thumb cluster if defined
    if thumbs:
        formatted_thumbs = [format_key(k, pressed_keys) for k in thumbs if k]
        thumb_string = " | ".join(formatted_thumbs)
        thumb_width = len(thumb_string) + 2

        # Center the thumb cluster under the keyboard
        left_padding = (actual_width - thumb_width) // 2
        if left_padding < 0: left_padding = 0

        centered_thumb_row = " " * left_padding + "| " + thumb_string + " |"
        layout.append(f" *{centered_thumb_row}")

        thumb_border = " " * left_padding + "`" + "-" * (thumb_width) + "'"
        layout.append(f" *{thumb_border}")

    layout.append(" */")
    return "\n.join(layout)

def format_half_row(row, width, pressed_keys=None):
    formatted_keys = [format_key(k, pressed_keys) for k in row if k]

    while len(formatted_keys) < width:
        formatted_keys.append("         ")

    return "|" + "|".join(formatted_keys) + "|"

def horizontal_bar(width):
    return "|" + "|".join("-" * KEY_WIDTH for _ in range(width)) + "|"

def pad_half(row_half: list, width: int) -> list:
    return row_half + [""] * (width - len(row_half))

def generate_split_ascii_layer(name, rows, thumbs=None, pressed_keys=None, split_at=6):
    layout = ["/*", f" * {name}"]
    spacer = " " * (KEY_WIDTH * 5)  # Space between keyboard halves

    if not rows and not thumbs:
        layout.append(" * No keys defined for this layer")
        layout.append(" */")
        return "\n".join(layout)

    all_rows = rows + ([thumbs] if thumbs else [])

    # Calculate widths for each half
    left_widths = [0] * len(rows)
    right_widths = [0] * len(rows)

    for i, row in enumerate(rows):
        if not row:
            continue

        row_split = split_at
        left_widths[i] = min(row_split, len(row))
        right_widths[i] = max(0, len(row) - row_split)

    left_width = max(left_widths) if left_widths else split_at
    right_width = max(right_widths) if right_widths else 6

    # Draw keyboard halves with curved borders
    top_border_left = "," + "-" * ((KEY_WIDTH + 1) * left_width - 1) + "."
    top_border_right = "," + "-" * ((KEY_WIDTH + 1) * right_width - 1) + "."
    layout.append(f" * {top_border_left}{spacer}{top_border_right}")

    for i, row in enumerate(rows):
        row_split = split_at
        left = row[:row_split] if len(row) > 0 else []
        right = row[row_split:] if row_split < len(row) else []

        layout.append(f" * {format_half_row(left, left_width, pressed_keys)}{spacer}{format_half_row(right, right_width, pressed_keys)}")

        if i < len(rows) - 1:
            layout.append(f" * {horizontal_bar(left_width)}{spacer}{horizontal_bar(right_width)}")

    # Bottom curved border connecting to thumb clusters
    main_layout_width = ((KEY_WIDTH + 1) * left_width)
    bottom_left = "`" + "-" * main_layout_width + "-" * KEY_WIDTH + "\\"
    bottom_spacer = " " * ((KEY_WIDTH * 3) - 2)
    bottom_right = "/" + "-" * KEY_WIDTH + "-" * (KEY_WIDTH + 1) * right_width + "'"
    layout.append(f" * {bottom_left}{bottom_spacer}{bottom_right}")

    # Add thumb clusters
    if thumbs:
        total_thumbs = len(thumbs)
        left_count = (total_thumbs + 1) // 2
        right_count = total_thumbs - left_count

        left_thumb = thumbs[:left_count]
        right_thumb = thumbs[left_count:]

        # Calculate indent for thumb clusters
        num_keys_indent = len(left) - len(left_thumb) + 1
        thumb_indent = " " * (num_keys_indent * (KEY_WIDTH + 1))

        left_formatted_keys = [format_key(k, pressed_keys) for k in left_thumb if k]
        right_formatted_keys = [format_key(k, pressed_keys) for k in right_thumb if k]

        left_thumb_str = "|".join(left_formatted_keys)
        right_thumb_str = "|".join(right_formatted_keys)

        left_formatted = f"|{left_thumb_str}|" if left_thumb_str else ""
        right_formatted = f"|{right_thumb_str}|" if right_thumb_str else ""

        left_cluster_end = len(thumb_indent) + len(left_formatted)
        center_gap_size = len(bottom_spacer)
        center_gap = " " * center_gap_size

        layout.append(f" * {thumb_indent}{left_formatted}{center_gap}{right_formatted}")

        # Add curved borders for thumb clusters
        if left_thumb_str:
            left_bottom = "`" + "-" * (len(left_formatted) - 2) + "/"
        else:
            left_bottom = ""

        if right_thumb_str:
            right_bottom = "\\" + "-" * (len(right_formatted) - 2) + "'"
        else:
            right_bottom = ""

        layout.append(f" * {thumb_indent}{left_bottom}{center_gap}{right_bottom}")

    layout.append(" */")
    return "\n.join(layout)

def generate_totem_ascii_layer(name, rows, thumbs=None, pressed_keys=None):
    """Special formatter for the Totem keyboard with its asymmetric layout"""
    layout = ["/*", f" * {name}"]
    spacer = " " * (KEY_WIDTH * 5)

    if not rows and not thumbs:
        layout.append(" * No keys defined for this layer")
        layout.append(" */")
        return "\n.join(layout)

    # Calculate indent for the shorter rows (1-2)
    indent_chars = (KEY_WIDTH + 1) * 1
    row_indent = " " * indent_chars

    # Calculate row widths for the Totem's 3 rows (10-10-12 keys layout)
    row_1_width = min(5, len(rows[0]) if len(rows) > 0 else 0)
    row_2_width = min(5, len(rows[1]) if len(rows) > 1 else 0)
    row_3_left_width = min(6, len(rows[2]) if len(rows) > 2 else 0)
    row_3_right_width = max(0, len(rows[2]) - 6 if len(rows) > 2 else 0)

    # Draw indented top borders for first row
    top_border_left = "," + "-" * ((KEY_WIDTH + 1) * row_1_width - 1) + "."
    top_border_right = "," + "-" * ((KEY_WIDTH + 1) * row_1_width - 1) + "."
    layout.append(f" * {row_indent}{top_border_left}{spacer}{top_border_right}")

    # First row (indented, 5 keys per side)
    if len(rows) > 0:
        left = rows[0][:5] if rows[0] else []
        right = rows[0][5:10] if rows[0] and len(rows[0]) > 5 else []
        layout.append(f" * {row_indent}{format_half_row(left, row_1_width, pressed_keys)}{spacer}{format_half_row(right, row_1_width, pressed_keys)}")
        layout.append(f" * {row_indent}{horizontal_bar(row_1_width)}{spacer}{horizontal_bar(row_1_width)}")

    # Second row (indented, 5 keys per side)
    if len(rows) > 1:
        left = rows[1][:5] if rows[1] else []
        right = rows[1][5:10] if rows[1] and len(rows[1]) > 5 else []
        layout.append(f" * {row_indent}{format_half_row(left, row_2_width, pressed_keys)}{spacer}{format_half_row(right, row_2_width, pressed_keys)}")

        # Special connector between rows 2 and 3 (connects the indented rows to the full-width row)
        left_slant = "/" + "-" * KEY_WIDTH
        right_slant = "-" * KEY_WIDTH + "\\"
        layout.append(f" * {left_slant}{horizontal_bar(row_1_width)}{spacer}{horizontal_bar(row_1_width)}{right_slant}")

    # Third row (full width, 6 keys per side)
    if len(rows) > 2:
        left = rows[2][:6] if rows[2] else []
        right = rows[2][6:] if rows[2] and len(rows[2]) > 6 else []
        layout.append(f" * {format_half_row(left, row_3_left_width, pressed_keys)}{spacer}{format_half_row(right, row_3_right_width, pressed_keys)}")

    # Bottom curved border
    bottom_left_width = (KEY_WIDTH + 1) * row_3_left_width + KEY_WIDTH
    bottom_right_width = (KEY_WIDTH + 1) * row_3_right_width + KEY_WIDTH
    bottom_left = "`" + "-" * bottom_left_width + "\\"
    bottom_spacer = " " * ((KEY_WIDTH * 3) - 1)
    bottom_right = "/" + "-" * bottom_right_width + "'"
    layout.append(f" * {bottom_left}{bottom_spacer}{bottom_right}")

    # Add thumb clusters
    if thumbs:
        total_thumbs = len(thumbs)
        left_count = (total_thumbs + 1) // 2
        right_count = total_thumbs - left_count

        left_thumb = thumbs[:left_count]
        right_thumb = thumbs[left_count:]

        num_keys_indent = len(left) - len(left_thumb) + 1
        thumb_indent = " " * (num_keys_indent * (KEY_WIDTH + 1))

        left_formatted_keys = [format_key(k, pressed_keys) for k in left_thumb if k]
        right_formatted_keys = [format_key(k, pressed_keys) for k in right_thumb if k]

        left_thumb_str = "|".join(left_formatted_keys)
        right_thumb_str = "|".join(right_formatted_keys)

        left_formatted = f"|{left_thumb_str}|" if left_thumb_str else ""
        right_formatted = f"|{right_thumb_str}|" if right_thumb_str else ""

        left_cluster_end = len(thumb_indent) + len(left_formatted)
        center_gap_size = len(bottom_spacer)
        center_gap = " " * center_gap_size

        layout.append(f" * {thumb_indent}{left_formatted}{center_gap}{right_formatted}")

        # Add curved borders for thumb clusters
        if left_thumb_str:
            left_bottom = "`" + "-" * (len(left_formatted) - 2) + "/"
        else:
            left_bottom = ""

        if right_thumb_str:
            right_bottom = "\\" + "-" * (len(right_formatted) - 2) + "'"
        else:
            right_bottom = ""

        layout.append(f" * {thumb_indent}{left_bottom}{center_gap}{right_bottom}")

    layout.append(" */")
    return "\n.join(layout)

def generate_for_keyboard(
    keyboard: str,
    keyboard_data: dict,
    split_index: int = None
) -> str:
    outputs = []

    # Extract configuration
    config = keyboard_data.get("config", {})
    is_split = config.get("is_split", False)
    default_split = config.get("split_at", 6)

    # Get layers from keyboard data
    layers = keyboard_data.get("layers", {})
    if not layers and "base" in keyboard_data:
        layers = keyboard_data  # Handle old format

    # Generate layouts for each layer
    for layer_name, layer_data in layers.items():
        if layer_name == "config":
            continue

        rows = layer_data.get("rows", [])
        thumbs = layer_data.get("thumbs", [])
        pressed_keys = layer_data.get("pressed", [])

        if is_split:
            current_split = split_index or default_split

            if keyboard == "totem":
                outputs.append(generate_totem_ascii_layer(
                    f"{keyboard.upper()} - {layer_name.upper()} Layer",
                    rows,
                    thumbs,
                    pressed_keys
                ))
            else:
                outputs.append(generate_split_ascii_layer(
                    f"{keyboard.upper()} - {layer_name.upper()} Layer",
                    rows,
                    thumbs,
                    pressed_keys,
                    split_at=current_split
                ))
        else:
            outputs.append(generate_ascii_layer(
                f"{keyboard.upper()} - {layer_name.upper()} Layer",
                rows,
                thumbs,
                pressed_keys
            ))
        outputs.append("")

    return "\n.join(outputs)

# Keyboard templates with layouts defined for different keyboards
keyboard_templates: Dict[str, Dict[str, List[List[str]]]] = {
   "reviung41": {
        "config": {
            "is_split": False,
            "split_at": None,
            "thumb_count": 5,
        },
        "base": {
            "rows": [
                ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "Esc"],
                ["Ctrl", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'"],
                ["GUI", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Enter"],
            ],
            "thumbs": ["MO(1)", "Shift", "Space", "Bksp", "MO(2)"],
            "pressed": []
        },
        "mo1": {
            "rows": [[]],
            "thumbs": ["MO(1)", "Shift", "Space", "Bksp", "MO(3)"],
            "pressed": ["MO(1)"]
        },
        "mo2": {
            "rows": [],
            "thumbs": [],
            "pressed": ["MO(2)"]
        },
        "mo3": {
            "rows": [],
            "thumbs": [],
            "pressed": ["MO(1)", "MO(2)"]
        }
    },
    "sofle": {
        "config": {
            "is_split": True,
            "split_at": 6,
            "thumb_count": 10,
        },
        "base": {
            "rows": [
                ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "Esc"],
                ["\\", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "Alt"],
                ["Ctrl", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'"],
                ["GUI", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Enter"],
            ],
            "thumbs": ["-", "=", "MO(1)", "Shift", "Tab", "Space", "Bksp", "MO(2)", "[", "]"],
            "pressed": []
        },
        "mo1": {
            "rows": [
                ["TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS"],
                [",", ".", "7", "8", "9", ";", "Vol+", "Prev", "Play", "Next", "TRNS", "TRNS"],
                ["TRNS", "TRNS", "4", "5", "6", "-", "Vol-", "Ctrl", "Shift", "Alt", "GUI", "TRNS"],
                ["TRNS", "0", "1", "2", "3", "=", "Mute", "TRNS", "TRNS", "TRNS"]
            ],
            "thumbs": ["{", "}", "MO(3)", "TRNS", "TRNS", "TRNS", "TRNS", "MO(1)", "TRNS", "TRNS"],
            "pressed": ["MO(1)"]
        },
        "mo2": {
            "rows": [
                ["TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS"],
                ["Insert", "PgUp", "PrtSc", "Up", "CapsWord", "Home", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS"],
                ["Del", "PgDn", "Left", "Down", "Right", "End", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS"],
                ["TRNS", "M1", "TRNS", "M2", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS"],
            ],
            "thumbs": ["TRNS", "TRNS", "MO(2)", "TRNS", "TRNS", "TRNS", "Del", "MO(3)", "TRNS", "TRNS"],
            "pressed": ["MO(2)"]
        },
        "mo3": {
            "rows": [
                ["Reset", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "Reset"],
                ["TRNS", "TRNS", "F7", "F8", "F9", "F10", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS"],
                ["TRNS", "TRNS", "F4", "F5", "F6", "F11", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS"],
                ["TRNS", "TRNS", "F1", "F2", "F3", "F12", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS", "TRNS"],
            ],
            "thumbs": ["TRNS", "TRNS", "MO(1)", "TRNS", "TRNS", "TRNS", "TRNS", "MO(2)", "TRNS", "TRNS"],
            "pressed": ["MO(1)", "MO(2)"]
        }
    },
    "corne": {
        "config": {
            "is_split": True,
            "split_at": 6,
            "thumb_count": 6,
        },
        "base": {
            "rows": [
                ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "Esc"],
                ["Ctrl", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'"],
                ["GUI", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Enter"],
            ],
            "thumbs": ["MO(1)", "Shift", "Tab", "Space", "Bksp", "MO(2)"],
            "pressed": []
        },
        "mo1": {
            "rows": [],
            "thumbs": [],
            "pressed": ["MO(1)"]
        },
        "mo2": {
            "rows": [],
            "thumbs": [],
            "pressed": ["MO(2)"]
        },
        "mo3": {
            "rows": [],
            "thumbs": [],
            "pressed": ["MO(1)", "MO(2)"]
        }
    },
    "totem": {
        "config": {
            "is_split": True,
            "split_at": 5,  # First two rows have 5 keys per half
            "thumb_count": 6,
        },
        "base": {
            "rows": [
                ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
                ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
                ["Ctrl", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Enter"],
            ],
            "thumbs": ["MO(1)", "Shift", "Tab", "Space", "Bksp", "MO(2)"],
            "pressed": []
        },
        "mo1": {
            "rows": [],
            "thumbs": [],
            "pressed": ["MO(1)"]
        },
        "mo2": {
            "rows": [],
            "thumbs": [],
            "pressed": ["MO(2)"]
        },
        "mo3": {
            "rows": [],
            "thumbs": [],
            "pressed": ["MO(1)", "MO(2)"]
        }
    }
}

if __name__ == "__main__":
    # Print layouts for each keyboard
    for keyboard_name in keyboard_templates:
        print(generate_for_keyboard(keyboard_name, keyboard_templates[keyboard_name]))
