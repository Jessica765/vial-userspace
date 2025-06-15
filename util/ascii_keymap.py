from typing import List, Dict
import json

KEY_WIDTH = 8  # Width of each key in the ASCII layout
LAYER_KEYS = {"MO(1)", "MO(2)", "MO(3)"}
TRANSPARENT_KEYS = {"_______", "TRANSPARENT", "TRNS"}

def convert_from_vial(vial_file_path: str, keyboard_name: str = "custom") -> dict:
    """Convert Vial JSON keymap to keyboard template format"""
    with open(vial_file_path, 'r') as f:
        vial_data = json.load(f)

    layout = vial_data.get("layout", [])
    encoder_layout = vial_data.get("encoder_layout", [])

    # Detect keyboard type based on layout structure
    if not layout:
        return {}

    # Count keys in first layer to determine keyboard type
    total_keys = sum(len(row) for row in layout[0] if row)

    # Determine if it's split and configuration
    config = {
        "is_split": True,  # Most keyboards in your templates are split
        "split_at": 6,     # Default split point
        "thumb_count": 6,  # Default thumb count
        "has_encoders": len(encoder_layout) > 0,
        "encoder_count": len(encoder_layout[0]) if encoder_layout else 0
    }

    # Auto-detect based on key count
    if total_keys >= 58:  # Sofle-like (54 + thumb cluster)
        config["thumb_count"] = 10
        config["split_at"] = 6
    elif total_keys >= 42:  # Corne-like
        config["thumb_count"] = 6
        config["split_at"] = 6
    elif total_keys >= 36:  # Totem-like
        config["thumb_count"] = 6
        config["split_at"] = 5

    # Convert layers
    template = {"config": config}

    layer_names = ["base", "mo1", "mo2", "mo3"]

    for i, layer in enumerate(layout[:4]):  # Process up to 4 layers
        layer_name = layer_names[i] if i < len(layer_names) else f"layer{i}"        # Separate main rows from thumb cluster
        # In Vial format for Sofle: rows 0-4 are left half, rows 5-9 are right half
        # Row structure: [left_row0, left_row1, left_row2, left_row3, left_thumbs, right_row0, right_row1, right_row2, right_row3, right_thumbs]
        main_rows = []
        thumbs = []

        if len(layer) == 10:  # Sofle format with separate left/right halves
            left_main = layer[:4]   # rows 0-3 are left main keys
            left_thumbs = layer[4]  # row 4 is left thumb keys
            right_main = layer[5:9] # rows 5-8 are right main keys
            right_thumbs = layer[9] # row 9 is right thumb keys

            # Combine left and right halves
            for i in range(4):
                left_row = left_main[i] if i < len(left_main) else []
                right_row = right_main[i] if i < len(right_main) else []
                combined_row = left_row + right_row
                main_rows.append(combined_row)

            # Combine thumb clusters
            thumbs = left_thumbs + right_thumbs
        else:
            # For other formats: first 4 rows are main, last row is thumbs
            if len(layer) >= 5:
                main_rows = layer[:4]
                thumbs = layer[4] if len(layer) > 4 else []
            else:
                main_rows = layer

        # Convert key codes and fix right half inversion
        converted_rows = []
        split_at = config["split_at"]

        for row in main_rows:
            if not row:  # Skip empty rows
                converted_rows.append([])
                continue

            converted_row = [convert_keycode(key) for key in row]

            # Fix right half inversion for split keyboards
            if config["is_split"] and len(converted_row) > split_at:
                left_half = converted_row[:split_at]
                right_half = converted_row[split_at:]
                # Reverse the right half to fix the inversion
                right_half.reverse()
                converted_row = left_half + right_half

            converted_rows.append(converted_row)        # Handle thumb cluster - fix the right half inversion
        converted_thumbs = []
        if thumbs:
            converted_thumbs = [convert_keycode(key) for key in thumbs]
            # For Sofle with 10 thumb keys: [L1, L2, L3, L4, L5, R5, R4, R3, R2, R1]
            # We want: [L1, L2, L3, L4, L5, R1, R2, R3, R4, R5]
            if config["is_split"] and len(converted_thumbs) >= 10:
                # Take only the first 10 keys and fix the inversion
                converted_thumbs = converted_thumbs[:10]
                left_thumbs = converted_thumbs[:5]
                right_thumbs = converted_thumbs[5:]
                right_thumbs.reverse()
                converted_thumbs = left_thumbs + right_thumbs
            elif config["is_split"] and len(converted_thumbs) == 6:
                left_thumbs = converted_thumbs[:3]
                right_thumbs = converted_thumbs[3:]
                right_thumbs.reverse()
                converted_thumbs = left_thumbs + right_thumbs

        # Handle encoders
        converted_encoders = []
        if i < len(encoder_layout) and encoder_layout[i]:
            for encoder in encoder_layout[i]:
                if len(encoder) >= 2:
                    # Convert CCW and CW actions
                    ccw = convert_keycode(encoder[0])
                    cw = convert_keycode(encoder[1])
                    converted_encoders.append([ccw, cw])        # Determine pressed keys for layer
        pressed_keys = []
        if i == 0:  # Base layer
            pressed_keys = []
        elif i == 1:  # MO(1) layer
            pressed_keys = ["MO(1)"]
        elif i == 2:  # MO(2) layer
            pressed_keys = ["MO(2)"]
        elif i == 3:  # MO(3) layer (combo)
            pressed_keys = ["MO(1)", "MO(2)"]

        layer_data = {
            "rows": converted_rows,
            "thumbs": converted_thumbs,
            "pressed": pressed_keys
        }

        # Add encoders if they exist for this layer
        if converted_encoders:
            layer_data["encoders"] = converted_encoders

        template[layer_name] = layer_data

    return {keyboard_name: template}

def convert_keycode(keycode: str) -> str:
    """Convert QMK/Vial keycode to readable format"""
    if not keycode or keycode == "KC_NO":
        return ""

    # Remove KC_ prefix
    if keycode.startswith("KC_"):
        keycode = keycode[3:]

    # Handle special cases
    keycode_map = {
        "TRNS": "TRNS",
        "TRANSPARENT": "TRNS",
        "GRAVE": "`",
        "BSLASH": "\\",
        "LCTRL": "Ctrl",
        "LGUI": "GUI",
        "MINUS": "-",
        "EQUAL": "=",
        "LSHIFT": "Shift",
        "ESCAPE": "Esc",
        "LALT": "Alt",
        "QUOTE": "'",
        "SCOLON": ";",
        "ENTER": "Enter",
        "SLASH": "/",
        "DOT": ".",
        "COMMA": ",",
        "SPACE": "Space",
        "TAB": "Tab",
        "BSPACE": "Bksp",
        "DELETE": "Del",
        "MUTE": "Mute",
        "VOLU": "Vol+",
        "VOLD": "Vol-",
        "MPRV": "Prev",
        "MPLY": "Play",
        "MNXT": "Next",
        "RESET": "Reset",
        "PGUP": "PgUp",
        "PGDN": "PgDn",
        "PSCR": "PrtSc",
        "UP": "Up",
        "DOWN": "Down",
        "LEFT": "Left",
        "RIGHT": "Right",
        "HOME": "Home",
        "END": "End",
        "INS": "Insert",
        "CAPS": "CapsLock",
        "RBRACKET": "]",
        "LBRACKET": "[",
        "PSCREEN": "PrtSc",
        "INSERT": "Insert",
        "PGDOWN": "PgDn",
    }

    # Handle function keys
    if keycode.startswith("F") and keycode[1:].isdigit():
        return keycode

    # Handle numbers and letters
    if keycode.isdigit() or (len(keycode) == 1 and keycode.isalpha()):
        return keycode

    # Handle MO() layer keys
    if keycode.startswith("MO(") and keycode.endswith(")"):
        return keycode

    # Handle hex codes (like "0x7c73")
    if keycode.startswith("0x"):
        return keycode

    # Handle macro keys (M1, M2, etc.)
    if keycode.startswith("M") and keycode[1:].isdigit():
        return keycode

    # Use mapping or return as-is
    return keycode_map.get(keycode, keycode)

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
    return "\n".join(layout)

def format_half_row(row, width, pressed_keys=None):
    formatted_keys = [format_key(k, pressed_keys) for k in row if k]

    while len(formatted_keys) < width:
        formatted_keys.append("         ")

    return "|" + "|".join(formatted_keys) + "|"

def horizontal_bar(width):
    return "|" + "|".join("-" * KEY_WIDTH for _ in range(width)) + "|"

def pad_half(row_half: list, width: int) -> list:
    return row_half + [""] * (width - len(row_half))

def generate_split_ascii_layer(name, rows, thumbs=None, encoders=None, pressed_keys=None, split_at=6):
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
    right_width = max(right_widths) if right_widths else 6    # Draw keyboard halves with curved borders
    top_border_left = "," + "-" * ((KEY_WIDTH + 1) * left_width - 1) + "."
    top_border_right = "," + "-" * ((KEY_WIDTH + 1) * right_width - 1) + "."
    layout.append(f" * {top_border_left}{spacer}{top_border_right}")

    for i, row in enumerate(rows):
        row_split = split_at
        left = row[:row_split] if len(row) > 0 else []
        right = row[row_split:] if row_split < len(row) else []        # Add encoders to the 4th row (index 3) on the inside edge
        if i == 3 and encoders:
            left_encoder = encoders[0] if len(encoders) > 0 else ["", ""]
            right_encoder = encoders[1] if len(encoders) > 1 else ["", ""]

            # Format encoder display as "CCW/CW"
            left_enc_display = f"{left_encoder[0]}/{left_encoder[1]}" if len(left_encoder) >= 2 else ""
            right_enc_display = f"{right_encoder[0]}/{right_encoder[1]}" if len(right_encoder) >= 2 else ""
              # Add encoder to inside edge of each half
            left_with_encoder = left + [left_enc_display] if left_enc_display else left
            right_with_encoder = [right_enc_display] + right if right_enc_display else right

            layout.append(f" * {format_half_row(left_with_encoder, left_width + (1 if left_enc_display else 0), pressed_keys)}{spacer}{format_half_row(right_with_encoder, right_width + (1 if right_enc_display else 0), pressed_keys)}")
        else:
            layout.append(f" * {format_half_row(left, left_width, pressed_keys)}{spacer}{format_half_row(right, right_width, pressed_keys)}")

        if i < len(rows) - 1:
            # Calculate separator widths to match the next row
            next_left_width = left_width
            next_right_width = right_width

            # If the next row (i+1) will have encoders, adjust separator width
            if (i + 1) == 3 and encoders:
                left_has_encoder = len(encoders) > 0 and encoders[0] and any(encoders[0])
                right_has_encoder = len(encoders) > 1 and encoders[1] and any(encoders[1])
                next_left_width += 1 if left_has_encoder else 0
                next_right_width += 1 if right_has_encoder else 0

            # Generate separators with proper spacing to avoid wrapping
            left_separator_parts = ["-" * KEY_WIDTH for _ in range(next_left_width)]
            right_separator_parts = ["-" * KEY_WIDTH for _ in range(next_right_width)]

            separator_left = "|" + "|".join(left_separator_parts) + "|"
            separator_right = "|" + "|".join(right_separator_parts) + "|"
            layout.append(f" * {separator_left}{spacer}{separator_right}")

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
    return "\n".join(layout)

def generate_totem_ascii_layer(name, rows, thumbs=None, pressed_keys=None):
    """Special formatter for the Totem keyboard with its asymmetric layout"""
    layout = ["/*", f" * {name}"]
    spacer = " " * (KEY_WIDTH * 5)

    if not rows and not thumbs:
        layout.append(" * No keys defined for this layer")
        layout.append(" */")
        return "\n".join(layout)

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
    return "\n".join(layout)

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
        layers = keyboard_data  # Handle old format    # Generate layouts for each layer
    for layer_name, layer_data in layers.items():
        if layer_name == "config":
            continue

        rows = layer_data.get("rows", [])
        thumbs = layer_data.get("thumbs", [])
        encoders = layer_data.get("encoders", [])
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
                    encoders,
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

    return "\n".join(outputs)

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
    # Convert a Vial keymap file to a keyboard template
    vial_file_path = "../keyboards/sofle/rev1/keymaps/base/vial_layout.json"
    converted_template = convert_from_vial(vial_file_path, "sofle")

    print(f"Converted Sofle keyboard layout from Vial:")
    print("="*60)
    for keyboard_name, keyboard_data in converted_template.items():
        result = generate_for_keyboard(keyboard_name, keyboard_data)
        print(result)

    # Print layouts for each predefined keyboard template
    # for keyboard_name in keyboard_templates:
    #     print(generate_for_keyboard(keyboard_name, keyboard_templates[keyboard_name]))
