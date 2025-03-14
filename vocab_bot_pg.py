# Description: A Telegram bot for learning vocabulary with PostgreSQL database.
from db import SessionLocal, Vocab, init_db
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import random
import csv
import os
import random

load_dotenv()
init_db()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Commands

def start(update, context):
    update.message.reply_text("📚 Chào mừng bạn đến với Bot học từ vựng!\nDùng /help để xem hướng dẫn.")

def help_command(update, context):
    update.message.reply_text("""
📖 Danh sách lệnh:
/add từ : nghĩa - Thêm từ mới
/update từ : nghĩa - Cập nhật nghĩa từ
/delete từ - Xoá từ
/search từ - Tìm kiếm nghĩa
/export - Xuất file CSV
/import - Nhập file CSV
/quiz - Kiểm tra từ vựng ngẫu nhiên
""")

def add_vocab(update, context):
    try:
        text = ' '.join(context.args)
        word, meaning = text.split(":")
        word, meaning = word.strip(), meaning.strip()

        db = SessionLocal()
        vocab = db.query(Vocab).filter_by(word=word).first()
        if vocab:
            update.message.reply_text(f"⚠️ Từ '{word}' đã tồn tại với nghĩa: {vocab.meaning}\nGõ /update {word} : nghĩa_mới nếu muốn cập nhật.")
        else:
            new_vocab = Vocab(word=word, meaning=meaning)
            db.add(new_vocab)
            db.commit()
            update.message.reply_text(f"✅ Đã lưu: {word} : {meaning}")
        db.close()
    except:
        update.message.reply_text("❌ Sai cú pháp! Dùng: /add từ : nghĩa")

def update_vocab(update, context):
    try:
        text = ' '.join(context.args)
        word, new_meaning = text.split(":")
        word, new_meaning = word.strip(), new_meaning.strip()

        db = SessionLocal()
        vocab = db.query(Vocab).filter_by(word=word).first()
        if vocab:
            vocab.meaning = new_meaning
            db.commit()
            update.message.reply_text(f"✅ Đã cập nhật: {word} : {new_meaning}")
        else:
            update.message.reply_text(f"⚠️ Không tìm thấy từ '{word}' để cập nhật.")
        db.close()
    except:
        update.message.reply_text("❌ Sai cú pháp! Dùng: /update từ : nghĩa_mới")

def delete_vocab(update, context):
    try:
        word = ' '.join(context.args).strip()
        db = SessionLocal()
        vocab = db.query(Vocab).filter_by(word=word).first()
        if vocab:
            db.delete(vocab)
            db.commit()
            update.message.reply_text(f"🗑️ Đã xoá từ '{word}'.")
        else:
            update.message.reply_text(f"⚠️ Không tìm thấy từ '{word}' để xoá.")
        db.close()
    except:
        update.message.reply_text("❌ Sai cú pháp! Dùng: /delete từ")

def search_vocab(update, context):
    try:
        word = ' '.join(context.args).strip()
        db = SessionLocal()
        vocab = db.query(Vocab).filter_by(word=word).first()
        db.close()
        if vocab:
            update.message.reply_text(f"🔍 {word} : {vocab.meaning}")
        else:
            update.message.reply_text(f"❌ Không tìm thấy từ '{word}'.")
    except:
        update.message.reply_text("❌ Sai cú pháp! Dùng: /search từ")

def export_csv(update, context):
    db = SessionLocal()
    vocabs = db.query(Vocab).all()
    with open("vocab_export.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Word", "Meaning"])
        for v in vocabs:
            writer.writerow([v.word, v.meaning])
    db.close()
    update.message.reply_document(document=open("vocab_export.csv", "rb"))

def import_csv(update, context):
    update.message.reply_text("📤 Hãy gửi file CSV sau khi dùng lệnh này.")
    context.user_data['awaiting_csv'] = True

def handle_document(update, context):
    if context.user_data.get('awaiting_csv'):
        file = update.message.document.get_file()
        file.download("imported_vocab.csv")

        db = SessionLocal()
        with open("imported_vocab.csv", encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) >= 2:
                    word, meaning = row[0].strip(), row[1].strip()
                    vocab = db.query(Vocab).filter_by(word=word).first()
                    if vocab:
                        vocab.meaning = meaning
                    else:
                        db.add(Vocab(word=word, meaning=meaning))
            db.commit()
        db.close()
        update.message.reply_text("✅ Đã nhập file CSV thành công.")
        context.user_data['awaiting_csv'] = False

def quiz(update, context):
    db = SessionLocal()
    vocabs = db.query(Vocab).all()
    db.close()
    if not vocabs:
        update.message.reply_text("⚠️ Bạn chưa có từ vựng để kiểm tra.")
        return
    vocab = random.choice(vocabs)
    update.message.reply_text(f"❓ Nghĩa của từ: {vocab.word} là gì?")
    context.user_data['quiz_answer'] = vocab.meaning

def handle_message(update, context):
    if 'quiz_answer' in context.user_data:
        answer = update.message.text.strip().lower()
        correct = context.user_data.pop('quiz_answer').strip().lower()
        if answer == correct:
            update.message.reply_text("✅ Chính xác!")
        else:
            update.message.reply_text(f"❌ Sai! Đáp án đúng là: {correct}")

# Main

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("add", add_vocab))
    dp.add_handler(CommandHandler("update", update_vocab))
    dp.add_handler(CommandHandler("delete", delete_vocab))
    dp.add_handler(CommandHandler("search", search_vocab))
    dp.add_handler(CommandHandler("export", export_csv))
    dp.add_handler(CommandHandler("import", import_csv))
    dp.add_handler(CommandHandler("quiz", quiz))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
