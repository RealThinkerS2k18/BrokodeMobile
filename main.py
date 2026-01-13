import flet as ft
import unicodedata

# ==========================================
# PHẦN LOGIC (ĐÃ FIX LỖI HOÀN TOÀN)
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
                # 1. Biến thể kw/km
                for mod in mods:
                    if mod in VARIANT_RULES:
                        base_char = VARIANT_RULES[mod].get(base_char, base_char)
                
                # 2. Dấu thanh (ĐÃ FIX: Check trực tiếp key)
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
# GIAO DIỆN MOBILE ULTIMATE (DARK MODE)
# ==========================================
def main(page: ft.Page):
    # Cấu hình mặc định: DARK MODE + NỀN ĐEN
    page.title = "Brokode Ultimate"
    page.scroll = "hidden" # Ẩn thanh cuộn để đẹp hơn
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "black" # Màu đen hoàn toàn (AMOLED)
    page.padding = 0 # Full màn hình

    # Hàm đổi giao diện Sáng/Tối
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = "white"
            btn_theme.icon = ft.icons.DARK_MODE
            btn_theme.tooltip = "Chuyển sang Tối"
        else:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = "black"
            btn_theme.icon = ft.icons.LIGHT_MODE
            btn_theme.tooltip = "Chuyển sang Sáng"
        page.update()

    # Thanh tiêu đề (AppBar)
    btn_theme = ft.IconButton(
        icon=ft.icons.LIGHT_MODE, 
        on_click=toggle_theme, 
        tooltip="Chuyển giao diện"
    )
    
    page.appbar = ft.AppBar(
        title=ft.Text("Brokode V3", weight="bold", size=22),
        center_title=True,
        bgcolor=ft.colors.BLUE_GREY_900,
        actions=[btn_theme]
    )

    # Ô hiển thị kết quả
    txt_result = ft.TextField(
        label="Kết quả dịch",
        multiline=True,
        read_only=True,
        min_lines=6,
        text_size=18,
        border_radius=15,
        filled=True, # Có màu nền
        bgcolor=ft.colors.with_opacity(0.1, ft.colors.WHITE), # Nền mờ nhẹ
        border_color=ft.colors.TRANSPARENT,
    )

    # Xử lý sự kiện nhập liệu
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

    # Ô nhập liệu
    txt_input = ft.TextField(
        label="Nhập văn bản",
        hint_text="Gõ Tiếng Việt hoặc dán mã Brokode...",
        multiline=True,
        min_lines=4,
        max_lines=6,
        on_change=on_input_change,
        text_size=16,
        border_radius=15,
        border_color=ft.colors.BLUE_400,
        focused_border_color=ft.colors.BLUE_200,
    )

    # Nút Copy
    def copy_result(e):
        page.set_clipboard(txt_result.value)
        page.show_snack_bar(ft.SnackBar(ft.Text("Đã copy vào bộ nhớ tạm!"), bgcolor="green"))

    btn_copy = ft.ElevatedButton(
        "Sao chép kết quả", 
        icon=ft.icons.COPY, 
        on_click=copy_result,
        height=50,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            bgcolor=ft.colors.BLUE_700,
            color="white"
        )
    )

    # Bố cục chính (Container bọc ngoài để tạo khoảng cách đẹp)
    content_container = ft.Container(
        padding=20,
        content=ft.Column(
            [
                txt_input,
                ft.Divider(height=20, color="transparent"),
                txt_result,
                ft.Divider(height=20, color="transparent"),
                ft.Container(content=btn_copy, alignment=ft.alignment.center)
            ],
            scroll="adaptive"
        )
    )

    page.add(content_container)

ft.app(target=main)
