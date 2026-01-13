import flet as ft
import unicodedata

# ==========================================
# PHẦN LOGIC (GIỮ NGUYÊN VÌ ĐÃ CHUẨN)
# ==========================================
CHAR_TO_CODE = {
    'a': '78', 'b': '75', 'c': '72', 'd': '69', 'e': '66', 'f': '63', 'g': '60',
    'h': '38', 'i': '36', 'j': '34', 'k': '32', 'l': '30', 'm': '28', 'n': '26',
    'o': '24', 'p': '22', 'q': '10', 'r': '9', 's': '8', 't': '7', 'u': '6',
    'v': '5', 'w': '4', 'x': '3', 'y': '2', 'z': '1', ' ': '0'
}
CODE_TO_CHAR = {v: k for k, v in CHAR_TO_CODE.items()}

DIGIT_TO_CODE = {
    '1': '9a1', '2': '8b1', '3': '9c1', '4': '8d1', '5': '9e1',
    '6': '8f1', '7': '9g1', '8': '8h1', '9': '9i1', '0': 'ao'
}
CODE_TO_DIGIT = {v: k for k, v in DIGIT_TO_CODE.items()}
CODE_TO_DIGIT['0'] = ' ' 

VARIANT_RULES = {
    'kw': {'a': 'ă', 'o': 'ơ', 'u': 'ư', 'd': 'đ'},
    'km': {'a': 'â', 'o': 'ô', 'e': 'ê'}
}
REVERSE_VARIANTS = {}
for mod, mapping in VARIANT_RULES.items():
    for base, variant in mapping.items():
        REVERSE_VARIANTS[variant] = (base, mod)

TONE_MARKS = {
    '\u0301': 's', '\u0300': 'hh', '\u0309': 'hr', '\u0303': 'dx', '\u0323': 'nn'
}
REVERSE_TONES = {v: k for k, v in TONE_MARKS.items()}

def get_char_modifiers(char):
    char_nfd = unicodedata.normalize('NFD', char)
    base_char = char_nfd[0]
    modifiers = []
    temp_chars_without_tone = [base_char]
    for c in char_nfd[1:]:
        if c in TONE_MARKS:
            modifiers.append(TONE_MARKS[c])
        else:
            temp_chars_without_tone.append(c)
    char_no_tone = unicodedata.normalize('NFC', "".join(temp_chars_without_tone))
    if char == 'đ' or base_char == 'đ' or char_no_tone == 'đ':
        return 'd', ['kw'] + modifiers
    if char_no_tone in REVERSE_VARIANTS:
        base_origin, mod_type = REVERSE_VARIANTS[char_no_tone]
        return base_origin, [mod_type] + modifiers
    return base_char, modifiers

def encode_text(text):
    text = unicodedata.normalize('NFC', text)
    result = []
    for char in text:
        lower_char = char.lower()
        if lower_char.isdigit():
            result.append(DIGIT_TO_CODE.get(lower_char, lower_char))
            continue
        base, mods = get_char_modifiers(lower_char)
        if base in CHAR_TO_CODE:
            code = CHAR_TO_CODE[base]
            unique_mods = list(dict.fromkeys(mods))
            if unique_mods:
                full_code = code + unique_mods[0]
                if len(unique_mods) > 1:
                    full_code += "".join("/" + m for m in unique_mods[1:])
                result.append(full_code)
            else:
                result.append(code)
        else:
            if char == '\n': result.append('\n')
            elif char.strip(): result.append("?") 
    final_output = []
    current_line = []
    for item in result:
        if item == '\n':
            if current_line:
                final_output.append("C(" + ".".join(current_line) + ")")
                current_line = []
            final_output.append("\n")
        else:
            current_line.append(item)
    if current_line:
        final_output.append("C(" + ".".join(current_line) + ")")
    return "".join(final_output)

def decode_brokode(text):
    lines = text.split('\n')
    decoded_lines = []
    for line in lines:
        line = line.strip()
        if not (line.startswith("C(") and line.endswith(")")):
            decoded_lines.append(line)
            continue
        content = line[2:-1]
        if not content: 
            decoded_lines.append("")
            continue
        parts = content.split('.')
        decoded_chars = []
        for part in parts:
            if part in CODE_TO_DIGIT:
                decoded_chars.append(CODE_TO_DIGIT[part])
                continue
            code_part = ""
            mod_part = ""
            for i, char in enumerate(part):
                if not char.isdigit():
                    code_part = part[:i]
                    mod_part = part[i:]
                    break
            if not code_part: code_part = part
            base_char = CODE_TO_CHAR.get(code_part, '?')
            if mod_part:
                mods = mod_part.split('/')
                for mod in mods:
                    if mod in VARIANT_RULES:
                        base_char = VARIANT_RULES[mod].get(base_char, base_char)
                tone_char = ""
                for mod in mods:
                    if mod in REVERSE_TONES:
                        tone_char = REVERSE_TONES[mod]
                        break
                if tone_char:
                    base_char = unicodedata.normalize('NFC', base_char + tone_char)
            decoded_chars.append(base_char)
        decoded_lines.append("".join(decoded_chars))
    return "\n".join(decoded_lines)

# ==========================================
# GIAO DIỆN DARK MODE (SAFE VERSION)
# ==========================================
def main(page: ft.Page):
    # Cấu hình an toàn: Không force màu đen nền, để Flet tự xử lý Dark Mode
    page.title = "Brokode"
    page.theme_mode = ft.ThemeMode.DARK # Chế độ tối
    page.scroll = "adaptive" # Cho phép cuộn nếu màn hình nhỏ
    page.padding = 20

    # Hàm đổi theme
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            btn_theme.icon = ft.icons.DARK_MODE # Icon mặt trăng (chuẩn)
        else:
            page.theme_mode = ft.ThemeMode.DARK
            btn_theme.icon = ft.icons.WB_SUNNY # Icon mặt trời (chuẩn)
        page.update()

    btn_theme = ft.IconButton(
        icon=ft.icons.WB_SUNNY, 
        on_click=toggle_theme,
        tooltip="Đổi giao diện"
    )

    page.appbar = ft.AppBar(
        title=ft.Text("Brokode V3.1", weight="bold"),
        center_title=True,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[btn_theme]
    )

    # Ô kết quả (Bỏ hiệu ứng mờ phức tạp để tránh lỗi render)
    txt_result = ft.TextField(
        label="Kết quả",
        multiline=True,
        read_only=True,
        min_lines=5,
        text_size=18,
        border_radius=10,
        filled=True
    )

    def on_input_change(e):
        try:
            content = e.control.value.strip()
            if not content:
                txt_result.value = ""
            elif content.startswith("C(") and content.endswith(")"):
                txt_result.value = decode_brokode(content)
            else:
                txt_result.value = encode_text(content)
            page.update()
        except Exception as ex:
            txt_result.value = f"Lỗi: {str(ex)}"
            page.update()

    txt_input = ft.TextField(
        label="Nhập văn bản",
        hint_text="Nhập tiếng Việt hoặc mã...",
        multiline=True,
        min_lines=3,
        on_change=on_input_change,
        text_size=16,
        border_radius=10,
        autofocus=True
    )

    def copy_result(e):
        page.set_clipboard(txt_result.value)
        page.show_snack_bar(ft.SnackBar(ft.Text("Đã copy!")))

    btn_copy = ft.ElevatedButton(
        "Sao chép", 
        icon=ft.icons.COPY, 
        on_click=copy_result,
        height=45
    )

    # Dùng SafeArea để tránh bị tai thỏ che mất nội dung
    page.add(
        ft.SafeArea(
            ft.Column(
                [
                    txt_input,
                    ft.Divider(),
                    txt_result,
                    ft.Container(height=10), # Khoảng cách
                    btn_copy
                ],
                spacing=10
            )
        )
    )

ft.app(target=main)
