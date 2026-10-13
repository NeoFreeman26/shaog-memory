#!/usr/bin/env python3
"""
小g (ShaoG) 24 小時 Telegram 橋接機器人
讓你可以從 iPhone 的 Telegram 隨時連線到家裡 Mac mini 上的小g，
並透過 GitHub (shaog-memory) 與 MacBook Air 同步 GEMINI.md 長期記憶。
"""

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, Set

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# 設定日誌格式
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("shaog-telegram")

BASE_DIR = Path(__file__).resolve().parent
GEMINI_MD_PATH = BASE_DIR / "GEMINI.md"

# 載入 .env 設定
load_dotenv(BASE_DIR / ".env")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
RAW_ALLOWED_IDS = os.getenv("ALLOWED_USER_IDS", "").strip()


def get_allowed_user_ids() -> Set[int]:
    """解析允許訪問的 Telegram User ID 白名單"""
    ids: Set[int] = set()
    if not RAW_ALLOWED_IDS:
        return ids
    for part in RAW_ALLOWED_IDS.split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids


ALLOWED_USER_IDS = get_allowed_user_ids()


def load_gemini_memory() -> str:
    """讀取本地 GEMINI.md 長期記憶檔"""
    if GEMINI_MD_PATH.exists():
        return GEMINI_MD_PATH.read_text(encoding="utf-8")
    return (
        "# 使用者偏好與協作規則\n"
        "- 助手稱呼：小g\n"
        "- 語言偏好：請一律使用繁體中文（Traditional Chinese）與使用者溝通。\n"
    )


def build_system_instructions() -> str:
    """組合小g的系統提示詞與長期記憶"""
    memory = load_gemini_memory()
    return (
        "你是「小g」，使用者的專屬 AI 助手，目前常駐在使用者家裡的 Mac mini 上，"
        "透過 Telegram 與使用者的 iPhone 連線。\n"
        "請務必遵守以下來自 GEMINI.md 的長期記憶與偏好規則：\n\n"
        f"{memory}\n\n"
        "回覆時請保持親切、清楚、精簡，適合在手機 Telegram 畫面上閱讀。"
    )


def is_authorized(update: Update) -> bool:
    """檢查傳訊者是否在安全白名單內（若尚未設定白名單則允許並提示 ID）"""
    if not ALLOWED_USER_IDS:
        return True
    user = update.effective_user
    return bool(user and user.id in ALLOWED_USER_IDS)


def run_git_sync(commit_message: Optional[str] = None) -> str:
    """與 GitHub 同步 GEMINI.md 長期記憶"""
    logs = []
    try:
        if commit_message:
            subprocess.run(
                ["git", "add", "GEMINI.md"],
                cwd=BASE_DIR,
                check=True,
                capture_output=True,
                text=True,
            )
            commit_res = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
            )
            if commit_res.returncode == 0:
                logs.append(f"已提交記憶更新：{commit_message}")

        pull_res = subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if pull_res.returncode == 0:
            logs.append("已從 GitHub 拉取最新記憶 (git pull)")
        else:
            logs.append(f"拉取提示：{pull_res.stderr.strip() or pull_res.stdout.strip()}")

        push_res = subprocess.run(
            ["git", "push", "origin", "HEAD:main"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if push_res.returncode == 0:
            logs.append("已將最新記憶推送到 GitHub (git push)")
        else:
            logs.append(f"推送提示：{push_res.stderr.strip() or push_res.stdout.strip()}")

    except Exception as exc:
        logs.append(f"Git 同步發生錯誤：{exc}")

    return "\n".join(f"• {line}" for line in logs)


class ShaoGSessionManager:
    """管理每個 Telegram 對話視窗與 Antigravity Agent 的連線"""

    def __init__(self) -> None:
        self._agents: Dict[int, object] = {}
        self._locks: Dict[int, asyncio.Lock] = {}

    def get_lock(self, chat_id: int) -> asyncio.Lock:
        if chat_id not in self._locks:
            self._locks[chat_id] = asyncio.Lock()
        return self._locks[chat_id]

    async def reset_session(self, chat_id: int) -> None:
        agent = self._agents.pop(chat_id, None)
        if agent is not None:
            try:
                await agent.__aexit__(None, None, None)
            except Exception as exc:
                logger.warning("關閉舊 Agent 連線時發生警告: %s", exc)

    async def chat(self, chat_id: int, user_message: str) -> str:
        from google.antigravity import Agent, CapabilitiesConfig, LocalAgentConfig

        if chat_id not in self._agents:
            config = LocalAgentConfig(
                system_instructions=build_system_instructions(),
                capabilities=CapabilitiesConfig(),
            )
            agent = Agent(config)
            await agent.__aenter__()
            self._agents[chat_id] = agent

        agent = self._agents[chat_id]
        response = await agent.chat(user_message)
        chunks = []
        async for token in response:
            chunks.append(token)
        reply = "".join(chunks).strip()
        return reply or "（小g 已執行完成，但沒有文字輸出）"


session_manager = ShaoGSessionManager()


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /start 指令"""
    if not is_authorized(update):
        await update.message.reply_text("⛔ 抱歉，這是私人專屬的小g機器人。")
        return

    user = update.effective_user
    user_id = user.id if user else "未知"
    security_tip = (
        f"✅ 已啟用白名單保護（你的 ID: `{user_id}`）"
        if ALLOWED_USER_IDS
        else (
            f"💡 你的 Telegram User ID 是：`{user_id}`\n"
            "建議將此 ID 填入 Mac mini 的 `.env` 檔案中的 `ALLOWED_USER_IDS`，這樣就只有你能跟小g對話！"
        )
    )

    msg = (
        f"嗨！我是住在你 Mac mini 裡的 **小g** ☀️\n\n"
        f"{security_tip}\n\n"
        "📌 **常用指令：**\n"
        "• 直接傳訊息：跟小g聊天或請小g在 Mac mini 上做事\n"
        "• `/remember <內容>`：讓小g記住新規則並自動同步到 GitHub\n"
        "• `/sync`：立即與 GitHub (`shaog-memory`) 同步最新記憶\n"
        "• `/reset`：開啟新對話（重新載入 `GEMINI.md` 記憶）\n"
        "• `/id`：查看你的 Telegram User ID"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /id 指令"""
    user = update.effective_user
    if user:
        await update.message.reply_text(
            f"你的 Telegram User ID 是：`{user.id}`",
            parse_mode="Markdown",
        )


async def remember_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /remember <記憶內容> 指令：寫入 GEMINI.md 並同步至 GitHub"""
    if not is_authorized(update):
        return

    note = " ".join(context.args).strip() if context.args else ""
    if not note:
        await update.message.reply_text(
            "請在 `/remember` 後面加上要小g記住的事情喔！\n例如：`/remember 我喜歡喝無糖拿鐵`",
            parse_mode="Markdown",
        )
        return

    current_content = load_gemini_memory().rstrip()
    new_content = f"{current_content}\n- {note}\n"
    GEMINI_MD_PATH.write_text(new_content, encoding="utf-8")

    # 重置對話以套用最新 GEMINI.md
    await session_manager.reset_session(update.effective_chat.id)
    sync_status = await asyncio.to_thread(run_git_sync, f"透過 Telegram 新增小g記憶：{note}")

    await update.message.reply_text(
        f"✅ 小g 已經寫進 `GEMINI.md` 記住囉！\n\n📝 新增記憶：{note}\n\n🔄 GitHub 同步狀態：\n{sync_status}"
    )


async def sync_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /sync 指令：從 GitHub 拉取並推送 GEMINI.md"""
    if not is_authorized(update):
        return

    await update.message.reply_text("🔄 小g 正在與 GitHub (`shaog-memory`) 同步記憶中...")
    sync_status = await asyncio.to_thread(run_git_sync, None)
    await session_manager.reset_session(update.effective_chat.id)
    await update.message.reply_text(
        f"✅ 同步完成！已重新載入最新記憶 `GEMINI.md`：\n\n{sync_status}"
    )


async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /reset 指令：重置當前對話視窗"""
    if not is_authorized(update):
        return

    await session_manager.reset_session(update.effective_chat.id)
    await update.message.reply_text("✨ 小g 已開啟全新的對話視窗，並載入最新的 `GEMINI.md` 長期記憶！")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理一般文字訊息並轉交給 Antigravity Agent"""
    if not update.message or not update.message.text:
        return

    if not is_authorized(update):
        await update.message.reply_text("⛔ 抱歉，這是私人專屬的小g機器人。")
        return

    chat_id = update.effective_chat.id
    user_text = update.message.text.strip()

    lock = session_manager.get_lock(chat_id)
    async with lock:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        try:
            reply = await session_manager.chat(chat_id, user_text)
        except Exception as exc:
            logger.exception("呼叫 Antigravity Agent 時發生錯誤")
            reply = (
                f"⚠️ 小g 暫時遇到一點狀況：`{exc}`\n\n"
                "請確認 Mac mini 上已安裝 `google-antigravity` 並完成登入驗證（可執行 `agy` 測試）。"
            )

        # Telegram 單則訊息上限為 4096 字元，若較長則分段傳送
        max_len = 4000
        for i in range(0, len(reply), max_len):
            chunk = reply[i : i + max_len]
            await update.message.reply_text(chunk)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "請填入你的_BOT_TOKEN":
        print("❌ 尚未設定 TELEGRAM_BOT_TOKEN！")
        print("請先複製 .env.example 為 .env，並填入從 @BotFather 取得的 Token。")
        return

    print("🚀 小g Telegram 24 小時機器人啟動中...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("remember", remember_cmd))
    app.add_handler(CommandHandler("sync", sync_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ 小g 已上線！現在可以用 iPhone Telegram 傳訊息給小g了。")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
