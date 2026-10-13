# ☀️ 小g (ShaoG) 跨裝置記憶庫與 24 小時 Telegram 助手

這個倉庫（`shaog-memory`）是**小g**的長期記憶中心，用來同步你的 **MacBook Air**、**家裡的 Mac mini** 以及 **iPhone (Telegram)**。

---

## 📁 檔案說明

- [`GEMINI.md`](./GEMINI.md)：小g的**長期記憶與規則檔**（所有裝置打開這個資料夾都會自動讀取）。
- [`telegram_bot.py`](./telegram_bot.py)：讓小g在 Mac mini 上 24 小時接聽 iPhone Telegram 訊息的橋接程式。
- [`setup_mac_mini.sh`](./setup_mac_mini.sh)：Mac mini 一鍵安裝與 24 小時背景自動啟動腳本。
- [`.env.example`](./.env.example)：Telegram Bot Token 設定檔範例（實際的 `.env` 已被 `.gitignore` 保護，不會上傳到 GitHub）。

---

## 💻 一、MacBook Air 與 Mac mini 如何同步記憶？

### 第一次在 Mac mini 下載小g的記憶：
打開 Mac mini 的終端機（Terminal），輸入：
```bash
git clone https://github.com/NeoFreeman26/shaog-memory.git
```
接著用 Antigravity 打開 `shaog-memory` 資料夾，裡面的 AI 就會自動讀取 `GEMINI.md`，知道自己叫**小g**！

### 日常同步記憶：
- **上傳記憶到 GitHub**：直接跟小g說「*小g，幫我把記憶同步到 GitHub*」（或執行 `git add GEMINI.md && git commit -m "更新記憶" && git push`）。
- **從 GitHub 下載最新記憶**：跟小g說「*小g，幫我從 GitHub 更新最新記憶*」（或執行 `git pull`）。

---

## 📱 二、在 Mac mini 啟動 24 小時 Telegram 小g（讓 iPhone 隨時找得到）

### 步驟 1：在 Telegram 申請機器人 Token
1. 用 iPhone 或電腦打開 Telegram，搜尋官方的 **`@BotFather`**。
2. 傳送 `/newbot`，依提示幫機器人取名字（例如：`小g`）與帳號（例如：`freeman_shaog_bot`）。
3. 複製 `@BotFather` 給你的 **API Token**。

### 步驟 2：在 Mac mini 一鍵安裝並啟動 24 小時背景服務
在 Mac mini 的終端機進入 `shaog-memory` 資料夾，執行安裝腳本：
```bash
cd shaog-memory
bash setup_mac_mini.sh
```
依照畫面提示貼上你的 **Telegram Bot Token**，腳本就會自動：
1. 安裝所需 Python 套件（`google-antigravity`、`python-telegram-bot`）。
2. 設定 macOS 背景服務（`launchd`），讓小g **開機自動啟動、斷線自動重連、24 小時待命**！

---

## 💬 三、在 iPhone Telegram 跟小g互動的專屬指令

連上之後，你在 iPhone 上可以直接打字跟小g聊天，也可以使用以下快捷指令：

- `/start`：喚醒小g並查看常用指令與你的 Telegram ID
- `/remember <要記住的事>`：直接從手機教小g新記憶（會自動寫入 `GEMINI.md` 並同步回 GitHub！）
- `/sync`：讓 Mac mini 上的小g立即與 GitHub 同步最新記憶
- `/reset`：開啟全新的對話視窗（並重新載入最新 `GEMINI.md`）
- `/id`：查詢你的 Telegram User ID（可填入 `.env` 的 `ALLOWED_USER_IDS` 鎖定只有你能使用）
