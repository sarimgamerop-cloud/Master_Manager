# Master Manager - AI-Powered Expense Tracker

Master Manager is a modern, professional desktop application for managing personal finances. Built with **Python** and **PyQt5**, it combines robust tracking tools with **Google Gemini AI** to provide insights and a hands-free voice experience.

![Dashboard Preview](<img width="1041" height="797" alt="dash" src="https://github.com/user-attachments/assets/8f58503b-8320-4283-921e-fe09d7d47114" />
)

## 🚀 Features

### 📊 Real-Time Financial Dashboard
Get an instant overview of your financial health. The dashboard shows your total spending for the current month, today's expenses, and your top spending category automatically.

### 🎙️ Voice-Assisted Entry (Dictate Price)
Hands-free amount entry. Simply click the microphone icon next to the Amount field and say your price (e.g., "Fifty dollars and twenty cents"). The app extracts the numeric value automatically.

### 🤖 Gemini AI Assistant
Ask questions about your spending patterns in natural language. Gemini analyzes your monthly, yearly, and category-wise data to give you personalized financial advice.

### 🔍 Advanced Search & Filtering
Easily navigate thousands of transactions. Filter by category or use the live search bar to find specific descriptions instantly.

### 📈 Visual Data Analytics
Visualize your habits with built-in:
- **Bar Charts:** Breakdown of spending by category.
- **Line Charts:** Monthly trend analysis to see how your spending evolves over time.

### ☁️ Free Cloud Backup
Never lose your data. Securely send a backup of your entire database directly to your Gmail inbox with one click.

### 🛠️ Personalization
- **Custom Branding:** Upload your own logo for a personalized dashboard.
- **Adjustable UI:** Change font sizes for comfortable viewing.
- **Star System:** Highlight and quickly access your most important expenses.

---

## 🛠️ Installation

### 1. Prerequisites
- **Python 3.8+**
- **Microphone** (for voice dictation)

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/MasterManager.git
cd MasterManager
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Gemini AI
1. Get a free API Key from [Google AI Studio](https://aistudio.google.com/).
2. Open the app, go to **Settings**, and paste your API key.

---

## 🖥️ Running the App
Start the application by running:
```bash
python main.py
```

---

## 📁 Project Structure
- `main.py`: The core UI and application logic.
- `database.py`: SQLite database management and optimized SQL queries.
- `config.json`: Stores your user settings and API configurations.
- `expense_manager.db`: Your local encrypted financial data.

---

## 💡 Usage Tips
- **Voice Input:** If you are on Linux and `PyAudio` fails, the app automatically falls back to `arecord`.
- **Cloud Backup:** To use Gmail backup, you must generate a **Google App Password**. [Learn how here](https://support.google.com/accounts/answer/185833).
- **Gemini Assistant:** The more data you enter, the smarter Gemini's financial advice becomes!

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
