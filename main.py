import flet as ft
import unicodedata

# ==========================================
# PHẦN LOGIC (ĐÃ SỬA LỖI MẤT DẤU MŨ/RÂU)
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
    # Bước 1: Tách ký tự thành các thành phần nhỏ (NFD)
    char_nfd = unicodedata.normalize('NFD', char)
    base_char = char_nfd[0] # Lấy chữ cái gốc (ví dụ 'ừ' -> gốc là 'u')
    modifiers = []
    
    # Danh sách tạm để tái tạo chữ cái không có dấu thanh (để check kw/km)
    temp_chars_without_tone = [base_char]

    # Bước 2: Duyệt qua các dấu đi kèm
    for c in char_nfd[1:]:
        if c in TONE_MARKS:
            # Nếu là dấu thanh (sắc huyền...) thì đưa vào danh sách mod
            modifiers.append(TONE_MARKS[c])
        else:
            # Nếu không phải dấu thanh (ví dụ dấu mũ, dấu râu), giữ lại để check kw/km
            temp_chars_without_tone.append(c)
    
    # Bước 3: Tái tạo chữ cái chỉ có mũ/râu (ví dụ 'ừ' -> tái tạo thành 'ư')
    char_no_tone = unicodedata.normalize('NFC', "".join(temp_chars_without_tone))
    
    # Xử lý riêng chữ đ (vì đ đôi khi không tách được bằng NFD trên một số hệ thống)
    if char == 'đ' or base_char == 'đ' or char_no_tone == 'đ':
        return 'd', ['kw'] + modifiers

    # Bước 4: Check xem chữ tái tạo có phải là biến thể (ă, â, ê, ô, ơ, ư) không
    if char_no_tone in REVERSE_VARIANTS:
        base_origin, mod_type = REVERSE_VARIANTS[char_no_tone]
        # Thêm mod loại kw/km vào đầu danh sách
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
        
        # Gọi hàm xử lý mới đã fix lỗi
        base, mods = get_char_modifiers(lower_char)
        
        if base in CHAR_TO_CODE:
            code = CHAR_TO_CODE[base]
            unique_mods = list(dict.fromkeys(mods))
            if unique_mods:
                # Format: code + mod1 + / + mod2...
                full_code = code + unique_mods[0]
                if len(unique_mods) > 1:
                    full_code += "".join("/" + m for m in unique_mods[1:])
                result.append(full_code)
            else:
                result.append(code)
        else:
            # Giữ nguyên ký tự lạ (xuống dòng, dấu câu...)
            if char == '\n': 
                result.append('\n')
            elif char.strip(): 
                result.append("?") 
    
    # Xử lý ghép chuỗi output đẹp hơn
    final_str = "C(" + ".".join([r for r in result if r != '\n']) + ")"
    # Nếu có xuống dòng thì xử lý hiển thị (tạm thời để simple)
    return final_str

def decode_brokode(text):
    text = text.strip()
    if not (text.startswith("C(") and text.endswith(")")):
        return text 
    content = text[2:-1]
    if not content: return ""
    parts = content.split('.')
    decoded = []
    for part in parts:
        if part in CODE_TO_DIGIT:
            decoded.append(CODE_TO_DIGIT[part])
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
            # Áp dụng kw/km trước
            for mod in mods:
                if mod in VARIANT_RULES:
                    base_char = VARIANT_RULES[mod].get(base_char, base_char)
            # Áp dụng dấu thanh sau
            tone_char = ""
            for mod in mods:
                if mod in REVERSE_TONES.values():
                    for u_char, u_name in TONE_MARKS.items():
                        if u_name == mod:
                            tone_char = u_char
                            break
            if tone_char:
                base_char = unicodedata.normalize('NFC', base_char + tone_char)
        decoded.append(base_char)
    return "".join(decoded)

# ==========================================
# GIAO DIỆN MOBILE
# ==========================================
def main(page: ft.Page):
    page.title = "Brokode Fixed"
    page.scroll = "adaptive"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20

    lbl_title = ft.Text("Brokode V2.1 (Fix dấu)", size=24, weight="bold")
    
    txt_result = ft.TextField(
        label="Kết quả",
        multiline=True,
        read_only=True,
        min_lines=5,
        text_size=16,
        border_color="blue"
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
        label="Nhập nội dung",
        hint_text="Thử nhập: ừ, ắ, ệ...",
        multiline=True,
        min_lines=3,
        on_change=on_input_change,
        text_size=16
    )

    def copy_result(e):
        page.set_clipboard(txt_result.value)
        page.show_snack_bar(ft.SnackBar(ft.Text("Đã copy!")))

    btn_copy = ft.ElevatedButton("Copy Kết quả", on_click=copy_result)

    page.add(
        ft.Column(
            [
                lbl_title,
                txt_input,
                ft.Divider(),
                txt_result,
                btn_copy
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START
        )
    )

ft.app(target=main)
