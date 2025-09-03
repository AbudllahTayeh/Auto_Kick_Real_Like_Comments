# Kick AI Bot Control Panel

> **Disclaimer:** This project is for educational purposes only. It was created to explore browser automation, GUI development with Tkinter, and integration with large language models. The API keys included in the source code have been invalidated and **will not work**. You must obtain your own API keys to run this application. The author is not responsible for how this code is used.

![Kick Bot GUI]

This is an advanced, AI-powered chat bot for the Kick streaming platform, controlled by a user-friendly graphical interface (GUI). The bot uses Google's Gemini AI to watch the live chat of any streamer, understand the context of the conversation, and generate unique, human-like comments in real-time.

It's designed to be highly resilient and efficient, capable of running for extended periods by intelligently managing API keys and batching requests.

---

# Core Features

-   **Full Graphical Interface:** No more command lines. Control everything from a clean, intuitive desktop application.
-   **AI-Powered Conversation:** Leverages the Gemini 1.5 Flash model to generate contextually relevant and casual comments.
-   **Dynamic Language & Accent Control:** The AI's personality, language, and accent can be directly controlled via the "Special Request" box in the GUI.
-   **Intelligent Scraping:** Filters out messages from other bots, emojis, and duplicate spam to provide the AI with high-quality context.
-   **API Key Rotation:** Automatically cycles through a list of your Gemini API keys to bypass daily free-tier limits and maximize runtime.
-   **Efficient Batching:** Reduces API usage significantly by generating multiple comments in a single request and using them over several cycles.
-   **Automated Login:** On first run, the bot saves your session cookies for quick, automated logins in the future.

---

#Setup Guide

Follow these steps to get the bot up and running on your system.

1. Clone the Repository

First, get the project files onto your machine.
```bash
git clone <https://github.com/AbudllahTayeh/Auto_Kick_Real_Like_Comments.git>
```
2. Create a Virtual Environment
It's highly recommended to use a virtual environment to keep dependencies clean.
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate
```
3. Install Dependencies
Install all the necessary Python libraries with a single command using the provided requirements.txt file.
```bash
pip install -r requirements.txt
```
4. Get Your Gemini API Keys

   The bot is powered by the Gemini AI. You will need to generate your own API keys for it to function.

    1.Go to Google AI Studio.

    2.Sign in and click "Get API key" -> "Create API key in new project".

    3.Copy the generated key.

For best results, create multiple Google accounts to generate several API keys. This allows the bot's API key rotation feature to work effectively.
#How to Use
Run the Application:
```bash
python kick_bot_gui.py
```
###First-Time Login: 
The first time you run the bot, a Chrome window will open asking you to log in to Kick.com. Log in to your account. The bot will automatically save your session cookies in a kick_cookies.json file so you won't have to log in again.

###Configure the Bot:

    Kick Username: The username of the streamer you want to watch.

    Time Interval: The minimum and maximum time (in seconds) the bot will wait between sending comments.

    Scrape Count: The number of recent, unique human messages the bot will read to understand the conversation.

    Comments per Request: How many comments the AI should generate in a single API call (batching). A value of 3 is recommended for efficiency.

    Gemini Special Request: Add custom instructions here to shape the AI's personality (e.g., "be sarcastic," "ask a lot of questions," "speak in a Saudi accent").

    Gemini API Keys: Paste your list of personal API keys, with each key on a new line.

###Start the Bot:
    Click the "Start Bot" button. The live log will show you the bot's status in real-time.

###Stop the Bot: 
    Click the "Stop Bot" button to safely shut down the browser and end the session.
