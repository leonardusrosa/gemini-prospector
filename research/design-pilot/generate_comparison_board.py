import os
from PIL import Image, ImageDraw, ImageFont

def make_board():
    a_desk_path = "research/design-pilot/a-baseline/desktop.png"
    b_desk_path = "research/design-pilot/b-opendesign/desktop.png"
    a_mob_path = "research/design-pilot/a-baseline/mobile.png"
    b_mob_path = "research/design-pilot/b-opendesign/mobile.png"
    out_path = "research/design-pilot/comparison/comparison-board.png"

    os.makedirs("research/design-pilot/comparison", exist_ok=True)

    img_a_d = Image.open(a_desk_path)
    img_b_d = Image.open(b_desk_path)
    img_a_m = Image.open(a_mob_path)
    img_b_m = Image.open(b_mob_path)

    # Scale to uniform comparative sizes
    # Desktop: target width 1000px, preserve aspect ratio
    d_w = 900
    a_d_h = int(img_a_d.height * (d_w / img_a_d.width))
    b_d_h = int(img_b_d.height * (d_w / img_b_d.width))

    # Mobile: target width 320px, preserve aspect ratio
    m_w = 300
    a_m_h = int(img_a_m.height * (m_w / img_a_m.width))
    b_m_h = int(img_b_m.height * (m_w / img_b_m.width))

    a_d_res = img_a_d.resize((d_w, a_d_h), Image.Resampling.LANCZOS)
    b_d_res = img_b_d.resize((d_w, b_d_h), Image.Resampling.LANCZOS)
    a_m_res = img_a_m.resize((m_w, a_m_h), Image.Resampling.LANCZOS)
    b_m_res = img_b_m.resize((m_w, b_m_h), Image.Resampling.LANCZOS)

    col_a_height = max(a_d_h, a_m_h)
    col_b_height = max(b_d_h, b_m_h)
    max_content_height = max(col_a_height, col_b_height)

    # Board layout:
    # Column A: width = d_w + m_w + 30px gap
    # Column B: width = d_w + m_w + 30px gap
    # Total width = (d_w + m_w + 30) * 2 + 80 (margins/center gap)
    col_width = d_w + m_w + 40
    margin = 50
    header_h = 100
    total_w = margin * 2 + col_width * 2 + 60
    total_h = header_h + max_content_height + margin * 2

    board = Image.new("RGB", (total_w, total_h), color=(245, 245, 247))
    draw = ImageDraw.Draw(board)

    # Simple font
    try:
        font_label = ImageFont.truetype("arial.ttf", 48)
        font_sub = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font_label = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Column A position
    col_a_x = margin
    col_b_x = margin + col_width + 60

    # Draw Headers
    draw.text((col_a_x + 20, 35), "A", fill=(15, 23, 42), font=font_label)
    draw.text((col_b_x + 20, 35), "B", fill=(15, 23, 42), font=font_label)

    # Paste A
    board.paste(a_d_res, (col_a_x, header_h))
    board.paste(a_m_res, (col_a_x + d_w + 30, header_h))

    # Paste B
    board.paste(b_d_res, (col_b_x, header_h))
    board.paste(b_m_res, (col_b_x + d_w + 30, header_h))

    board.save(out_path, quality=92)
    print(f"Board saved to {out_path} ({total_w}x{total_h})")

if __name__ == "__main__":
    make_board()
