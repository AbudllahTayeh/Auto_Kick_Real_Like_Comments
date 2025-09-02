import time
import random
import json
import os
import traceback
import re
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import undetected_chromedriver as uc
import google.generativeai as genai
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

# --- BOT LOGIC (encapsulated for the GUI) ---

class KickBot:
    def __init__(self, params, logger):
        self.params = params
        self.logger = logger
        self.stop_event = threading.Event()
        self.driver = None
        # API Key Rotation Logic
        self.api_keys = [key.strip() for key in params['api_keys'] if key.strip()]
        self.current_api_key_index = 0
        self.model = None
        # Comment batching queue
        self.comment_queue = []


    def log(self, message):
        self.logger(message)

    def run(self):
        try:
            self._switch_api_key() # Initial setup of the first key
            if not self.model:
                 self.log("--- CRITICAL: No valid API keys found. Bot cannot start. ---")
                 return
            self._main_loop()
        except Exception as e:
            self.log(f"--- A CRITICAL ERROR OCCURRED ---")
            self.log(traceback.format_exc())
        finally:
            if self.driver:
                self.driver.quit()
            self.log("\n--- Bot has stopped. ---")

    def stop(self):
        self.log("--- Stop signal received. Shutting down... ---")
        self.stop_event.set()

    def _switch_api_key(self):
        # [FIX] Complete overhaul of the key rotation logic.
        if self.current_api_key_index >= len(self.api_keys):
            self.log("All API keys have been tried and failed. Cannot generate comments.")
            self.model = None
            return False

        try:
            key_to_try = self.api_keys[self.current_api_key_index]
            self.log(f"Attempting to initialize with API Key #{self.current_api_key_index + 1}...")
            
            genai.configure(api_key=key_to_try)
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            self.log(f"Successfully initialized with API Key #{self.current_api_key_index + 1}.")
            # Increment the index AFTER a successful configuration,
            # so the next rotation call will correctly use the next key in the list.
            self.current_api_key_index += 1
            return True
            
        except Exception as e:
            self.log(f"API Key #{self.current_api_key_index + 1} failed during initialization: {e}")
            self.current_api_key_index += 1
            return self._switch_api_key() # Recursively try the next key


    def _human_type(self, element, text):
        for char in text:
            if self.stop_event.is_set(): break
            delay = random.uniform(0.05, 0.2)
            element.send_keys(char)
            time.sleep(delay)

    def _scrape_messages(self, count):
        scrape_wait = WebDriverWait(self.driver, 5) 
        scrape_buffer = count * 3 
        
        selectors_to_try = [
            "div[data-index] .chat-entry-content", "div[data-index]",
            "div.chat-entry-content", "p.break-words.text-gray-300",
            "[data-test-id='chat-message-content']"
        ]
        
        bmp_pattern = re.compile("[\U00010000-\U0010FFFF]", flags=re.UNICODE)

        for selector in selectors_to_try:
            try:
                scrape_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    meaningful_messages = []
                    for el in elements[-scrape_buffer:][::-1]: 
                        if len(meaningful_messages) >= count:
                            break 
                        
                        raw_text = el.text
                        if not raw_text or not el.is_displayed():
                            continue
                        
                        parts = raw_text.split('\n')
                        
                        if len(parts) > 1 and "bot" in parts[0].lower():
                            continue 

                        if bmp_pattern.search(raw_text):
                            continue
                        
                        cleaned_text = parts[-1].strip() if len(parts) > 1 else parts[0].strip()

                        if cleaned_text and cleaned_text not in meaningful_messages:
                            meaningful_messages.insert(0, cleaned_text) 
                    
                    if meaningful_messages:
                        self.log(f"Scraped {len(meaningful_messages)} unique, human messages using selector: '{selector}'")
                        return meaningful_messages
            except Exception:
                continue
        self.log("Failed to scrape chat with all selectors.")
        return []

    def _generate_comment_batch(self, context, special_request, batch_size):
        if not self.model or not context: return []
        context_str = "\n- ".join(context)
        prompt = f"""
        You are an AI impersonating a clever and witty fan of a streamer. Your goal is to blend in with the chat and sound like a real person texting their friend.

        Here is the recent chat history:
        - {context_str}

        **Your Task:**
        1. your primary language is same as chat (common accent).
        2. Generate a numbered list of {batch_size} short, clever, and relevant comments in that SAME language.

        **Critical Instructions:**
        - Be VERY Casual: No punctuation. Write like you're texting.
        - Analyze, Don't Just Repeat: Your comments MUST match the topic and mood.
        - User's Special Request: "{special_request}"
        - Strictly No Emojis or Translations.
        - Ensure each comment is on a new line, starting with a number (e.g., "1. comment one\n2. comment two").

        Now, generate your list of {batch_size} clever and casual comments.
        """
        try:
            self.log(f"Asking Gemini for a batch of {batch_size} comments...")
            response = self.model.generate_content(prompt)
            
            raw_text = response.text.strip()
            comments = re.split(r'\n', raw_text)
            
            cleaned_comments = []
            for line in comments:
                clean_line = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                if clean_line:
                    bmp_pattern = re.compile("[\U00010000-\U0010FFFF]", flags=re.UNICODE)
                    clean_line = bmp_pattern.sub(r'', clean_line)
                    cleaned_comments.append(clean_line)
            
            return cleaned_comments if cleaned_comments else []
        except Exception as e:
            self.log(f"Current API Key failed. Rotating to the next one. Error: {e}")
            self._switch_api_key()
            return []

    def _main_loop(self):
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # [FIX] Force the driver to use the version matching your browser to prevent crashes.
        self.driver = uc.Chrome(options=options, headless=False, version_main=139)
        wait = WebDriverWait(self.driver, 45)

        self.log("Attempting to log in via cookies...")
        self.driver.get("https://kick.com")
        if os.path.exists(self.params['cookie_file']):
            with open(self.params['cookie_file'], 'r') as f: cookies = json.load(f)
            for cookie in cookies:
                if 'sameSite' in cookie and cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                    del cookie['sameSite']
                try: self.driver.add_cookie(cookie)
                except Exception: pass
            self.driver.refresh()
        else:
            self.log("Cookie file not found. Please log in manually.")
            self.driver.get("https://kick.com/login")
            WebDriverWait(self.driver, 300).until(EC.url_to_be("https://kick.com/"))
            self.log("Login successful! Saving cookies...")
            with open(self.params['cookie_file'], 'w') as f: json.dump(self.driver.get_cookies(), f)
        
        stream_url = f"https://kick.com/{self.params['streamer']}"
        self.log(f"Navigating to stream: {stream_url}")
        self.driver.get(stream_url)
        
        self.log("Checking for 'Start watching' overlay...")
        try:
            overlay_wait = WebDriverWait(self.driver, 5)
            start_button = overlay_wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Start watching']")))
            self.log("Overlay found. Clicking it...")
            start_button.click()
            time.sleep(2)
        except TimeoutException:
            self.log("No overlay found. Assuming chat is visible.")

        chat_input_selector = "div[contenteditable='true']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, chat_input_selector)))
        self.log("Stream loaded. Waiting for chat to go live...")

        chat_is_live = False
        for selector in ["div[data-index]", "div.chat-entry-content"]:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                self.log(f"Chat found. Bot is live.")
                chat_is_live = True
                break
            except TimeoutException:
                self.log(f"Selector '{selector}' timed out...")
        if not chat_is_live:
            raise TimeoutException("Could not find the chat container.")

        self.log("Starting the AI comment loop.")
        
        while not self.stop_event.is_set():
            comment_to_send = None
            
            if not self.model:
                 self.log("No working API key. Bot will remain silent.")
            elif not self.comment_queue:
                self.log("Comment queue is empty. Generating a new batch...")
                context = self._scrape_messages(self.params['scrape_count'])
                
                max_retries = 3 
                for attempt in range(max_retries):
                    if self.stop_event.is_set(): break
                    
                    batch = self._generate_comment_batch(context, self.params['special_request'], self.params['batch_size'])
                    if batch:
                        self.comment_queue.extend(batch)
                        self.log(f"Successfully generated a batch of {len(self.comment_queue)} comments.")
                        break 
                    if not self.model:
                        break
                    self.log(f"AI batch generation failed. Retrying... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(1)

            if self.comment_queue:
                comment_to_send = self.comment_queue.pop(0)
                self.log(f"Using comment from queue. {len(self.comment_queue)} remaining.")
            
            if not comment_to_send:
                self.log("No comment to send this cycle. Entering rapid retry mode...")
                wait_time = random.uniform(3, 5) # Short wait on failure
            else:
                self.log(f"AI Generated Comment: '{comment_to_send}'")
                try:
                    chat_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, chat_input_selector)))
                    self._human_type(chat_box, comment_to_send)
                    chat_box.send_keys(Keys.RETURN)
                    self.log("Comment sent.")
                    self.log("Cooldown... letting chat update.")
                    time.sleep(3) 
                except TimeoutException:
                    self.log("Could not find chat box. Skipping turn.")
                
                # Normal long wait time only on success
                wait_time = random.uniform(self.params['min_time'], self.params['max_time'])
            
            self.log(f"Waiting for {int(wait_time)} seconds...")
            
            for _ in range(int(wait_time)):
                if self.stop_event.is_set(): break
                time.sleep(1)

# --- GUI APPLICATION ---

class KickBotGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kick AI Bot Control Panel")
        self.geometry("700x700")

        self.bot_thread = None
        self.kick_bot = None

        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        controls_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        controls_frame.pack(fill=tk.X, expand=False)
        controls_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(controls_frame, text="Kick Username:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.streamer_var = tk.StringVar(value="")
        ttk.Entry(controls_frame, textvariable=self.streamer_var).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(controls_frame, text="Time Interval (sec):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        time_frame = ttk.Frame(controls_frame)
        time_frame.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.min_time_var = tk.StringVar(value="70")
        self.max_time_var = tk.StringVar(value="100")
        ttk.Entry(time_frame, textvariable=self.min_time_var, width=5).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(time_frame, text="to").pack(side=tk.LEFT, padx=5)
        ttk.Entry(time_frame, textvariable=self.max_time_var, width=5).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(controls_frame, text="Scrape Count:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.scrape_count_var = tk.StringVar(value="20")
        ttk.Entry(controls_frame, textvariable=self.scrape_count_var).grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(controls_frame, text="Comments per Request:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.batch_size_var = tk.StringVar(value="3")
        ttk.Entry(controls_frame, textvariable=self.batch_size_var).grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(controls_frame, text="Gemini Special Request:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.special_request_var = tk.StringVar(value="be cleaverly funny and supportive.")
        ttk.Entry(controls_frame, textvariable=self.special_request_var).grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(controls_frame, text="Gemini API Keys (one per line):").grid(row=5, column=0, padx=5, pady=5, sticky="nw")
        self.api_keys_text = tk.Text(controls_frame, height=7, wrap=tk.WORD)
        self.api_keys_text.grid(row=5, column=1, padx=5, pady=5, sticky="ew")
        self.api_keys_text.insert(tk.END, "AIzaSyCw2_fGnpEFgZctFKasdaPUU5L_quzkSKMNKDY\n"
                                           "AIzaSyBoikuUp5RFcVasdMVoYsg6eJObkwSlDquB88\n" #THESE APIS WILL NOT WORK ANY MORE
                                           "AIzaSyC4jh_WC8VDIyGeasdcrAv_JgfhHT49zmM4KE\n" #THESE APIS WILL NOT WORK ANY MORE
                                           "AIzaSyDc5Lgb_dqisad23adrfxMe12CWqhkT-c7t2M\n" #THESE APIS WILL NOT WORK ANY MORE
                                           "AIzaSyBJXjIeM8SmBQPe8asdZ2u6nSKd35Io5NjnNc\n" #THESE APIS WILL NOT WORK ANY MORE
                                           "AIzaSyBwxgX2lFoOjWhsasdpDuVBpUmPmUb4DE1h9A\n"
                                           "AIzaSyC6XGoNvHPhv7IfMadsViAfq5d_GsCpXdKoIw")


        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        self.start_button = ttk.Button(button_frame, text="Start Bot", command=self.start_bot)
        self.start_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.stop_button = ttk.Button(button_frame, text="Stop Bot", command=self.stop_bot, state=tk.DISABLED)
        self.stop_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        log_frame = ttk.LabelFrame(main_frame, text="Live Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def start_bot(self):
        keys_text = self.api_keys_text.get("1.0", tk.END)
        api_keys = keys_text.strip().split('\n')

        params = {
            "streamer": self.streamer_var.get(),
            "min_time": int(self.min_time_var.get()),
            "max_time": int(self.max_time_var.get()),
            "scrape_count": int(self.scrape_count_var.get()),
            "batch_size": int(self.batch_size_var.get()),
            "special_request": self.special_request_var.get(),
            "api_keys": api_keys,
            "cookie_file": 'kick_cookies.json'
        }
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        self.kick_bot = KickBot(params, lambda msg: self.after(0, self.log_message, msg))
        self.bot_thread = threading.Thread(target=self.kick_bot.run, daemon=True)
        self.bot_thread.start()
        self.monitor_thread()

    def stop_bot(self):
        if self.kick_bot:
            self.kick_bot.stop()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def monitor_thread(self):
        if self.bot_thread.is_alive():
            self.after(100, self.monitor_thread)
        else:
            self.stop_bot()

if __name__ == "__main__":
    app = KickBotGUI()
    app.mainloop()

