# Kick AI Bot Control Panel

> **Disclaimer:** This project is for educational purposes only. It was created to explore browser automation, GUI development with Tkinter, and integration with large language models. The API keys included in the source code have been invalidated and **will not work**. You must obtain your own API keys to run this application. The author is not responsible for how this code is used.

![Kick Bot GUI](https'://i.imgur.com/u5uF2f7.png)

This is an advanced, AI-powered chat bot for the Kick streaming platform, controlled by a user-friendly graphical interface (GUI). The bot uses Google's Gemini AI to watch the live chat of any streamer, understand the context of the conversation, and generate unique, human-like comments in real-time.

It's designed to be highly resilient and efficient, capable of running for extended periods by intelligently managing API keys and batching requests.

---

### Core Features

-   **Full Graphical Interface:** No more command lines. Control everything from a clean, intuitive desktop application.
-   **AI-Powered Conversation:** Leverages the Gemini 1.5 Flash model to generate contextually relevant and casual comments.
-   **Dynamic Language & Accent Control:** The AI's personality, language, and accent can be directly controlled via the "Special Request" box in the GUI.
-   **Intelligent Scraping:** Filters out messages from other bots, emojis, and duplicate spam to provide the AI with high-quality context.
-   **API Key Rotation:** Automatically cycles through a list of your Gemini API keys to bypass daily free-tier limits and maximize runtime.
-   **Efficient Batching:** Reduces API usage significantly by generating multiple comments in a single request and using them over several cycles.
-   **Automated Login:** On first run, the bot saves your session cookies for quick, automated logins in the future.

---

### Setup Guide

Follow these steps to get the bot up and running on your system.

#### 1. Clone the Repository

First, get the project files onto your machine.
```bash
git clone <https://github.com/AbudllahTayeh/Auto_Kick_Real_Like_Comments.git>
