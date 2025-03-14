import os
import re
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

# ====== CẤU HÌNH ======
TOKEN = os.getenv("TELEGRAM_TOKEN_SAVING")
CHAT_SAVING_ID = "7965457812"
FILE_NAME = "savings_log.txt"
CHART_IMG = "savings_chart.png"
MARKER_IMG = "savings_marker_chart.png"

# ====== XỬ LÝ DỮ LIỆU ======
def load_savings_log():
    data = []
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            for line in f:
                match = re.search(r"Ngày (\d+): (\d+) nghìn đồng", line)
                if match:
                    day = int(match.group(1))
                    amount = int(match.group(2))
                    data.append((day, amount))
    return data

def calculate_total(data):
    return sum(amount for _, amount in data)

# ====== BIỂU ĐỒ SỐ TIỀN ======
def draw_amount_chart(data):
    if not data:
        return
    days = [d for d, _ in data]
    amounts = [a for _, a in data]

    plt.figure(figsize=(10, 5))
    plt.bar(days, amounts, color="#4CAF50")
    plt.title("Biểu đồ tiến độ tiết kiệm 365 ngày")
    plt.xlabel("Ngày")
    plt.ylabel("Số tiền (nghìn đồng)")
    plt.tight_layout()
    plt.savefig(CHART_IMG)
    plt.close()

# ====== BIỂU ĐỒ ĐÁNH DẤU 365 NGÀY ======
def draw_savings_grid(saved_days):
    total_days = 365
    cols = 31  # dễ chia hơn cho layout đẹp
    rows = (total_days // cols) + 1

    fig, ax = plt.subplots(figsize=(20, 12))
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)

    for i in range(1, total_days + 1):
        col = (i - 1) % cols
        row = rows - 1 - (i - 1) // cols

        # Màu sắc
        if any(i == days[1] for days in saved_days):
            color = "#4CAF50"  # xanh lá
            text_color = "white"
        else:
            color = "#E0E0E0"  # xám nhạt
            text_color = "black"

        # Vẽ ô
        rect = plt.Rectangle((col, row), 1, 1, facecolor=color, edgecolor='black', linewidth=0.5)
        ax.add_patch(rect)
        ax.text(col + 0.5, row + 0.5, str(i), ha='center', va='center', fontsize=8, color=text_color, fontweight='bold')

    # Gỡ trục
    ax.set_xticks([])
    ax.set_yticks([])

    # Thêm tiêu đề
    ax.set_title("Các số đã tiết kiệm 365 ngày", fontsize=24, fontweight='bold', pad=20)

    # Thêm chú thích (legend)
    saved_patch = mpatches.Patch(color="#4CAF50", label="Đã tiết kiệm")
    unsaved_patch = mpatches.Patch(color="#E0E0E0", label="Chưa tiết kiệm")
    ax.legend(handles=[saved_patch, unsaved_patch], loc="lower center", bbox_to_anchor=(0.5, -0.05), ncol=2, fontsize=12)

    plt.tight_layout()
    plt.savefig(MARKER_IMG, dpi=300)
    plt.close()

# ====== GỬI QUA TELEGRAM ======
def send_report(data):
    bot = Bot(token=TOKEN)
    total = calculate_total(data)

    message = f"💰 Báo cáo tiết kiệm 365 ngày\n\n"
    message += f"Tổng đã tiết kiệm: {total} nghìn đồng\n"
    message += f"Số ngày đã hoàn thành: {len(data)}/365\n"

    bot.send_message(chat_id=CHAT_SAVING_ID, text=message)

    # Gửi biểu đồ số tiền
    if os.path.exists(CHART_IMG):
        with open(CHART_IMG, "rb") as img:
            bot.send_photo(chat_id=CHAT_SAVING_ID, photo=img)

    # Gửi biểu đồ đánh dấu 365 ngày
    if os.path.exists(MARKER_IMG):
        with open(MARKER_IMG, "rb") as img:
            bot.send_photo(chat_id=CHAT_SAVING_ID, photo=img)

    # Gửi lịch sử gần đây
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            log = f.readlines()
            log_recent = "".join(log[-10:])
            bot.send_message(chat_id=CHAT_SAVING_ID, text=f"📜 Lịch sử gần đây:\n\n{log_recent}")

# ====== MAIN ======
if __name__ == "__main__":
    savings_data = load_savings_log()
    draw_amount_chart(savings_data)
    draw_savings_grid(savings_data)
    send_report(savings_data)
