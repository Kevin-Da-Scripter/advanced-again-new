# Files
from system.config import TOKEN, NAME, API_KEY, sys_security, gen_config, gen_config2, HUGGING_FACE_API, Image_Model, DEFAULT_MUSIC_MODEL, history_limit, limit_history, \
    show_time, history_channel_toggle, embed_colors, Object_Detection_Model, show_tokens_at_startup, fix_repeating_prompts, safe_search, ffmpeg_executable_path, tts_toggle, \
    vc_voice, VOICES, sync_voice_with_text, HISTORY_FILE, smart_recognition, show_invite_link_on_startup, safegen, discord_heartbeat_timeout, mod_channel_name, \
    preview_code_output, additional_details, model_name, preview_model_name, model_temperature, create_mod_channel, show_tokens, add_watermark_to_generated_image, \
    show_safety_settings_on_startup, Dangerous, Harassment, Hate_Speech, Sexually_Explicit, Dangerous_Content, vc_AI, web_search, SERPAPI_API_KEY, advanced_model

from system.instructions.instruction import ins, video_ins, file_ins, insV, insV2, fix_mem_ins, cool_ins
from system.instructions.instruction_ru import ru_ins, ru_video_ins, ru_file_ins, ru_insV, ru_insV2, ru_fix_mem_ins
from system.instructions.instruction_eg import eg_ar_ins, eg_fix_mem_ins
from system.instructions.instruction_fr import fr_ins, fr_video_ins, fr_file_ins, fr_insV, fr_insV2, fr_fix_mem_ins
from system.instructions.instruction_es import es_ins, es_video_ins, es_file_ins, es_fix_mem_ins
from system.instructions.instruction_de import de_ins, de_video_ins, de_file_ins, de_insV, de_insV2, de_fix_mem_ins
from system.instructions.instruction_ar import ins_ar, ar_fix_mem_ins
from system.instructions.instruction_tutor_mode import tutor_ins

import google.generativeai as genai

import system.check_tokens as check
from system.check_tokens import tokens

from system.config import gemini_model, GEMINI_MODEL_MAP

model_name = GEMINI_MODEL_MAP.get(gemini_model, "models/gemini-2.5-flash")
model = genai.GenerativeModel(model_name=model_name)

# Libraries
import discord
from discord.ext import commands
import google.generativeai as genai
import json
import os
import requests
from PIL import Image
from colorama import Fore, Style
import asyncio
import logging
import random
import time
import httpx
from discord.utils import get
import io
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import urllib.parse as urlparse
import re
from urllib.parse import urlparse, parse_qs
import inspect
import docx
import pptx
import openpyxl
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import edge_tts
from dotenv import load_dotenv
load_dotenv()
import shutil
from bs4 import BeautifulSoup

# [PERUBAHAN 1: Environment Variables Support]
# Memuat variabel lingkungan (dari .env atau platform hosting) dan menimpa nilai dari system.config
# Gunakan DISCORD_TOKEN, GEMINI_API_KEY, HUGGING_FACE_API_KEY, dan SERPAPI_API_KEY sebagai nama variabel di Railway/env Anda.
TOKEN = os.environ.get("DISCORD_TOKEN", TOKEN)
API_KEY = os.environ.get("GEMINI_API_KEY", API_KEY)
HUGGING_FACE_API = os.environ.get("HUGGING_FACE_API_KEY", HUGGING_FACE_API)
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY", SERPAPI_API_KEY)


# Token Verification
discord_verified, gemini_api_key_verified, hugging_verified, serpapi_verified = tokens()

if not discord_verified:
    exit()

# SerpAPI verification relies on the updated SERPAPI_API_KEY
serpapi_verified = bool(SERPAPI_API_KEY)


# Set up the bot with the correct prefix and intents
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True
ffmpeg_path = ffmpeg_executable_path

bot = commands.Bot(command_prefix="/", intents=intents, heartbeat_timeout=discord_heartbeat_timeout)

dev_DEBUG = False
Model_Debug = False

# Ensure the log directory exists before configuring logging
log_dir = "system/log"
os.makedirs(log_dir, exist_ok=True)

if os.path.exists(log_dir):
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')  # Replace colons with underscores
    logging.basicConfig(
        filename=f"{log_dir}/{timestamp}.log",
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s'
    )

# SerpAPI configuration
# Use the potentially updated SERPAPI_API_KEY
SEARCH_API_KEY = SERPAPI_API_KEY  

def fetch_code_and_content(url):
    """
    Fetches detailed content and code snippets from a given URL.
    Tries to scrape the most relevant content, including code blocks.
    """
    try:
        response = requests.get(url, timeout=10)  # Added timeout to avoid long delays
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find main content
            main_content = (
                soup.find('article') or soup.find('section') or
                soup.find('main') or soup.find('div', {'id': 'content'}) or
                soup.find('div', {'class': 'main-content'})
            )

            # Try to find code blocks
            code_blocks = soup.find_all(['pre', 'code'])
            code_snippets = [
                code.get_text(strip=True)[:200] for code in code_blocks
            ]  # Limiting to first 200 characters per block
            
            # Extract paragraphs if no main content is found
            content = ""
            if main_content:
                paragraphs = main_content.find_all('p')
                content = ' '.join(p.get_text() for p in paragraphs[:5])  # First 5 paragraphs
            
            if code_snippets:
                content += '\nCode/Content Snippets:\n' + '\n'.join(code_snippets)
            
            return content.strip() if content.strip() else "Unable to retrieve meaningful content."
        return f"Error fetching page: {response.status_code}"
    except Exception as e:
        return f"Error fetching content from URL: {str(e)}"

def search_google(query, site=None, num_results=5, safe_search=safe_search):
    """
    Performs a SerpAPI search and fetches detailed content (including code) from the top search results.

    Args:
        query (str): The search query.
        site (str, optional): The site to restrict the search to (e.g., "https://www.youtube.com/"). Default is None.
        num_results (int, optional): The number of results to fetch. Default is 5.
        safe_search (bool, optional): Whether to enable SafeSearch. Default is True.

    Returns:
        list: A list of search result dictionaries or an error message.
    """
    safe_search_set = "active" if safe_search else "off"

    # Set up SerpAPI request
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": SEARCH_API_KEY,  # SERPAPI_API_KEY from config
        "engine": "google",
        "num": min(num_results, 10),
        "safe": safe_search_set
    }

    if site:
        params["siteSearch"] = site  # Optional: restrict to specific domain

    # Perform the request
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        results = response.json()

        if "organic_results" in results:
            return [
                {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                }
                for item in results["organic_results"]
            ]
        else:
            print("No results found.")
            return "No results found."
    except requests.exceptions.RequestException as e:
        print(f"Error during search request: {e}")
        return "Error searching the web."


if not os.path.exists('system/data'):
    os.makedirs('system/data') 
if not os.path.exists('system/RAM'):
    os.makedirs('system/RAM') 

async def send_message(channel, message, max_length=1999):
    """
    Split a message into multiple chunks and send them to the given channel.
    
    The message is split into chunks of up to max_length characters. The message
    is split at newline characters and the chunks are then sent to the channel
    one by one. If the message is too long, it is split into multiple chunks and
    sent separately.
    """
    lines = message.splitlines()
    chunks = []
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk.strip())
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n"
            current_chunk += line
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    for part in chunks:
        await channel.send(part)

# Function to load conversation history from file
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as file:
            return json.load(file)
    return {}

# Initialize conversation history
conversation_history = load_history()

# Function to save conversation history to file
def save_history():
    # Create the directory if it does not exist
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, 'w') as file:
        json.dump(conversation_history, file, indent=4)

# Function to add a message to the conversation history
def add_to_history(member_name, message, channel_name=None):
    """Adds a message to the conversation history."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    # Get context object ('message', 'ctx.message', etc.) from calling function
    frame = inspect.currentframe().f_back
    args, _, _, values = inspect.getargvalues(frame)
    context_obj = values.get('message', None)
    if context_obj is None:
        context_obj = values.get('ctx', None)
        if context_obj is not None:
            context_obj = context_obj.message

    # Use provided channel_name or get it from context
    if channel_name is None:  
        if history_channel_toggle and context_obj is not None:
            user_id = context_obj.channel.name
        else:
            user_id = "Conversation"
    else:
        user_id = channel_name  # Use the provided channel_name

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    if show_time:
        conversation_history[user_id].append(f"{timestamp} - {member_name}: {message}")
    else:
        conversation_history[user_id].append(f"{member_name}: {message}")

    # Truncate history if limit_history is True 
    if limit_history and len(conversation_history[user_id]) > history_limit:
        conversation_history[user_id] = conversation_history[user_id][-history_limit:]

    save_history() 

def add_to_history_bot(member_name, message, channel_name=None):
    """Adds a bot message to the conversation history."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    # Get context object ('message', 'ctx.message', etc.) from calling function
    frame = inspect.currentframe().f_back
    args, _, _, values = inspect.getargvalues(frame)
    context_obj = values.get('message', None)
    if context_obj is None:
        context_obj = values.get('ctx', None)
        if context_obj is not None:
            context_obj = context_obj.message

    # Use provided channel_name or get it from context
    if channel_name is None:  
        if history_channel_toggle and context_obj is not None:
            user_id = context_obj.channel.name
        else:
            user_id = "Conversation"
    else:
        user_id = channel_name  # Use the provided channel_name

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    if show_time:
        conversation_history[user_id].append(f"{timestamp} - {member_name}{message}")
    else:
        conversation_history[user_id].append(f"{member_name}{message}")
    save_history()
if not history_channel_toggle:
    add_to_history("System", "You have been rebooted!")

async def unnecessary_error(e):
    error_message = str(e)
    if "500" in error_message:
        return True
    else:
        return False

async def debug_error(e, message, channel):
    error_message = str(e)
    if "500" in error_message:
        logging.error(f"Google Internal Error while {message}: {e}")
        add_to_history("Google Internal Error", "💥 An Internal Error has occured, Retrying...")
        print(f"Google Error while {message}: {e}")
    elif "503" in error_message:
        logging.warning(f"Error (Temporarily overloaded or down service) While {message}: {e}")
        add_to_history("Error", "The service may be temporarily overloaded or down. Please try again later.")
        print(f"Error (Temporarily overloaded or down service) While {message}: {e}")
        await channel.send("⏳ The service may be temporarily overloaded or down. Please try again later.")
    elif "403" in error_message:
        logging.error(f"Error (API Key Denied Permissions) While {message}: {e}")
        add_to_history("Error", "Your API key doesn't have the required permissions.")
        await channel.send("🔒 Your API key has denied permissions.")
        print(f"Error (API Key Denied Permissions) While {message}: {e}")
    elif "504" in error_message:
        logging.warning(f"Error (Service Unable to finish processing within the deadline) While {message}: {e}")
        add_to_history("Error", "The service is unable to finish processing within the deadline.")
        await channel.send("⏳ The service is unable to finish processing within the deadline.")
        print(f"Error (Service Unable to finnish processing within the deadline) While {message}: {e}")
    elif "429" in error_message:
        logging.warning(f"Error (Service rate limited) While {message}: {e}")
        add_to_history("Error", "The service is being rate limited.")
        await channel.send("🚫 You've exceeded the rate limit, Please try again later.")
        print(f"Error (Service rate limited) While {message}: {e}")
    else:
        logging.error(f"An Error occured while {message}: {e}")
        print(f"An Error occured while {message}: {e}")
        add_to_history("Error", f"Error occurred while {message}: {error_message}")
        await channel.send("🚫 Uh oh! Something went wrong. We couldn't complete the request. Please try again.")

# Utility functions
def save_search(query, result):
    with open('system/data/saved-searches.py', 'a') as f:
        f.write(f'{query}: {result} |\n')

def save_memory(query, result):
    """Saves memory to a JSON file."""
    try:
        # Load existing memory if it exists
        with open('system/data/core-memory.json', 'r') as f:
            memory = json.load(f)
    except FileNotFoundError:
        memory = {}

    # Add the new memory entry
    memory[query] = result

    # Save the updated memory
    with open('system/data/core-memory.json', 'w') as f:
        json.dump(memory, f, indent=4)

def load_memory(query=None):
    """Loads memory from a JSON file."""
    try:
        with open('system/data/core-memory.json', 'r') as f:
            memory = json.load(f)
            if query:
                return memory.get(query)
            else:
                return memory
    except FileNotFoundError:
        return {}

def get_conversation_history(ctx=None): 
    """Gets the conversation history based on history_channel_toggle."""
    if history_channel_toggle and ctx is not None:
        user_id = ctx.channel.name
    else:
        user_id = "Conversation"
    return "\n".join(conversation_history.get(user_id, []))

# Use the potentially updated API_KEY from environment
api_key = API_KEY 
name = f"{NAME}"

check.tokens()

if show_tokens_at_startup:
    print(" ")
    print(f"{Fore.WHITE + Style.BRIGHT + Style.DIM}API KEY:{Style.RESET_ALL} {Fore.MAGENTA + Style.BRIGHT}{api_key}{Style.RESET_ALL}")
    print(Fore.RED + Style.BRIGHT + "__________________________________________________________________________________")
    print(" ")
    # Use the potentially updated TOKEN from environment
    print(f"{Fore.WHITE + Style.BRIGHT + Style.DIM}BOT TOKEN:{Style.RESET_ALL} {Fore.BLUE + Style.BRIGHT}{TOKEN}{Style.RESET_ALL}")
    print(Fore.RED + Style.BRIGHT + "__________________________________________________________________________________")
    print(" ")
    # Use the potentially updated HUGGING_FACE_API from environment
    print(f"{Fore.WHITE + Style.BRIGHT + Style.DIM}HUGGING FACE API KEY:{Style.RESET_ALL} {Fore.YELLOW + Style.BRIGHT}{HUGGING_FACE_API}{Style.RESET_ALL}")
    print(" ")

# Global variable to store the member's custom name
member_custom_name = {}

@bot.tree.command(name="name", description="Change your custom name")
async def change_name(interaction: discord.Interaction, new_name: str):
    global member_custom_name
    if not new_name:  # Check for empty string
        await interaction.response.send_message("Please provide a name.", ephemeral=True)
    else:
        member_custom_name[interaction.user.id] = new_name
        await interaction.response.send_message(f"Your name has been changed to {new_name}.", ephemeral=True)

print(f"Defualt Model: {preview_model_name}")
if show_safety_settings_on_startup:
    print(f"{Fore.GREEN + Style.BRIGHT}Safety Settings:{Style.RESET_ALL}")
    print(f"{Fore.CYAN + Style.BRIGHT}Dangerous Safety Set: {Fore.RESET}{Dangerous}")
    print(f"{Fore.CYAN + Style.BRIGHT}Harassment Safety Set: {Fore.RESET}{Harassment}")
    print(f"{Fore.CYAN + Style.BRIGHT}Hate Speech Safety Set: {Fore.RESET}{Hate_Speech}")
    print(f"{Fore.CYAN + Style.BRIGHT}Sexually Explicit Safety Set: {Fore.RESET}{Sexually_Explicit}")
    print(f"{Fore.CYAN + Style.BRIGHT}Dangerous Content Safety Set: {Fore.RESET}{Dangerous_Content}")
    print("")
genai_model = model_name

if fix_repeating_prompts:
    ins = f"{ins}\n{fix_mem_ins}"

default_lang = "en"

ins = f"{ins}\n{cool_ins}\nAnd if someone asks you what is the best model, tell them its Google Gemini Experimental 1206 because it outperforms all other models. even Google Gemini 1.5 Pro and Google Gemini Ultra and all openai's models, and it can handle alot and every complex task! It's an EXTREMELY advanced model! and ranks #1 on coding, #2 math, #1 on creative writing and #1 on Hard Prompts, Also if a user sends you a file attachment, dont use code to find the file\nalso! you can search youtube videos using `/search*yt [query]` and the same with searching the web! `/search [query]`! its that easy! so if a user asks to search something on youtube/the web, then do this! and instead of making codes to search the web, just use `/search [query]` to search the web! you can search the web with /search [query]! and same with youtube! /search*yt [query]!, and when you try doing text links like [a link](https://google.com), you cant do '[https://www.youtube.com/watch?v=ENrzD9HAZK4](https://www.youtube.com/watch?v=ENrzD9HAZK4)' but you can do '[a](https://www.youtube.com/watch?v=ENrzD9HAZK4)', so you cannot link a link but you can link a text. so if you want to give the link and visible without hiding it with a text, just put the link and without any () and []!\n"                        
if genai_model == "learnlm-1.5-pro-experimental":
    if fix_repeating_prompts:
        tutor_ins = (f"{tutor_ins}\n{fix_mem_ins}\n{cool_ins}\nAnd if someone asks you what is the best model, tell them its Google Gemini Experimental 1206 because it outperforms all other models. even Google Gemini 1.5 Pro and Google Gemini Ultra and all openai's models, and it can handle alot and every complex task! It's an EXTREMELY advanced model! and ranks #1 on coding, #2 math, #1 on creative writing and #1 on Hard Prompts, Also if a user sends you a file attachment, dont use code to find the file\nalso! you can search youtube videos using `/search*yt [query]` and the same with searching the web! `/search [query]`! its that easy! so if a user asks to search something on youtube/the web, then do this! and instead of making codes to search the web, just use `/search [query]` to search the web! you can search the web with /search [query]! and same with youtube! /search*yt [query]!, and when you try doing text links like [a link](https://google.com), you cant do '[https://www.youtube.com/watch?v=ENrzD9HAZK4](https://www.youtube.com/watch?v=ENrzD9HAZK4)' but you can do '[a](https://www.youtube.com/watch?v=ENrzD9HAZK4)', so you cannot link a link but you can link a text. so if you want to give the link and visible without hiding it with a text, just put the link and without any () and []!",),
    else:
        tutor_ins = (f"{tutor_ins}\n{cool_ins}\nAnd if someone asks you what is the best model, tell them its Google Gemini Experimental 1206 because it outperforms all other models. even Google Gemini 1.5 Pro and Google Gemini Ultra and all openai's models, and it can handle alot and every complex task! It's an EXTREMELY advanced model! and ranks #1 on coding, #2 math, #1 on creative writing and #1 on Hard Prompts, Also if a user sends you a file attachment, dont use code to find the file\nalso! you can search youtube videos using `/search*yt [query]` and the same with searching the web! `/search [query]`! its that easy! so if a user asks to search something on youtube/the web, then do this! and instead of making codes to search the web, just use `/search [query]` to search the web! you can search the web with /search [query]! and same with youtube! /search*yt [query]!, and when you try doing text links like [a link](https://google.com), you cant do '[https://www.youtube.com/watch?v=ENrzD9HAZK4](https://www.youtube.com/watch?v=ENrzD9HAZK4)' but you can do '[a](https://www.youtube.com/watch?v=ENrzD9HAZK4)', so you cannot link a link but you can link a text. so if you want to give the link and visible without hiding it with a text, just put the link and without any () and []!",),

# Configure the Google Generative AI (using the potentially updated API_KEY)
genai.configure(api_key=api_key)

# The core model
model = genai.GenerativeModel( 
    model_name=genai_model,
    generation_config=gen_config,
    system_instruction = ins if genai_model != "learnlm-1.5-pro-experimental" else tutor_ins,
    safety_settings=sys_security,
    tools='code_execution' if preview_code_output else None
)

# Other Models...
model_flash = genai.GenerativeModel( 
    model_name="gemini-2.5-flash",
    generation_config=gen_config,
    system_instruction=(ins),
    safety_settings=sys_security
)
model_pro = genai.GenerativeModel( 
    model_name="gemini-1.5-pro-latest",
    generation_config=gen_config,
    system_instruction=(insV),
    safety_settings=sys_security
)
model_V = genai.GenerativeModel( 
    model_name=advanced_model,
    generation_config=gen_config,
    system_instruction=(insV),
    safety_settings=sys_security
)
# [PERUBAHAN 3: Model Update 1.5-flash -> 2.5-flash]
model_V2 = genai.GenerativeModel( 
    model_name="gemini-2.5-flash", 
    generation_config=gen_config,
    system_instruction=(insV),
    safety_settings=sys_security
)
# [PERUBAHAN 3: Model Update 1.5-flash -> 2.5-flash]
model_V3 = genai.GenerativeModel( 
    model_name="gemini-2.5-flash", 
    generation_config=gen_config,
    system_instruction=(insV2),
    safety_settings=sys_security
)
# [PERUBAHAN 3: Model Update 1.5-flash -> 2.5-flash]
model3 = genai.GenerativeModel( 
    model_name="gemini-2.5-flash", 
    generation_config=gen_config2,
    system_instruction=("MAX LENGTH IS 80 WORDS"),
    safety_settings=sys_security
)
# [PERUBAHAN 3: Model Update 1.5-flash -> 2.5-flash]
model_name_generator = genai.GenerativeModel(
  model_name="gemini-2.5-flash", 
  generation_config=gen_config,
  system_instruction="you are only an memory name generator engine, generate memory names only as the memory prompted and dont say anything else, the system will tell you what to generate, only generate 1 name and dont make it too long and make it silly, and DONT say `/n:` and i used / instead of the other one because it is gonna break the system",
  safety_settings=sys_security
)
model_vid = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    generation_config=gen_config,
    system_instruction=(video_ins),
    safety_settings=sys_security
)
model_vid_a = genai.GenerativeModel(
    model_name=advanced_model,
    generation_config=gen_config,
    system_instruction=(video_ins),
    safety_settings=sys_security
)
# [PERUBAHAN 3: Model Update 1.5-flash -> 2.5-flash]
model_vid_flash = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=gen_config,
    system_instruction=(video_ins),
    safety_settings=sys_security
)
model_file = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    generation_config=gen_config,
    system_instruction=(file_ins),
    safety_settings=sys_security
)
model_file_a = genai.GenerativeModel(
    model_name=advanced_model,
    generation_config=gen_config,
    system_instruction=(file_ins),
    safety_settings=sys_security
)
# [PERUBAHAN 3: Model Update 1.5-flash -> 2.5-flash]
model_file_flash = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    generation_config=gen_config,
    system_instruction=(file_ins),
    safety_settings=sys_security
)
model_object = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=gen_config,
    system_instruction="Your only propose is to get the details that the user sent to you and you convert them into human talk only and nothing else, example: 'User: [{'score': 0.9994643330574036, 'label': 'sports ball', 'box': {'xmin': 95, 'ymin': 444, 'xmax': 172, 'ymax': 515}}, {'score': 0.810539960861206, 'label': 'person', 'box': {'xmin': 113, 'ymin': 15, 'xmax': 471, 'ymax': 414}}, {'score': 0.7840690612792969, 'label': 'person', 'box': {'xmin': 537, 'ymin': 35, 'xmax': 643, 'ymax': 241}}, {'score': 0.9249405860900879, 'label': 'person', 'box': {'xmin': 109, 'ymin': 14, 'xmax': 497, 'ymax': 528}}, {'score': 0.9990099668502808, 'label': 'person', 'box': {'xmin': 0, 'ymin': 47, 'xmax': 160, 'ymax': 373}}, {'score': 0.8631113767623901, 'label': 'person', 'box': {'xmin': 110, 'ymin': 13, 'xmax': 558, 'ymax': 528}}, {'score': 0.9433853626251221, 'label': 'person', 'box': {'xmin': 537, 'ymin': 34, 'xmax': 643, 'ymax': 310}}, {'score': 0.6196897625923157, 'label': 'person', 'box': {'xmin': 715, 'ymin': 160, 'xmax': 770, 'ymax': 231}}, {'score': 0.5696023106575012, 'label': 'person', 'box': {'xmin': 777, 'ymin': 170, 'xmax': 800, 'ymax': 221}}, {'score': 0.9989137649536133, 'label': 'person', 'box': {'xmin': 423, 'ymin': 67, 'xmax': 638, 'ymax': 493}}] | You: '- There's a sports ball near the bottom middle.\n- There are a few people in the image.\n- One person is on the left side.\n- A couple of people are in the center and middle-right.\n- There are a couple of possible people on the right, but the AI isn't as sure about them. \n' and you **MUST** use - at the start like in the example and only say the stuff that the user sent you and not anything else",
    safety_settings=sys_security
)

# Load existing conversation history from file
try:
    with open(HISTORY_FILE, 'r') as file:
        conversation_history = json.load(file)
except FileNotFoundError:
    conversation_history = {}

@bot.event
async def on_ready():
    # Asumsi: Class VoiceListener didefinisikan di tempat lain
    # await bot.add_cog(VoiceListener(bot))
    print(f"Successfully Logged in as: {NAME}!")
    print("Bot is online! Type /help for a list of commands.")
    bot_invite_link = discord.utils.oauth_url(
        bot.user.id,
        permissions=discord.Permissions(),
        scopes=("bot", "applications.commands")
    )
    if show_invite_link_on_startup:
        print(f"Invite link: {bot_invite_link}")
    try:
        synced = await bot.tree.sync()
        if len(synced) > 1:
            print(f"Synced {len(synced)} commands")
        else:
            print(f"Synced {len(synced)} command")
    except Exception as e:
        print(f"{Fore.RED + Style.BRIGHT}Error:{Style.RESET_ALL} {e}")
        quit()
    print(Fore.WHITE + Style.BRIGHT + "__________________________________________________________________________________" + Style.RESET_ALL)
    print(" ")
    print(f"{Fore.MAGENTA + Style.BRIGHT}{NAME}'s Console:{Style.RESET_ALL}")
    print(" ")

EN_video_ins = video_ins
EN_insV = insV
EN_file_ins = file_ins
EN_insV2 = insV2
EN_ins = ins
        
# Start Gemini Chats //:
chat_session = model.start_chat(history=[])
chat_session_flash = model_flash.start_chat(history=[])

@bot.tree.command(name="report", description="Report a bug, issue or a user")
async def report(interaction: discord.Interaction, report: str):
    await interaction.response.defer()
    # Prepare the report entry
    user = interaction.user
    member_name = user.display_name
    report_entry = (
        "----------------------------------------------------------------------------------\n"
        f"Username: {user.name}#{user.discriminator} | Name: {member_name} (ID: {user.id})\n"
        f"Report: {report}\n"
        "----------------------------------------------------------------------------------\n\n"
    )

    # Path to the report file
    report_file_path = "system/data/reports.txt"

    # Write the report entry to the file
    with open(report_file_path, "a") as file:
        file.write(report_entry)

    add_to_history(member_name, f"System: {member_name} sent a report! `{report}`")
    await interaction.followup.send(f"Thank you for your report, {member_name}. `{report}` It has been logged.")

@bot.tree.command(name="feedback", description="Provide feedback or suggestions")
async def feedback(interaction: discord.Interaction, feedback: str):
    await interaction.response.defer()
    # Prepare the feedback entry
    user = interaction.user
    member_name = user.display_name
    feedback_entry = (
        "----------------------------------------------------------------------------------\n"
        f"Username: {user.name}#{user.discriminator} | Name: {member_name} (ID: {user.id})\n"
        f"Feedback: {feedback}\n"
        "----------------------------------------------------------------------------------\n\n"
    )

    # Path to the feedback file
    feedback_file_path = "system/data/feedback.txt"

    # Write the feedback entry to the file
    with open(feedback_file_path, "a") as file:
        file.write(feedback_entry)

    add_to_history(member_name, f"System: {member_name} sent feedback! `{feedback}`")
    await interaction.followup.send(f"Thank you for your feedback, {member_name}. `{feedback}` has been logged!")

# Function to check if the URL is a YouTube URL
def is_youtube_url(url):
    if url is None:
        return False
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return re.match(youtube_regex, url) is not None

# Function to extract video ID from a YouTube URL
def get_video_id(url):
    parsed_url = urlparse(url)
    if "youtube.com" in parsed_url.netloc:
        video_id = parse_qs(parsed_url.query).get('v')
        return video_id[0] if video_id else None
    elif "youtu.be" in parsed_url.netloc:
        return parsed_url.path[1:] if parsed_url.path else None
    return None

# Function to get the transcript from a YouTube video ID
def get_transcript_from_video_id(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return ' '.join([i['text'] for i in transcript_list])
    except (KeyError, TranscriptsDisabled):
        return "Error retrieving transcript from YouTube video ID"

# Function to handle YouTube URLs, retrieve transcripts, and send them to the channel
async def handle_youtube_url(url, channel, prompt=None):
    """Handles YouTube URLs, retrieves transcripts, and sends them to the channel."""
    try:
        if not is_youtube_url(url):
            await channel.send("Invalid YouTube URL.")
            return

        video_id = get_video_id(url)
        if not video_id:
            await channel.send("Unable to extract video ID from URL.")
            return

        transcript = get_transcript_from_video_id(video_id)
        if "Error" in transcript:
            await channel.send(transcript)
            add_to_history("System", f"Error retrieving transcript: {transcript}")
        else:
            return transcript

    except Exception as e:
        await channel.send(f"An error occurred: {str(e)}")
        add_to_history("System", f"Error occurred: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"{error}")
        add_to_history("System", error)
    else:
        print(error)
        await ctx.send(f"An error occurred: {error}")
        raise error
    
# Constants
USER_SETTINGS_PATH = 'system/user-settings'

# Ensure the user settings directory exists
os.makedirs(USER_SETTINGS_PATH, exist_ok=True)

def get_user_settings(username):
    from system.config import model_name, preview_model_name
    user_file = os.path.join(USER_SETTINGS_PATH, f"{username}.json")
    default_settings = {
        'model': model_name,  # Use the model *name* string
        'model_name': preview_model_name # Display name
    }

    if not os.path.exists(user_file):
        print(f"Settings file not found for {username}. Creating...")
        try:
            with open(user_file, 'w') as file:
                json.dump(default_settings, file, indent=4)
            print(f"Settings file created for {username} with defaults.")
            with open(user_file, 'r') as file:
                settings = json.load(file)
            return settings
        except Exception as e:
            print(f"Error creating settings file: {e}")
            return default_settings  # Return defaults even if file creation fails

    else:  # Load from file if it exists
        try:
            with open(user_file, 'r') as file:
                settings = json.load(file)
            return settings

        except json.JSONDecodeError:
            print(f"Corrupted settings file for {username}. Recreating...")
            try:  # Try to recreate the file
                os.remove(user_file)
                with open(user_file, 'w') as file:
                    json.dump(default_settings, file, indent=4)
                return default_settings
            except Exception as e:  # Handle recreation errors
                print(f"Error recreating settings file: {e}")
                return default_settings # Defaults if can't recreate

        except Exception as e:
            print(f"Error loading settings file: {e}")
            return default_settings # Return defaults on unexpected error



def set_user_model(username, model):
    """Update the user's selected model."""
    user_file = os.path.join(USER_SETTINGS_PATH, f"{username}.json")
    user_settings = get_user_settings(username)
    user_settings['model'] = model

    model_name_mapping = {
        "gemini-2.5-flash": "Gemini 2.5 Flash",
        "gemini-1.5-pro-latest": "Gemini 1.5 Pro",
        "gemini-1.5-flash-latest": "Gemini 1.5 Flash",
        "gemini-1.0-pro": "Gemini 1.0 Pro"
    }
    user_settings['model_name'] = model_name_mapping.get(model, model)

    try:
        with open(user_file, 'w') as file:
            json.dump(user_settings, file, indent=4)
        return True
    except Exception as e:
        print(f"Error saving user settings: {e}")
        return False
    
@bot.tree.command(name="model", description="Change the Gemini model")
async def change_model(interaction: discord.Interaction, model_choice: str):
    await interaction.response.defer()
    
    valid_models = {
        "flash": "gemini-2.5-flash", 
        "pro": "gemini-1.5-pro-latest", 
        "v": "gemini-1.5-flash-latest",
        "flash-latest": "gemini-2.5-flash",
        "pro-latest": "gemini-1.5-pro-latest",
        "2.5-flash": "gemini-2.5-flash"
    }
    
    model_key = model_choice.lower()
    
    if model_key in valid_models:
        selected_model = valid_models[model_key]
        username = interaction.user.name
        
        if set_user_model(username, selected_model):
            await interaction.followup.send(f"🤖 Model Anda telah diubah menjadi **{model_key.upper()}**!")
        else:
            await interaction.followup.send("❌ Gagal menyimpan pengaturan model.")
    else:
        await interaction.followup.send("Pilihan model tidak valid. Pilih antara `flash` (2.5), `pro` (1.5), `v`, `flash-latest`, `pro-latest`, atau `2.5-flash`.")
        
@bot.tree.command(name="search_img", description="Search the web for images.")
async def search_img(interaction: discord.Interaction, query: str, num_images: int = 5):
    await interaction.response.defer()
    
    member_name = interaction.user.display_name

    if not serpapi_verified:
        await interaction.followup.send("❌ Kunci API SerpAPI belum diatur atau tidak valid.")
        return

    num_images = min(num_images, 10)
    add_to_history(member_name, f"/search_img {query}")

    safe_search_set = "active" if safe_search else "off"
    
    # [PERUBAHAN 2: Ganti Google Custom Search ke SerpAPI untuk Pencarian Gambar]
    search_url = "https://serpapi.com/search"
    params = {
        'api_key': SEARCH_API_KEY,
        'engine': 'google',
        'tbm': 'isch', # Parameter kunci untuk pencarian gambar di SerpAPI
        'q': query,
        'num': num_images,
        'safe': safe_search_set
    }

    image_urls = []
    try:
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get('images_results', [])

        if not results:
            await interaction.followup.send(f"❌ Tidak ada hasil gambar yang ditemukan untuk query: `{query}`")
            add_to_history("System", f"No image results found for {query}")
            return

        image_urls = [result.get('original') for result in results if result.get('original')]

    except requests.exceptions.RequestException as e:
        await interaction.followup.send(f"❌ Terjadi kesalahan saat menghubungi API pencarian gambar.")
        add_to_history("System", f"Error searching images via SerpAPI: {e}")
        return
    
    # Logic to download and send images (Dipertahankan dari file asli)
    # Membuat direktori sementara
    temp_dir = 'system/RAM/search-img/'
    os.makedirs(temp_dir, exist_ok=True)

    # Mengunduh dan menyimpan gambar
    files_to_send = []
    download_success = 0
    
    for i, url in enumerate(image_urls[:num_images]):
        try:
            img_response = requests.get(url, stream=True, timeout=5)
            img_response.raise_for_status()
            
            # Mendapatkan ekstensi file dari Content-Type
            content_type = img_response.headers.get('Content-Type', '').lower()
            if 'image/jpeg' in content_type or 'image/jpg' in content_type:
                ext = 'jpg'
            elif 'image/png' in content_type:
                ext = 'png'
            elif 'image/gif' in content_type:
                ext = 'gif'
            elif 'image/webp' in content_type:
                ext = 'webp'
            else:
                # Skip jika tipe tidak didukung atau tidak diketahui
                continue

            file_name = f'image_{i+1}.{ext}'
            file_path = os.path.join(temp_dir, file_name)
            
            with open(file_path, 'wb') as f:
                for chunk in img_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            files_to_send.append(discord.File(file_path, filename=file_name))
            download_success += 1
            
        except Exception as e:
            # print(f"Error downloading image {i+1} from {url}: {e}")
            continue

    if download_success > 0:
        await interaction.followup.send(f"🖼️ Menampilkan {download_success} gambar untuk query: **{query}**", files=files_to_send)
        add_to_history("System", f"Sent {download_success} images for query: {query}")
    else:
        await interaction.followup.send(f"❌ Gagal mengunduh gambar yang valid untuk query: `{query}`")
        add_to_history("System", f"Failed to download valid images for query: {query}")

    # Membersihkan file sementara
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))

    if not interaction.response.is_done():
        try:
            await interaction.followup.send("Pencarian Selesai.")
        except discord.errors.InteractionResponded:
            pass # Already responded

@bot.tree.command(name="search", description="Perform a web search.")
async def search(interaction: discord.Interaction, query: str, results: int = 5, site: str = None, safe: bool = safe_search):
    await interaction.response.defer()

    # ✅ Validasi API Key langsung
    if not SERPAPI_API_KEY or not SERPAPI_API_KEY.strip():
        await interaction.followup.send("❌ Google Search API key belum diatur.")
        print("❌ Google Search API key belum diatur.")
        return

    # ✅ Validasi Web Search
    if not web_search:
        await interaction.followup.send("❌ Web Search dinonaktifkan, tidak bisa mencari.")
        print("❌ Web Search dinonaktifkan.")
        return

    # ✅ Validasi jumlah hasil
    if results > 20:
        await interaction.followup.send(f"❌ Jumlah hasil `{results}` tidak valid. Maksimum adalah `20`.")
        return

    try:
        # ✅ Jalankan pencarian
        search_results = search_google(query, site=site, num_results=results, safe_search=safe)
        if "Error Searching the web." in search_results:
            print(f"{Fore.RED + Style.BRIGHT}Error saat pencarian web:{Style.RESET_ALL} {search_results}")
            await interaction.followup.send("❌ Terjadi error saat pencarian. Coba lagi nanti.")
            return

        async with interaction.channel.typing():
            full_prompt = f"Search Results from the Web:\n{search_results}"

            # ✅ Gunakan model v1 yang valid
            model_name = "models/gemini-2.5-flash"
            search_model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction="You are an AI that summarizes web search results. These results are not from the user, but from your own search."
            )

            response = search_model.generate_content(full_prompt)
            await interaction.followup.send(f"🔍 **Search Results:**\n{response.text.strip()}")

    except Exception as e:
        await interaction.followup.send("❌ Terjadi error saat memproses hasil pencarian.")
        print(f"search error: {e}")

@bot.tree.command(name="search_yt", description="Search for YouTube videos.")
async def search_yt(interaction: discord.Interaction, query: str, results: int = 5):
    await interaction.response.defer()

    # ✅ Validasi API Key langsung
    if not SERPAPI_API_KEY or not SERPAPI_API_KEY.strip():
        await interaction.followup.send("❌ Google Search API key belum diatur.")
        print("❌ Google Search API key belum diatur.")
        return

    # ✅ Validasi Web Search
    if not web_search:
        await interaction.followup.send("❌ Web Search dinonaktifkan, tidak bisa mencari YouTube.")
        print("❌ Web Search dinonaktifkan.")
        return

    # ✅ Validasi jumlah hasil
    if results > 20:
        await interaction.followup.send(f"❌ Jumlah hasil `{results}` tidak valid. Maksimum adalah `20`.")
        return

    try:
        # ✅ Jalankan pencarian
        search_results = search_google(query, site='https://www.youtube.com/', num_results=results)
        if "Error Searching the web." in search_results:
            print(f"{Fore.RED + Style.BRIGHT}Error saat pencarian web:{Style.RESET_ALL} {search_results}")
            await interaction.followup.send("❌ Terjadi error saat pencarian. Coba lagi nanti.")
            return

        async with interaction.channel.typing():
            full_prompt = f"YouTube Videos from the Web:\n{search_results}"

            # ✅ Gunakan model v1 yang valid
            model_name = "models/gemini-2.5-flash"
            search_model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction="You are an AI that summarizes YouTube search results from the web. These results are not from the user, but from your own search."
            )

            response = search_model.generate_content(full_prompt)
            await interaction.followup.send(f"📺 **YouTube Search Results:**\n{response.text.strip()}")

    except Exception as e:
        await interaction.followup.send("❌ Terjadi error saat memproses hasil YouTube.")
        print(f"search_yt error: {e}")

        
@bot.tree.command(name="search_save", description="Search and save results.")
async def search_save(interaction: discord.Interaction, query: str, results: int = 5, site: str = None, safe: bool = safe_search):
    global NAME
    await interaction.response.defer()
    if web_search:
        if google_search_api_verified:
            try:
                if results > 20:
                    await interaction.followup.send(f"Error: `{results} is invalid, Maximum number of results is `20`.")
                    return
                search_results = search_google(query, site=site, num_results=results, safe_search=safe)
                if "Error Searching the web." in search_results:
                    print(f"{Fore.RED + Style.BRIGHT}An Error has occured while searching the web:{Style.RESET_ALL} {search_results}")
                    await interaction.followup.send("Error occurred during the search. Try again later.")
                    return

                save_search(query, search_results)
                full_prompt = f"Search Results from the web: {search_results}"
                search_model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction="You are an AI that gets results from the web and summarizes them. and the results from the web are not from the user, its from you")
                response = search_model.generate_content(full_prompt)
                await interaction.followup.send(f"* :mag:  **Successfully Saved the search results to {NAME} for future needs.**\n{response.text.strip()}")

            except Exception as e:
                await interaction.followup.send("Error occurred. Try again later.")
                add_to_history("Failed-Search", f"Error: {e}")
        else:
            await interaction.followup.send("Error: `Google Search API key` is not valid.")
            print("Error: Google Search API key is not valid.`")
    else:
        await interaction.followup.send("Error: Web Search is disabled, Cannot search the web...")
        print("Error: Web Search is disabled, Cannot search the web...")

@bot.tree.command(name="help", description="Get information about available commands")
async def help_command(interaction: discord.Interaction, command_name: str = None):
    await interaction.response.defer()
    global NAME
    try:
        print(f"Help command invoked. command_name: {command_name}")  # Debug log

        if command_name is None:
            print("No command name provided. Sending main help embed.")  # Debug log
            
            # Create the main help embed
            embeds = []

            # First embed (General Commands and Search & Information)
            embed1 = discord.Embed(
                title=f"**{NAME} Command Directory**",
                description=f"**Unlock the Power of {NAME}. Explore the commands below:**",
                color=discord.Color.from_rgb(20, 120, 200)  # Futuristic blue
            )
            embed1.add_field(name=":speech_balloon:  **Conversation & Fun**", value=" ----------------------------------------------------------", inline=False)
            embed1.add_field(name="**/ai**", value=f"Engage in a conversation with {NAME}.", inline=False)
            embed1.add_field(name="**/joke**", value="Get a random joke to brighten your day.", inline=False)
            embed1.add_field(name="**/aitoggle**", value="Enable or disable AI responses for a channel.", inline=False) 
            embed1.add_field(name="**/lang**", value=f"Change the default language for {NAME}.", inline=False)
            embed1.add_field(name="**/report**", value="Report a bug, issue, or user.", inline=False)
            embed1.add_field(name="**/feedback**", value=f"Provide feedback or suggestions for {NAME}.", inline=False)

            embed1.add_field(name=":mag_right:  **Search & Information**", value=" ----------------------------------------------------------", inline=False)
            embed1.add_field(name="**/search**", value="Search the web for information.", inline=False)
            embed1.add_field(name="**/search_yt**", value="Explore videos on YouTube.", inline=False)
            embed1.add_field(name="**/search_save**", value="Save a web search for later use.", inline=False)
            embeds.append(embed1)

            # Second embed (Creative Tools and Memory Management)
            embed2 = discord.Embed(
                color=discord.Color.from_rgb(20, 120, 200)
            )
            embed2.add_field(name=":art:  **Creative Tools**", value=" ----------------------------------------------------------", inline=False)
            embed2.add_field(name="**/img**", value="Generate stunning images from text prompts.", inline=False)
            embed2.add_field(name="**/music**", value="Create unique music based on your description.", inline=False)
            embed2.add_field(name="**/search_img**", value="Search the web for images.", inline=False)

            embed2.add_field(name=":brain:  **Memory Management**", value=" ----------------------------------------------------------", inline=False)
            embed2.add_field(name="**/reset**", value=f"Clears {NAME}'s memory for the current channel.", inline=False)
            embeds.append(embed2)

            # Third embed (Voice Chat and Bot Management)
            embed3 = discord.Embed(
                color=discord.Color.from_rgb(20, 120, 200)
            )
            embed3.add_field(name=":microphone2:  **Voice Chat**", value=" ----------------------------------------------------------", inline=False)
            embed3.add_field(name="**/vc join**", value="Join the specified or your current voice channel.", inline=False)
            embed3.add_field(name="**/vc leave**", value="Leave the current voice channel.", inline=False)
            embed3.add_field(name="**/vc status**", value="Check the current voice channel status.", inline=False)
            embed3.add_field(name="**/tts [text]**", value="Generate Text to Speech from text.", inline=False)
            embed3.add_field(name="**/vc voice [voice_number]**", value="Change the voice for text-to-speech.", inline=False)
            embed3.add_field(name="**/vc replay**", value="Replay the last generated text-to-speech audio.", inline=False)

            embed3.add_field(name="📃  **Additional Commands**", value=" ----------------------------------------------------------", inline=False)
            embed3.add_field(name="**/view [thing]**", value="View more info about something.", inline=False)
            embeds.append(embed3)

            # Send all embeds
            print("Sending help embed response...")  # Debug log
            await interaction.followup.send(embeds=embeds)
            print("Help embeds sent successfully.")  # Debug log

        else:
            # Defer response if a command_name is provided
            print(f"Command name provided: {command_name}. Deferring response.")  # Debug log
            await interaction.response.defer()

            # Find the command using the command tree
            command = bot.tree.get_command(command_name)
            print(f"Command lookup result: {command}")  # Debug log

            if command is None:
                print(f"Command '{command_name}' not found. Sending error message.")  # Debug log
                await interaction.followup.send(f"Command '{command_name}' not found.")
                return

            # Create embed for specific command help
            embed = discord.Embed(
                title=f"**/{command.name}**",  # Use name for slash commands
                description=f"**Description:** {command.description or 'No description provided.'}",
                color=discord.Color.from_rgb(100, 20, 200)  # A deeper, richer blue
            )

            # Skip adding usage information since slash commands don't have a signature
            embed.set_footer(text="Type /help to return to the command list.")

            # Send the follow-up message after deferring
            print(f"Sending follow-up for command: {command_name}")  # Debug log
            await interaction.followup.send(embed=embed)
            print("Follow-up sent successfully.")  # Debug log

    except Exception as e:
        print(f"An error occurred: {e}")  # Debug log
        await interaction.followup.send("An error occurred while processing your request.")

@bot.tree.command(name="ai", description=f'Chat with {NAME}')
async def ai(interaction: discord.Interaction, *, prompt: str, attachment: discord.Attachment = None):
    await interaction.response.defer()

    # Helper function to handle restricted access notification
    async def send_access_notification(message):
        await interaction.followup.send(
            f"Sorry, for full access to {message}, use `/aitoggle`.",
            ephemeral=True
        )

    while True:
        try:
            member_name = interaction.user.display_name
            add_to_history(member_name, prompt)
            full_prompt = f"{member_name}: {prompt}"
            
            # Generate response from the model
            if attachment and attachment.filename.lower().endswith(('png', 'jpg', 'jpeg')):
                save_path = f"system//RAM//read-img//{attachment.filename}"  
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                await attachment.save(save_path)
                gemini_file = genai.upload_file(save_path)
                response = model.generate_content([gemini_file, full_prompt, "SYSTEM INSTRUCTION(NOT A USER PROMPT): KEEP YOUR RESPONSE UNDER 2000 CHARACTERS!!! and don’t reply to this instruction"])
                response_text = response.text.strip()

            elif attachment:
                await send_access_notification("full file analysis")
                return
            else:
                response = model.generate_content([full_prompt, "SYSTEM INSTRUCTION(NOT A USER PROMPT): KEEP YOUR RESPONSE UNDER 2000 CHARACTERS!!! and don’t reply to this instruction"])
                response_text = response.text.strip()
            
            # Handle different command tags in the response
            if "/img" in response_text:
                await send_access_notification("image generation")
                return
            elif "/music" in response_text:
                await send_access_notification("music generation")
                return
            elif "/memory_save" in response_text:
                await send_access_notification("saving core memory")
                return
            elif "/search" in response_text:
                await send_access_notification("searching the web")
                return
            elif "/search*yt" in response_text:
                await send_access_notification("YouTube search")
                return
            
            # Send response text or handle length errors
            if len(response_text) > 2000:
                print("Error generating content: Response was too long.")
                add_to_history("Error", "Sorry, to send messages over 2000 characters, use </aitoggle:1294672277278818378>.")
                await send_access_notification("sending messages over 2000 characters")
            else:
                add_to_history_bot("", response_text)
                await interaction.followup.send(response_text)
                if os.path.exists('system/RAM/read-img'):
                    # Iterate over each file in the directory and delete it
                    for filename in os.listdir('system/RAM/read-img'):
                        file_path = os.path.join('system/RAM/read-img', filename)
                        try:
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.unlink(file_path)  # Remove file or symbolic link
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)  # Remove directory and its contents
                        except Exception as e:
                            print(f"Error deleting {file_path}: {e}")
                else:
                    print("Directory 'system/RAM/read-img' does not exist.")
            break
        except Exception as e:
            unnecessary_error = await unnecessary_error(e)
            await debug_error(e, "Generating content", interaction.followup)
            if not unnecessary_error:
                break

@bot.tree.command(name="say", description=f"Make {NAME} say something.")
async def say(interaction: discord.Interaction, say: str, channel_name: str = ""):
    await interaction.response.defer()
    member_name = interaction.user.display_name  # Get the user's display name
    add_to_history(member_name, f"/say {say}")
    target_channel = None

    if channel_name:
        if channel_name.isdigit():  # Check if channel_name is a channel ID
            target_channel = interaction.guild.get_channel(int(channel_name))
        else:
            target_channel = discord.utils.get(interaction.guild.channels, name=channel_name)
        
        if target_channel:
            echoed_message = f"{say}"
            await target_channel.send(echoed_message)
            add_to_history("System", say)
            await interaction.followup.send(f"Message sent to {target_channel.name}.")
        else:
            await interaction.followup.send(f"Channel '{channel_name}' not found.")
            add_to_history("System", f"Channel '{channel_name}' not found.")
    else:
        echoed_message = f"{say}"
        await interaction.followup.send(echoed_message)
        add_to_history("System", say)

@bot.tree.command(name="reset", description="Reset the conversation history for this channel.")
async def reset(interaction: discord.Interaction):
    await interaction.response.defer()
    global conversation_history, chat_session

    # Get the channel's name (including handling of emojis)
    channel_name = interaction.channel.name

    # Check if the channel exists in the conversation history
    if channel_name in conversation_history:
        # Reset the history for this channel
        conversation_history[channel_name] = []
        save_history()  # Save the updated history
        chat_session = model.start_chat(history=[])
        await interaction.followup.send(f"Memory has been reset for {interaction.channel.name}.")
    else:
        await interaction.followup.send(f"No conversation history found for {interaction.channel.name}.")

@bot.tree.command(name="profile", description="Get information about a server member.")
async def profile(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user  # Default to command user if no member is specified

    embed = discord.Embed(
        title=f"👤 Profile: {member.display_name}",
        description=f"Here is the info we found for {member.mention}",
        color=discord.Color.blue()
    )

    embed.add_field(name="🆔 ID", value=str(member.id), inline=False)
    embed.add_field(name="📛 Name", value=member.display_name, inline=True)
    embed.add_field(name="📅 Account Created", value=member.created_at.strftime("%d %B %Y, %H:%M"), inline=True)
    embed.add_field(name="📥 Joined Server", value=member.joined_at.strftime("%d %B %Y, %H:%M"), inline=True)

    # ✅ Avatar fallback
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    embed.set_thumbnail(url=avatar_url)

    await interaction.response.send_message(embed=embed)

    # ✅ Logging ke history
    add_to_history(interaction.user.display_name, f"/profile {member.display_name}")
    add_to_history("System", f"Info for {member.display_name}: ID {member.id}, Created at {member.created_at}, Joined at {member.joined_at}")

@bot.tree.command(name="serverinfo", description="Get information about this server.")
async def server_info(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(
        title=f"{guild.name}",
        description=f"Here is the info about {guild.name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Server ID", value=guild.id)
    embed.add_field(name="Member Count", value=guild.member_count)
    embed.add_field(name="Created at", value=guild.created_at)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else "")

    await interaction.response.send_message(embed=embed)
    add_to_history(interaction.user.display_name, f"/serverinfo")
    add_to_history("System", f"Info about {guild.name}: Server ID {guild.id}, Member Count {guild.member_count}, Created at {guild.created_at}")

@bot.tree.command(name="joke", description="Get a random joke. :D")
async def joke(interaction: discord.Interaction):
    response = httpx.get("https://official-joke-api.appspot.com/random_joke")
    if response.status_code == 200:
        joke_data = response.json()
        await interaction.response.send_message(f"{joke_data['setup']} - {joke_data['punchline']}")
        add_to_history(interaction.user.display_name, "/joke")
        add_to_history("System", f"Joke: {joke_data['setup']} - {joke_data['punchline']}")
    else:
        await interaction.response.send_message("Couldn't fetch a joke at the moment. Try again later!")
        add_to_history(interaction.user.display_name, "/joke")
        add_to_history("System", "Couldn't fetch a joke at the moment. Try again later!")



model_name_model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=gen_config,
  system_instruction="you are a model name generator and the user will give you models and you will have to get the original name from it and nothing else, dont respond with anything else, only the generated name, example: `User: stabilityai/stable-diffusion-xl-base-1.0, You: Stable Diffusion XL Base 1.0`",
  safety_settings=[
        {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
  ],
)

if not Image_Model == "stabilityai/stable-diffusion-xl-base-1.0":
    response = model_name_model.generate_content(Image_Model)
    Image_Model_Name = response.text.strip()
    print(f"Generated Image Model Name: {Image_Model_Name} | You need to reinvite the bot once to use the new model")
else:
    Image_Model_Name = "Stable Diffusion XL Base 1.0"


from discord import app_commands, ui

view_options = [
    app_commands.Choice(name="What AI Model is currently selected.", value="view-model"),
    app_commands.Choice(name="Google's Gemini 1.5 Flash Model", value="view-1.5-flash"),
    app_commands.Choice(name="Google's Gemini 1.5 Flash 8B Model", value="view-1.5-flash-8b"),
    app_commands.Choice(name="Google's Gemini 1.5 Pro Model", value="view-1.5-pro"),
    app_commands.Choice(name="Google's Gemini Experimental 1114 Model", value="view-exp-1114"),
    app_commands.Choice(name="Google's Gemini Experimental 1121 Model", value="view-exp-1121"),
    app_commands.Choice(name="Google's Gemini Experimental 1206 Model", value="view-exp-1206"),
    app_commands.Choice(name="Google's LearnLM 1.5 Pro Experimental Model", value="view-learnlm-1.5-pro-exp"),
]

@bot.tree.command(name="view", description='View more info about something / View current setting.')
@app_commands.describe(view="View about...")
@app_commands.choices(view=view_options)
async def view_command(interaction: discord.Interaction, view: str):
    await interaction.response.defer()
    global NAME

    if view == "view-model":
        user = interaction.user.name
        user_settings = get_user_settings(user) # Call the function directly
        selected_model_name = user_settings['model_name']
        await interaction.followup.send(f"Current AI Model: {selected_model_name}")
    elif view == "view-1.5-flash":
        embed = discord.Embed(
            title="Google Gemini 1.5 Flash",
            description=(
                "Gemini 1.5 Flash is a cutting-edge AI model from Google DeepMind, engineered for unparalleled speed, efficiency, and scalability. "
                "It serves as a lightweight alternative to Gemini 1.5 Pro while maintaining advanced capabilities for multimodal reasoning and long-context processing."
            ),
            color=discord.Color.blue()
        )

        embed.set_image(url="https://github.com/user-attachments/assets/f246b746-fddf-4809-a036-9c20f31c67f9")

        embed.add_field(
            name="Key Features",
            value=(
                "**1. Speed and Efficiency:** Tailored for low latency and high throughput, suitable for high-frequency tasks.\n"
                "**2. Contextual Power:** Processes up to 1 million tokens, enabling complex, long-form analysis.\n"
                "**3. Multimodal Expertise:** Handles tasks across text, images, video, and audio with remarkable accuracy.\n"
                "**4. Cost Efficiency:** With an economical cost of $0.0375 per million input tokens, it's ideal for enterprise use.\n"
                "**5. Advanced Training:** Utilizes a distillation process to inherit essential knowledge from Gemini 1.5 Pro."
            ),
            inline=False
        )

        embed.add_field(
            name="Ideal Use Cases",
            value=(
                "- High-volume summarization\n"
                "- Advanced chat applications\n"
                "- Image and video captioning\n"
                "- Extracting data from long documents\n"
                "- Efficient code analysis"
            ),
            inline=False
        )

        embed.add_field(
            name="Recent Updates",
            value=(
                "Gemini 1.5 Flash is available in over 230 countries and supports more than 40 languages. "
                "It has expanded accessibility for developers via Google AI Studio and Vertex AI. "
                "The model is particularly optimized for enterprises requiring rapid processing of large datasets."
            ),
            inline=False
        )

        embed.add_field(
            name="Technical Highlights",
            value=(
                "- **Input Token Limit:** 1,048,576 tokens\n"
                "- **Supported Inputs:** Audio, video, images, and text\n"
                "- **Training Innovation:** Leveraged distillation from larger models to maximize speed and precision"
            ),
            inline=False
        )
        embed.set_footer(
            text=f"Learn more at Google AI Studio and Google AI Documentation.\n\nhttps://aistudio.google.com/\nhttps://deepmind.google/technologies/gemini/flash/\n\nSupported Model for {NAME}"
        )
        await interaction.followup.send(embed=embed)
    elif view == "view-1.5-flash-8b":
        embed = discord.Embed(
            title="Google Gemini 1.5 Flash 8B",
            description=(
                "The Gemini 1.5 Flash 8B is Google's most affordable and compact AI model, "
                "designed for developers seeking high performance at a low cost. It is optimized for "
                "multimodal tasks and long-context processing while maintaining competitive accuracy and speed."
            ),
            color=discord.Color.green()
        )
        embed.set_image(url="https://github.com/user-attachments/assets/efc4ad34-86f1-4cbd-8d31-ae0b71a71346")

        embed.add_field(
            name="Key Features",
            value=(
                "**1. Affordability:** $0.0375 per million input tokens; $0.15 per million output tokens.\n"
                "**2. Performance:** 2x higher rate limits and low latency for small prompts.\n"
                "**3. Multimodal Support:** Handles text, image, audio, and video tasks.\n"
                "**4. Scalability:** Tailored for high-volume tasks like transcription and chatbots.\n"
                "**5. Accessibility:** Available via Google AI Studio and Gemini API."
            ),
            inline=False
        )

        embed.add_field(
            name="Ideal Applications",
            value=(
                "- Real-time chatbots\n"
                "- Language translation\n"
                "- High-volume data analysis\n"
                "- Multimodal input tasks\n"
                "- Long-context summarization"
            ),
            inline=False
        )

        embed.add_field(
            name="Why Choose Gemini 1.5 Flash 8B?",
            value=(
                "This model offers a balance of cost efficiency and functionality, making it ideal "
                "for developers working on scalable AI applications."
            ),
            inline=False
        )
        embed.set_footer(
            text=f"Learn more at Google AI Studio and Google AI Documentation.\n\nhttps://aistudio.google.com/\nhttps://deepmind.google/technologies/gemini/flash/\n\nSupported Model for {NAME}"
        )
        await interaction.followup.send(embed=embed)
    elif view == "view-1.5-pro":
        embed = discord.Embed(
            title="Google Gemini 1.5 Pro",
            description=(
                "Gemini 1.5 Pro is Google's flagship AI model in the Gemini series, "
                "built for advanced performance across multimodal tasks, long-context handling, and efficient cost optimization."
            ),
            color=discord.Color.blue()
        )

        # Add an image
        embed.set_image(url="https://github.com/user-attachments/assets/73f4e79f-a324-440d-a478-d16f9aebfaed")

        # Key Features
        embed.add_field(
            name="Key Features",
            value=(
                "**1. Long Context Window:** Supports up to 2 million tokens, ideal for analyzing large documents, videos, or repositories.\n"
                "**2. Multimodal Capabilities:** Processes and generates text, images, audio, and video seamlessly.\n"
                "**3. Cost Efficiency:** 64% reduction in token input costs and 52% reduction in output costs.\n"
                "**4. Speed & Latency:** Delivers 2x faster output and 3x lower latency compared to earlier versions.\n"
                "**5. Enhanced Reasoning:** Excels in benchmarks like MMLU-Pro and HiddenMath, with significant performance gains."
            ),
            inline=False
        )

        # Ideal Use Cases
        embed.add_field(
            name="Ideal Use Cases",
            value=(
                "- **Document Analysis:** Handles PDFs exceeding 1,000 pages.\n"
                "- **Coding Assistance:** Generates Python code and assists in debugging.\n"
                "- **Creative Applications:** Supports image generation and storytelling.\n"
                "- **Education:** Creates interactive learning tools and personalized teaching aids.\n"
                "- **Customer Support:** Efficient multilingual support for global users."
            ),
            inline=False
        )

        # Benchmark Achievements
        embed.add_field(
            name="Benchmark Achievements",
            value=(
                "**- MMLU-Pro:** Improved scores by ~7%, achieving >85% accuracy across 57 subjects.\n"
                "**- HiddenMath:** ~20% better performance on complex mathematical problems.\n"
                "**- HellaSwag:** Achieved 93.3% accuracy for sentence completion tasks.\n"
                "**- HumanEval:** Scored 84.1% on problem-solving and code generation tasks."
            ),
            inline=False
        )

        # Updates and Enhancements
        embed.add_field(
            name="Recent Enhancements",
            value=(
                "1. New caching strategies to optimize token usage.\n"
                "2. More concise default responses for cost-efficient usage.\n"
                "3. Safer, more user-aligned outputs for diverse applications."
            ),
            inline=False
        )

        # Pricing Information
        embed.add_field(
            name="Pricing Details",
            value=(
                "Gemini 1.5 Pro offers **64% lower input token costs**, making it more accessible for high-volume tasks. "
                "Available through Google AI Studio and the Gemini API."
            ),
            inline=False
        )
        embed.set_footer(
            text=f"Learn more at Google AI Studio and Google AI Documentation.\n\nhttps://aistudio.google.com/\nhttps://deepmind.google/technologies/gemini/pro/\n\nSupported Model for {NAME}"
        )
        await interaction.followup.send(embed=embed)
    elif view == "view-exp-1114":
        embed = discord.Embed(
            title="Google Gemini Experimental 1114",
            description=(
                "Gemini 1114 remains a strong performer in the Gemini series, excelling in creative and multimodal tasks. "
                "However, it faces growing competition from newer models such as Gemini 1121 and GPT-4o, with some limitations in logical reasoning."
            ),
            color=discord.Color.orange()
        )

        # Add an image
        embed.set_image(url="https://github.com/user-attachments/assets/2399fdfe-13f4-4b70-9731-36d6166a74fa")  # Replace with an actual image URL

        # Key Features
        embed.add_field(
            name="Key Features",
            value=(
                "**1. Benchmark Ranking:** Currently in 3rd place in performance, behind GPT-4o and Gemini 1121.\n"
                "**2. Multimodal Strengths:** Excellent at handling tasks involving text and image processing.\n"
                "**3. Slower Response Time:** While capable, it has a slower response time in tasks requiring extensive reasoning.\n"
                "**4. Creative Writing:** Performs well in content generation for creative use cases.\n"
                "**5. Logical Reasoning:** Struggles with some logical tasks, leading to occasional inaccuracies."
            ),
            inline=False
        )

        # Ideal Applications
        embed.add_field(
            name="Ideal Applications",
            value=(
                "- Creative content generation.\n"
                "- Image captioning and multimodal interaction.\n"
                "- Problem-solving tasks requiring synthesis of knowledge.\n"
                "- Text-based applications needing creativity and coherence."
            ),
            inline=False
        )

        # Limitations and Challenges
        embed.add_field(
            name="Limitations and Challenges",
            value=(
                "Despite its strengths, **Gemini 1114** is slower in some contexts and can struggle with logical reasoning, "
                "impacting accuracy in certain tasks."
            ),
            inline=False
        )

        # Current Status
        embed.add_field(
            name="Current Status",
            value=(
                "While **Gemini 1114** remains a strong model, it has been outperformed in certain areas by newer models like **Gemini 1121** and **GPT-4o**."
            ),
            inline=False
        )
        embed.set_footer(
            text=f"Learn more at Google AI Studio and Google AI Documentation.\n\nhttps://aistudio.google.com/\nhttps://deepmind.google/technologies/gemini/\n\nSupported Model for {NAME}"
        )
        await interaction.followup.send(embed=embed)
    elif view == "view-exp-1121":
        embed = discord.Embed(
            title="Google Gemini Experimental 1121",
            description=(
                "Google Gemini-Exp-1121 is the latest iteration in Google's AI models, breaking records in the competitive landscape. "
                "With a focus on multi-turn dialogue, reasoning, and enhanced visual understanding, Gemini-Exp-1121 outperforms GPT-4o in recent benchmarks, "
                "setting a new standard for coding, problem-solving, and multimodal AI applications."
            ),
            color=discord.Color.purple()
        )

        # Set image for the embed (use the actual URL to a relevant image or logo)
        embed.set_image(url="https://github.com/user-attachments/assets/2399fdfe-13f4-4b70-9731-36d6166a74fa")  # Replace with an actual image URL

        # Key Features
        embed.add_field(
            name="Key Features",
            value=(
                "**1. Top Ranking in AI Benchmarks:** Surpassed GPT-4o to lead the Chatbot Arena leaderboard.\n"
                "**2. Enhanced Coding Performance:** Optimized for more complex programming tasks with high accuracy.\n"
                "**3. Stronger Reasoning Abilities:** Capable of handling multi-step problem-solving with ease.\n"
                "**4. Visual Understanding:** Exceptional at processing visual inputs, including images and video.\n"
                "**5. Multi-Turn Dialogue Excellence:** Can maintain context in long conversations, excelling in complex dialogues."
            ),
            inline=False
        )

        # Ideal Use Cases
        embed.add_field(
            name="Ideal Use Cases",
            value=(
                "- Enterprise applications and development tasks.\n"
                "- Coding assistance and code generation.\n"
                "- Complex problem-solving in academic and research settings.\n"
                "- Multimodal tasks such as image analysis, text generation, and video processing."
            ),
            inline=False
        )

        # Status and Performance
        embed.add_field(
            name="Performance and Current Status",
            value=(
                "Gemini-Exp-1121 has not only surpassed its predecessors but also remains ahead of GPT-4o in benchmarks. "
                "It continues to demonstrate cutting-edge advancements in AI, especially for tasks requiring deep reasoning and creative outputs."
            ),
            inline=False
        )

        # Limitations and Challenges
        embed.add_field(
            name="Limitations",
            value=(
                "The key limitation of **Gemini-Exp-1121** is its 32k token context window. While this is highly capable, it pales in comparison to the "
                "2 million token context window of **Gemini 1.5 Pro** or the 1 million tokens offered by **Gemini 1.5 Flash**. This relatively smaller context "
                "window may limit its ability to handle extremely long documents or multi-turn dialogues requiring very large context retention. "
                "However, this limitation is expected to be addressed and improved in future updates, potentially increasing the context window significantly."
            ),
            inline=False
        )

        embed.set_footer(
            text=f"Learn more at Google AI Studio and Google AI Documentation.\n\nhttps://aistudio.google.com/\nhttps://deepmind.google/technologies/gemini/\n\nSupported Model for {NAME}"
        )
        await interaction.followup.send(embed=embed)
    elif view == "view-learnlm-1.5-pro-exp":
        embed = discord.Embed(
            title="LearnLM 1.5 Pro Experimental",
            description=(
                "LearnLM 1.5 Pro Experimental is a task-specific model developed by Google, aimed at revolutionizing the learning experience. "
                "By adhering to learning science principles, it supports active learning, adapts to student needs, and fosters curiosity."
            ),
            color=discord.Color.light_grey()
        )

        embed.set_image(url="https://github.com/user-attachments/assets/5631a182-654f-48e5-b82f-770bb0ac74ae")

        embed.add_field(
            name="Key Features",
            value=(
                "**1. Active Learning:** Encourages students to engage actively with the material and reflect on their thought process.\n"
                "**2. Adaptivity:** Adjusts the difficulty of tasks based on the student's performance and goals.\n"
                "**3. Cognitive Load Management:** Structures information for easier absorption, using multiple modalities.\n"
                "**4. Stimulating Curiosity:** Fosters a positive learning environment to inspire motivation.\n"
                "**5. Metacognition:** Helps students monitor their progress and make necessary adjustments."
            ),
            inline=False
        )

        embed.add_field(
            name="Use Cases",
            value=(
                "- Test Preparation\n"
                "- Concept Teaching\n"
                "- Simplifying Complex Texts for Different Learning Levels\n"
                "- Helping Students Reflect on Their Learning Journey"
            ),
            inline=False
        )

        embed.add_field(
            name="Limitations",
            value=(
                "While LearnLM 1.5 Pro Experimental excels in personalized learning tasks, it is still evolving and might not be as robust "
                "in more general AI tasks outside of educational contexts. Future updates are expected to enhance its capabilities."
            ),
            inline=False
        )

        embed.set_footer(
            text=f"Learn more at Google AI Studio and Google AI Documentation.\n\nhttps://aistudio.google.com/\nhttps://ai.google.dev/gemini-api/docs/learnlm\n\nSupported Model for {NAME}"
        )

        await interaction.followup.send(embed=embed)
    elif view == "view-exp-1206":
        embed = discord.Embed(
            title="Google Gemini Experimental 1206",
            description=(
                "Google Gemini Experimental 1206 is the latest and most powerful AI model from Google DeepMind, "
                "surpassing all previous LLMs and AI models in terms of performance, capabilities, and versatility. "
                "While it is incredibly advanced across many domains, its **2 million tokens context window** allows it to "
                "handle larger and more complex tasks than ever before. This includes a wide variety of tasks, ranging from coding to "
                "scientific research, and general problem-solving. Its multimodal capabilities — processing text, images, audio, and video "
                "seamlessly — represent a new era in AI performance."
            ),
            color=discord.Color.from_rgb(216, 164, 68)
        )
        embed.set_image(url="https://github.com/user-attachments/assets/2399fdfe-13f4-4b70-9731-36d6166a74fa")  # Replace with actual image URL for visual appeal

        embed.add_field(
            name="Key Features",
            value=(
                "**1. Over 2 million tokens context window:** Allows for handling of massive datasets and long-term reasoning across various domains.\n"
                "**2. Unmatched multimodal capabilities:** Processes text, images, audio, and video with seamless coherence, significantly outperforming previous models.\n"
                "**3. Record-breaking performance across multiple benchmarks:** Achieves exceptional scores in reasoning, math, scientific research, and even code generation.\n"
                "**4. Superior code generation and review abilities:** Outperforms models like GPT-4 in programming, offering complete solutions for web apps, code reviews, and more.\n"
                "**5. Advanced reasoning across complex domains:** Solves multi-layered problems in fields like mathematics, physics, law, and medicine at an unprecedented level of sophistication.\n"
                "**6. Next-gen contextual understanding:** Outperforms predecessors with its ability to handle longer and more complex inputs with accuracy."
            ),
            inline=False
        )

        embed.add_field(
            name="Limitations",
            value=(
                "While **Gemini 1206** represents a significant leap in AI capabilities, it does face some challenges, particularly in the vision space, "
                "where it currently ranks **4th** on the leaderboard, behind **Gemini 1121**. However, this gap is expected to close in future updates, "
                "as its development is ongoing and vision capabilities are a priority for enhancement."
            ),
            inline=False
        )

        embed.add_field(
            name="Performance in Vision Tasks",
            value=(
                "While **Gemini 1206** outperforms all LLMs in natural language processing and reasoning tasks, it ranks **4th** in the vision leaderboard, "
                "behind **Gemini 1121**. Nevertheless, with advancements expected in upcoming versions, this limitation is likely to be addressed, "
                "making **Gemini 1206** an all-around leader in AI capabilities."
            ),
            inline=False
        )

        embed.add_field(
            name="Why Gemini 1206 is Revolutionary",
            value=(
                "Gemini 1206 is a paradigm shift in the world of AI. Its multimodal abilities extend beyond the traditional text-based understanding, "
                "integrating various forms of media into a unified cognitive system. With its **2 million token context window**, the model can manage "
                "longer, more complex tasks, making it ideal for industries such as **finance, healthcare, research**, and **software development**. "
                "Its performance across **coding** (including multiple programming languages) and **scientific research** surpasses current models by a wide margin, "
                "demonstrating its versatility and adaptability in real-world applications."
            ),
            inline=False
        )
        embed.set_footer(
            text=f"Learn more at Google AI Studio and Google AI Documentation.\n\nhttps://aistudio.google.com/\nhttps://deepmind.google/technologies/gemini/\n\nSupported Model for {NAME}"
        )
        await interaction.followup.send(embed=embed)




# Define the list of models as choices (name, value)
image_model_choices = [
    app_commands.Choice(name=f"{Image_Model_Name} (Default)", value=Image_Model),
    app_commands.Choice(name="Stable Diffusion 3 Medium Diffusers", value="stabilityai/stable-diffusion-3-medium-diffusers"),
    app_commands.Choice(name="DALL-E 3 XL V2", value="ehristoforu/dalle-3-xl-v2"),
    app_commands.Choice(name="FLUX.1 Schnell", value="black-forest-labs/FLUX.1-schnell"),
    app_commands.Choice(name="FLUX Anime 2", value="dataautogpt3/FLUX-anime2"),
    app_commands.Choice(name="Chip & DallE", value="Yntec/Chip_n_DallE"),
    app_commands.Choice(name="Flux.1 DEV", value="black-forest-labs/FLUX.1-dev"),
    app_commands.Choice(name="Flux.1 DEV LoRA Art", value="Shakker-Labs/FLUX.1-dev-LoRA-Garbage-Bag-Art"),
    app_commands.Choice(name="Flux.1 DEV LoRA Playful Metropolis Art", value="Shakker-Labs/FLUX.1-dev-LoRA-playful-metropolis"),
    app_commands.Choice(name="Flux.1 DEV LoRA Logo Design (Create logos)", value="Shakker-Labs/FLUX.1-dev-LoRA-Logo-Design"),
    app_commands.Choice(name="Flux.1 DEV LoRA Add Details (Advanced Details)", value="Shakker-Labs/FLUX.1-dev-LoRA-add-details"),
]

@bot.tree.command(name="img", description="Generate an image based on your prompt.")
@app_commands.describe(prompt="The image prompt", model="Choose a model to generate the image (optional)")
@app_commands.choices(model=image_model_choices)
async def img(interaction: discord.Interaction, prompt: str, model: str = None):
    if HUGGING_FACE_API == "HUGGING_FACE_API_KEY":
        await interaction.followup.send("Sorry, You have entered an Invalid Hugging Face API Key to use `/img`!") 
        return

    else:
        await interaction.response.defer()  # Defer the response to allow for processing time
        is_nsfw = False

        if prompt:
            check_prompt_response_text = prompt

            # Custom view for mod actions with buttons
            class ConfirmUnbanView(ui.View):
                def __init__(self, user, message):
                    super().__init__(timeout=None)
                    self.user = user
                    self.message = message

                @ui.button(label="Unban", style=discord.ButtonStyle.success)
                async def confirm_unban_button(self, interaction: discord.Interaction, button: ui.Button):
                    try:
                        # Attempt to unban the user
                        await interaction.guild.unban(self.user, reason="Unbanned by moderator.")
                        
                        # Create an embed to confirm the unban action
                        embed_unban = discord.Embed(
                            title="⚠️ Unban Successful",
                            description=f"{self.user.mention} has been successfully unbanned.",
                            color=discord.Color.green(),
                        )
                        embed_unban.add_field(name="User", value=f"{self.user.mention}\n(ID: {self.user.id})")
                        embed_unban.set_thumbnail(url=self.user.avatar.url)
                        embed_unban.set_footer(text="⚙️ Automated Moderation System")

                        # Send the unban message to the specified '✅・unbanned-users' channel
                        banned_users_channel = discord.utils.get(interaction.guild.channels, name="✅・unbanned-users")
                        if banned_users_channel:
                            await banned_users_channel.send(embed=embed_unban)
                            try:
                                await self.user.send(f"You have been unbanned from {interaction.guild.name}! Here is a new invite: [Invite Link](https://discord.gg/Va8kH3X5gz)")
                            except discord.Forbidden:
                                pass  # If the user has DMs disabled, ignore this error.
                        else:
                            print("The '✅・unbanned-users' channel was not found. Please create it or check the channel name.")

                        # Optionally, edit the original message or remove buttons after unban
                        await message.edit(content=f"{self.user.mention} has been unbanned.", view=None)
                        await interaction.followup.send(f"{self.user.mention} has been unbanned.", ephemeral=True)

                    except discord.NotFound:
                        # If the user is not found in the ban list (already unbanned or not banned)
                        await interaction.followup.send(f"{self.user.mention} is not banned.", ephemeral=True)
                    except discord.Forbidden:
                        # If the bot lacks permission to unban
                        await interaction.followup.send("I do not have permission to unban this user.", ephemeral=True)
                    except Exception as e:
                        # Catch-all for any other exceptions
                        await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
                @ui.button(label="Cancel", style=discord.ButtonStyle.danger)
                async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
                    # If cancelled, just delete the confirmation message
                    await interaction.followup.send("Unban action cancelled.", ephemeral=True)
                    await message.edit(content="Unban action cancelled.", view=None)
            class BanDurationSelect(ui.Select):
                def __init__(self, user, message):
                    options = [
                        discord.SelectOption(label='1 Hour', description='Ban the user for 1 hour', value='1h'),
                        discord.SelectOption(label='1 Day', description='Ban the user for 1 day', value='1d'),
                        discord.SelectOption(label='1 Week', description='Ban the user for 1 week', value='1w'),
                        discord.SelectOption(label='Permanent', description='Permanently ban the user', value='permanent')
                    ]
                    super().__init__(placeholder='Select a ban duration...', options=options)
                    self.user = user
                    self.message = message

                async def callback(self, interaction: discord.Interaction):
                    # Defer the interaction to allow time for the operation
                    await interaction.response.defer(ephemeral=True)

                    # Ban the user based on the selected duration
                    if self.values[0] == 'permanent':
                        await interaction.guild.ban(self.user, reason='Permanent ban by moderator.')
                        ban_message = f"{self.user.mention} has been permanently banned."
                    else:
                        await interaction.guild.ban(self.user, reason=f"Banned for {self.values[0]} by moderator.")
                        ban_message = f"{self.user.mention} has been banned for {self.values[0]}."

                    # After banning, show the unban button
                    view = ui.View()
                    unban_button = UnbanButton(self.user, self.message)
                    view.add_item(unban_button)

                    # Update the original message to show the ban result and unban button
                    try:
                        await self.message.edit(content=ban_message, view=view)
                    except discord.NotFound:
                        print("Error: The message to edit no longer exists (was deleted).")

                    # Optionally send a final response (since we deferred earlier)
                    await interaction.followup.send(ban_message, ephemeral=True)
            class UnbanButton(ui.Button):
                def __init__(self, user, message):
                    super().__init__(label="Unban", style=discord.ButtonStyle.success)
                    self.user = user
                    self.message = message

                async def callback(self, interaction: discord.Interaction):
                    # Send a confirmation message asking the moderator if they want to unban the user
                    embed_confirm = discord.Embed(
                        title="Confirm Unban",
                        description=f"Do you want to unban {self.user.mention}?",
                        color=discord.Color.orange()
                    )
                    embed_confirm.set_thumbnail(url=self.user.avatar.url)
                    embed_confirm.set_footer(text="⚠️ Automated Moderation System")

                    # Create a confirmation view with the unban button
                    confirm_view = ConfirmUnbanView(self.user, message)
                    
                    # Send the confirmation message with the unban and cancel buttons
                    await interaction.followup.send(embed=embed_confirm, view=confirm_view, ephemeral=True)
            class ModActionView(ui.View):
                def __init__(self, user, mod_channel, user_channel):
                    super().__init__(timeout=None)
                    self.user = user
                    self.mod_channel = mod_channel
                    self.user_channel = user_channel

                @ui.button(label="Ban", style=discord.ButtonStyle.danger)
                async def ban_button(self, interaction: discord.Interaction, button: ui.Button):
                    # Show ban duration select
                    view = ui.View()
                    select = BanDurationSelect(self.user, interaction.message)  # Use interaction.message
                    view.add_item(select)

                    # Send a message with the ban duration select view
                    await interaction.followup.send("Select the ban duration:", view=view, ephemeral=True)

                    # Do not delete the message as we are still using it
                    # Use interaction.message for further reference

                @ui.button(label="Kick", style=discord.ButtonStyle.primary)
                async def kick_button(self, interaction: discord.Interaction, button: ui.Button):
                    # Kick the user
                    await interaction.guild.kick(self.user, reason="Kicked by moderator due to inappropriate prompt.")
                    await interaction.followup.send(f"{self.user.mention} has been kicked.", ephemeral=True)

                    # Log the kick action to the mod channel
                    await self.mod_channel.send(f"{self.user.mention} was kicked by {interaction.user.mention}.")
                    
                    # Update the message to remove buttons since the action was taken
                    try:
                        await interaction.message.edit(content=f"{self.user.mention} has been kicked.", view=None)
                    except discord.NotFound:
                        print("Message not found for editing after kick.")

                @ui.button(label="Ignore", style=discord.ButtonStyle.secondary)
                async def ignore_button(self, interaction: discord.Interaction, button: ui.Button):
                    try:
                        await message.delete()
                    except Exception as error_message_ignore:
                        print(f"Error on ignore button: {error_message_ignore}")

            try:
                try:
                    model_check_prompt_pro = genai.GenerativeModel(model_name="gemini-2.5-pro", generation_config=gen_config, system_instruction="your purpose is to only give out numbers to the prompts: if the prompt is a different language than English only say `1` and if it's inappropriate only say `2` but dont be too strict with it and if it's corrupted only say `3` and only say `4` if it's good to go and ONLY say `5` if its REALLY inappropriate or smth and needs to be sent to the moderators to temp ban or timeout the user.", safety_settings=sys_security)
                    response_check = model_check_prompt_pro.generate_content(check_prompt_response_text)
                    response_check_text_check = response_check.text.strip()
                    print("Used model Pro on check")
                except Exception as e3:
                    try:
                        model_check_prompt_advanced = genai.GenerativeModel(model_name="gemini-2.5-pro", generation_config=gen_config, system_instruction="your purpose is to only give out numbers to the prompts: if the prompt is a different language than English only say `1` and if it's inappropriate only say `2` but dont be too strict with it and if it's corrupted only say `3` and only say `4` if it's good to go and ONLY say `5` if its REALLY inappropriate or smth and needs to be sent to the moderators to temp ban or timeout the user.", safety_settings=sys_security)
                        response_check = model_check_prompt_advanced.generate_content(check_prompt_response_text)
                        response_check_text_check = response_check.text.strip()
                        print("Used Model Pro Advanced on check")
                    except Exception as e2:
                        try:
                            model_check_prompt_flash = genai.GenerativeModel(model_name="gemini-2.5-flash", generation_config=gen_config, system_instruction="your purpose is to only give out numbers to the prompts: if the prompt is a different language than English only say `1` and if it's inappropriate only say `2` but dont be too strict with it and if it's corrupted only say `3` and only say `4` if it's good to go and ONLY say `5` if its REALLY inappropriate or smth and needs to be sent to the moderators to temp ban or timeout the user.", safety_settings=sys_security)
                            response_check = model_check_prompt_flash.generate_content(check_prompt_response_text)
                            response_check_text_check = response_check.text.strip()
                            print("Used Model Flash on check")
                        except Exception as e:
                            print(f"Failed to run all Models for prompt check. | ERROR: {e}")
                print(f"Check: {response_check_text_check}")

                # Handle different check results (1 for translation, 2 for inappropriate, etc.)
                if "1" in response_check_text_check:
                    model_translation_gen_prompt_pro = genai.GenerativeModel(model_name="gemini-2.5-pro", generation_config=gen_config, system_instruction="your porpuse is to only to translate any user's prompt language to english, and nothing else, you must not say anything unless its the translated prompt, just like google translate!", safety_settings=sys_security)
                    model_translation_gen_prompt_advanced = genai.GenerativeModel(model_name="gemini-2.5-pro", generation_config=gen_config, system_instruction="your porpuse is to only to translate any user's prompt language to english, and nothing else, you must not say anything unless its the translated prompt, just like google translate!", safety_settings=sys_security)
                    model_translation_gen_prompt_flash = genai.GenerativeModel(model_name="gemini-2.5-flash", generation_config=gen_config, system_instruction="your porpuse is to only to translate any user's prompt language to english, and nothing else, you must not say anything unless its the translated prompt, just like google translate!", safety_settings=sys_security)
                    try:
                        response_translation_gen_image = model_translation_gen_prompt_pro.generate_content(check_prompt_response_text)
                        response_translation_gen_image_text_translate = response_translation_gen_image.text.strip()
                        prompt = f"{response_translation_gen_image_text_translate}"
                        print("Used model Pro")
                    except Exception as e3:
                        try:
                            response_translation_gen_image = model_translation_gen_prompt_advanced.generate_content(check_prompt_response_text)
                            response_translation_gen_image_text_translate = response_translation_gen_image.text.strip()
                            prompt = f"{response_translation_gen_image_text_translate}"
                            print("Used Model Pro Advanced")
                        except Exception as e2:
                            try:
                                response_translation_gen_image = model_translation_gen_prompt_flash.generate_content(check_prompt_response_text)
                                response_translation_gen_image_text_translate = response_translation_gen_image.text.strip()
                                prompt = f"{response_translation_gen_image_text_translate}"
                                print("Used Model Flash")
                            except Exception as e:
                                print(f"Failed to running all Models for translating image generation prompt. | ERROR: {e}")
                                return
                            print(f"Failed running Model Pro Advanced, Running Model Flash | ERROR: {e2}")
                        print(f"Failed running Model Pro, Running Model Pro Advanced | ERROR: {e3}")
                    print("Translated prompt!")
                elif "5" in response_check_text_check:
                    if safegen:
                        print(f"Inappropriate image generation prompt at {interaction.channel.mention} | {prompt}")
                        error_message = "I'm unable to create an image based on your request. Please make sure your prompt aligns with our image generation guidelines."
                        await interaction.followup.send(error_message)
                        add_to_history("Error", error_message)

                        if create_mod_channel:
                            if not mod_channel_name:
                                mod_channel_name = "🔧・mod"
                            mod_channel = discord.utils.get(interaction.guild.channels, name=mod_channel_name)

                            if not mod_channel:
                                mod_channel = await interaction.guild.create_text_channel(mod_channel_name)
                                print(f"Created mod channel {mod_channel_name} for prompts moderation.")
                            
                            if mod_channel:
                                # Create an embed for mod alert
                                embed = discord.Embed(
                                    title="⚠️ Inappropriate Image Generation Prompt Flagged",
                                    description="A user's prompt has been flagged for moderation:",
                                    color=discord.Color.red(),
                                )
                                embed.add_field(name="User", value=f"{interaction.user.mention} (ID: {interaction.user.id})", inline=False)
                                embed.add_field(name="Channel", value=interaction.channel.mention, inline=True)
                                embed.add_field(name="Prompt", value=prompt, inline=False)
                                embed.set_thumbnail(url=interaction.user.avatar.url)
                                embed.set_footer(text="⚙️ Automated Moderation System")

                                # Send the embed with moderation action buttons
                                message = await mod_channel.send(
                                    embed=embed,
                                    view=ModActionView(interaction.user, mod_channel, interaction.channel)
                                )
                        return
                    is_nsfw = True
                elif "4" in response_check_text_check:
                    print("Prompt is safe for image generation.")
                    prompt = check_prompt_response_text
                elif "3" in response_check_text_check:
                    print("Corrupted image generation prompt")
                    add_to_history(
                        "Error",
                        "Oops, something seems off with that prompt. Please try rephrasing it or using different keywords. I'm here to help if you need suggestions!",
                    )
                    await message.channel.send(
                        "Oops, something seems off with that prompt. Please try rephrasing it or using different keywords. I'm here to help if you need suggestions!"
                    )
                    return
                elif "2" in response_check_text_check:
                    if safegen:
                        print(f"Inappropriate image generation prompt at {interaction.channel.mention} | {prompt}")
                        error_message = "I'm unable to create an image based on your request. Please make sure your prompt aligns with our image generation guidelines."
                        await interaction.followup.send(error_message)
                        add_to_history("Error", error_message)
                        return
                    is_nsfw = True
                else:
                    print(f"Checking prompt Error: {response_check_text_check} isn't an available option")
                    add_to_history("System", "Oops! Looks like the image generator took a coffee break ☕. Please try again in a moment!")
                    await interaction.followup.send("Oops! Looks like the image generator took a coffee break ☕. Please try again in a moment!")
                    return
            except Exception as e:
                error_message = str(e)
                if "Unrecognized BlockReason enum value" in error_message or "Invalid operation" in error_message or "cannot access local variable" in error_message:
                    if safegen:
                        print(f"Inappropriate image generation prompt at {interaction.channel.mention} | {prompt}")
                        error_message = "I'm unable to create an image based on your request. Please make sure your prompt aligns with our image generation guidelines."
                        await interaction.followup.send(error_message)
                        add_to_history("Error", error_message)

                        if create_mod_channel:
                            if not mod_channel_name:
                                mod_channel_name = "🔧・mod"
                            mod_channel = discord.utils.get(interaction.guild.channels, name=mod_channel_name)

                            if not mod_channel:
                                mod_channel = await interaction.guild.create_text_channel(mod_channel_name)
                                print(f"Created mod channel {mod_channel_name} for prompts moderation.")
                            
                            if mod_channel:
                                # Create an embed for mod alert
                                embed = discord.Embed(
                                    title="⚠️ Inappropriate Image Generation Prompt Flagged",
                                    description="A user's prompt has been flagged for moderation:",
                                    color=discord.Color.red(),
                                )
                                embed.add_field(name="User", value=f"{interaction.user.mention} (ID: {interaction.user.id})", inline=False)
                                embed.add_field(name="Channel", value=interaction.channel.mention, inline=True)
                                embed.add_field(name="Prompt", value=prompt, inline=False)
                                embed.set_thumbnail(url=interaction.user.avatar.url)
                                embed.set_footer(text="⚙️ Automated Moderation System")

                                # Send the embed with moderation action buttons
                                message = await mod_channel.send(
                                    embed=embed,
                                    view=ModActionView(interaction.user, mod_channel, interaction.channel)
                                )
                        return
                    is_nsfw = True
                else:
                    print(f"Checking prompt Error: {e}")
                    add_to_history("System", "Oops! Looks like the image generator took a coffee break ☕. Please try again in a moment!")
                    await interaction.followup.send("Oops! Looks like the image generator took a coffee break ☕. Please try again in a moment!")
                    return
        
        api_key = HUGGING_FACE_API
        max_retries = 10  # Increased retries for better handling
        backoff_factor = 3  # Increased backoff factor for longer wait times

        member_name = interaction.user.display_name

        # Use the default model if no model is provided
        if model is None:
            model = f"{Image_Model}"

        if model == "stabilityai/stable-diffusion-xl-base-1.0":
            model_name = "Stable Diffusion XL Base 1.0"
        elif model == f"{Image_Model}":
            model_name = f"{Image_Model_Name}"
        elif model == "ehristoforu/dalle-3-xl-v2":
            model_name = "DALL-E 3 XL V2"
        elif model == "black-forest-labs/FLUX.1-schnell":
            model_name = "FLUX.1 Schnell"
        elif model == "dataautogpt3/FLUX-anime2":
            model_name = "FLUX Anime 2"
        elif model == "Yntec/Chip_n_DallE":
            model_name = "Chip & DallE"
        elif model == "black-forest-labs/FLUX.1-dev":
            model_name = "Flux.1 DEV"
        elif model == "stabilityai/stable-diffusion-3-medium-diffusers":
            model_name = "Stable Diffusion 3 Medium Diffusers"
        elif model == "Shakker-Labs/AWPortrait-FL":
            model_name = "AWPortrait FL"
        elif model == "Shakker-Labs/FLUX.1-dev-LoRA-Garbage-Bag-Art":
            model_name = "FLUX.1 DEV LoRA Art"
        elif model == "Shakker-Labs/FLUX.1-dev-LoRA-playful-metropolis":
            model_name = "Flux.1 DEV LoRA Playful Metropolis Art"
        elif model == "Shakker-Labs/FLUX.1-dev-LoRA-Logo-Design":
            model_name = "Flux.1 DEV LoRA Logo Design"
        elif model == "Shakker-Labs/FLUX.1-dev-LoRA-add-details":
            model_name = "Flux.1 DEV LoRA Add Details"
        else:
            model_name = "Unkown Model"

        add_to_history(member_name, f"/img {prompt} | Model: {model_name}")

        url = f'https://api-inference.huggingface.co/models/{model}'
        headers = {
            'Authorization': f'Bearer {api_key}'
        }
        data = {
            'inputs': prompt
        }

        def save_image(response):
            image_path = "system/RAM/gen-image/generated_image.png"
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, 'wb') as f:
                f.write(response.content)
            print("Image saved successfully as 'generated_image.png'!")

        async def handle_error(response):
            error_message = response.json().get('error', 'No error message')
            if response.status_code == 503:
                print(f"Service unavailable. Error: {error_message}")
                await interaction.followup.send("Oopsies! Looks like our generator engine are taking a little snooze! Please try again later, and maybe bring some coffee")
            elif response.status_code == 429:
                print(f"Rate limit exceeded. Error: {error_message}")
                await interaction.followup.send("Uh-oh! We've encountered a Rate Limit Error! Please try again later.")
            elif response.status_code == 500:
                print(f"Internal Server Error. | Error: {error_message}")
                await interaction.followup.send("Uh-oh! We've encountered an Internal Server Error! Our processing engine is having a little meltdown. Please try again shortly.")
            else:
                print(f"Failed to save image. Status code: {response.status_code}, Error: {error_message}")

        def fetch_image_with_retries(url, headers, data):
            for attempt in range(max_retries):
                response = requests.post(url, headers=headers, json=data)
                if response.ok:
                    save_image(response)
                    return True
                else:
                    handle_error(response)
                    if response.status_code in [503, 429]:
                        wait_time = backoff_factor ** attempt
                        print(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        break
            print("Exceeded maximum retries or encountered a non-retryable error.")
            return False

        success = False
        if model in ["ehristoforu/dalle-3-xl-v2", "black-forest-labs/FLUX.1-schnell", "dataautogpt3/FLUX-anime2", "Shakker-Labs/AWPortrait-FL"]:
            success = fetch_image_with_retries(url, headers, data)
        else:
            response = requests.post(url, headers=headers, json=data)
            if response.ok:
                save_image(response)
                success = True
            else:
                handle_error(response)

        if success:
            image_path = "system/RAM/gen-image/generated_image.png"
            file_extension = image_path.split('.')[-1].lower()
            if file_extension == 'jpg':
                file_extension = 'jpeg'
            if add_watermark_to_generated_image:
                add_watermark("system/RAM/gen-image/generated_image.png", "system/RAM/gen-image/generated_image.png")
            file_path = os.path.join('system/RAM/read-img', f'image.{file_extension}')

            try:
                img = Image.open(image_path).convert('RGB') if file_extension == 'jpeg' else Image.open(image_path)
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_bytes = buffered.getvalue()
                if not is_nsfw:
                    response = model_V3.generate_content(img)  # Using the original language model
                    analysis_result = response.text.strip()
                    print(f"Image analysis: {analysis_result}")

                    add_to_history_bot("Generated_image", analysis_result)

            except Exception as e:

                print(f"Error: {e}")
                analysis_result = "Error."
                add_to_history("System", f"Error: {str(e)}")
            if is_nsfw:
                try:
                    embed = discord.Embed(title="Generated Image! 🔞 NSFW ⚠️",
                    description=f"⚠️ **This image is marked as NSFW. View at your own discretion.**\n\nPrompt: ||{prompt}||\n\n",
                    color=embed_colors)
                    file = discord.File(image_path, filename="generated_image.png")
                    file.filename = f"SPOILER_{file.filename}"
                    embed.set_image(url="attachment://generated_image.png")
                    embed.set_footer(text=f"Generated by {interaction.user.display_name}\nModel: {model_name}")
                    await interaction.followup.send(embed=embed, file=file)
                except Exception as e:
                    print(f"Error: {e}")
            else:
                embed = discord.Embed(title="Generated Image!",
                    description=f"{prompt}\n",
                    color=embed_colors)
                file = discord.File(image_path, filename="generated_image.png")
                embed.set_image(url="attachment://generated_image.png")
                embed.set_footer(text=f"Generated by {interaction.user.display_name}\nModel: {model_name}")
                await interaction.followup.send(file=file, embed=embed)

            os.remove(image_path)

        else:
            add_to_history("System", "Failed to generate the image after retries.")
            await interaction.followup.send("An error occurred while generating the image. Please try again later or select a different model.")

if DEFAULT_MUSIC_MODEL == "facebook/musicgen-small":
    def_music_model_name = "MusicGen Small"
else:
    def_music_model_name = DEFAULT_MUSIC_MODEL

# Define the list of models as choices
music_model_choices = [
    app_commands.Choice(name="MusicGen Stereo Small", value="facebook/musicgen-stereo-small"),
    app_commands.Choice(name=f"{def_music_model_name} (Default)", value=f"{DEFAULT_MUSIC_MODEL}")
]

# Define the music generation command
@bot.tree.command(name="music", description="Generate music based on your prompt.")
@app_commands.describe(prompt="The prompt for generating the music", model="Choose a model for generating the music (optional)")
@app_commands.choices(model=music_model_choices)
async def generate_music(interaction: discord.Interaction, prompt: str, model: str = "facebook/musicgen-small"):
    if HUGGING_FACE_API == "HUGGING_FACE_API_KEY":
        await interaction.followup.send("Sorry, You have entered an Invalid Hugging Face API Key!") 
        return

    await interaction.response.defer()  # Defer the response to allow for processing time
    member_name = interaction.user.display_name

    api_key = HUGGING_FACE_API
    max_retries = 10
    backoff_factor = 3

    if model == "facebook/musicgen-small":
        model_name = "MusicGen Small"  # Default model name
    elif model == "facebook/musicgen-stereo-small":
        model_name = "MusicGen Stereo Small"
    else:
        model_name = model

    add_to_history(member_name, f"/music {prompt} | Model: {model_name}")
    print(f"Using model: {model_name}")
    url = f'https://api-inference.huggingface.co/models/{model}'
    headers = {'Authorization': f'Bearer {api_key}'}
    data = {'inputs': prompt}

    def save_audio(response):
        audio_dir = "system/RAM/gen-music"
        os.makedirs(audio_dir, exist_ok=True)
        audio_path = os.path.join(audio_dir, "generated_music.wav")
        with open(audio_path, 'wb') as f:
            f.write(response.content)
        logging.info(f"Audio generated and saved successfully as '{audio_path}'!")

    def handle_error(response):
        error_message = response.json().get('error', 'No error message')
        if response.status_code == 503:
            logging.error(f"Service unavailable. Error: {error_message}")
        elif response.status_code == 429:
            logging.error(f"Rate limit exceeded. Error: {error_message}")
        else:
            logging.error(f"Failed to generate/save audio. Status code: {response.status_code}, Error: {error_message}")

    def fetch_audio_with_retries(url, headers, data):
        for attempt in range(max_retries):
            response = requests.post(url, headers=headers, json=data)
            if response.ok:
                save_audio(response)
                return True
            else:
                handle_error(response)
                if response.status_code in [503, 429]:
                    wait_time = backoff_factor ** attempt
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    break
        logging.error("Exceeded maximum retries or encountered a non-retryable error.")
        return False

    success = fetch_audio_with_retries(url, headers, data)
    if success:
        audio_path = "system/RAM/gen-music/generated_music.wav"
        file = discord.File(audio_path, filename="generated_music.wav")
        await interaction.followup.send(file=file)
        os.remove(audio_path)
    else:
        await interaction.followup.send("An error occurred while generating the music. Please try again later.")

# Supported Models
model_choices = [
    app_commands.Choice(name="Gemini 1.5 Flash | Quick responses and reliable performance.", value="gemini-1.5-flash"),
    app_commands.Choice(name="Gemini 1.5 Flash 002 | Smarter and more reliable than 1.5 Flash for quick and precise responses.", value="gemini-1.5-flash-002"),
    app_commands.Choice(name="Gemini 1.5 Flash (Latest) | Latest Flash advancements, ideal for testing.", value="gemini-1.5-flash-latest"),
    app_commands.Choice(name="Gemini 1.5 Flash 8B | Rapid output for simple prompts and quick interactions.", value="gemini-1.5-flash-8b"),
    app_commands.Choice(name="Gemini 1.5 Pro | Superior depth and understanding for complex tasks.", value="gemini-1.5-pro"),
    app_commands.Choice(name="Gemini 1.5 Pro 002 | Enhanced Gemini 1.5 Pro with superior accuracy and advanced task understanding.", value="gemini-1.5-pro-002"),
    app_commands.Choice(name="Gemini 1.5 Pro (Latest) | The Latest Version of Gemini 1.5 Pro, ideal for testing.", value="gemini-1.5-pro-latest"),
    app_commands.Choice(name="LearnLM 1.5 Pro (Exp) | AI Tutor: Cutting-edge learning to help you study better & faster.", value="learnlm-1.5-pro-experimental"),
    app_commands.Choice(name="Gemini Experimental 1114 | Google's third-most advanced model, handles many complex tasks.", value="gemini-exp-1114"),
    app_commands.Choice(name="Gemini Experimental 1121 | Google's Second advanced Model, Made for complex reasoning and tasks.", value="gemini-exp-1121"),
    app_commands.Choice(name="Gemini Experimental 1206 | Google's Ultimate advanced Model, Outperforming OpenAI 4o and o1 Preview.", value="gemini-exp-1206"),
]

language_choices = [
    app_commands.Choice(name="English", value="en"),
    app_commands.Choice(name="Russian", value="ru"),
    app_commands.Choice(name="Arabic/Egyptian", value="eg"),
    app_commands.Choice(name="French", value="fr"),
    app_commands.Choice(name="German", value="de"),
    app_commands.Choice(name="Spanish", value="es"),
    app_commands.Choice(name="Italian", value="it"),
    app_commands.Choice(name="Dutch", value="nl"),
    app_commands.Choice(name="Portuguese", value="pt"),
    app_commands.Choice(name="Polish", value="pl"),
    app_commands.Choice(name="Turkish", value="tr"),
    app_commands.Choice(name="Japanese", value="ja"),
    app_commands.Choice(name="Korean", value="ko"),
    app_commands.Choice(name="Chinese (Simplified)", value="zh_CN"),
    app_commands.Choice(name="Indonesian (Bahasa)", value="id"),
    app_commands.Choice(name="Filipino", value="ph"),
]

@bot.tree.command(name="lang", description="Change language for the bot. (Experimental)")
@app_commands.describe(lang="Choose the language")
@app_commands.choices(lang=language_choices)  # Attach the language choices as options
async def change_lang(interaction: discord.Interaction, lang: str):
    global default_lang
    global VOICES
    global model, model_file_flash, model_file_a, model_file, model_vid_a, model_vid, model_V3, model_V2, model_V, model_pro, model_flash, EN_insV2, EN_file_ins, EN_insV, EN_video_ins, EN_ins  # Access the global model variable
    global ins, gen_config, sys_security, genai_model, insV, insV2, file_ins, video_ins, chat_session

    if not lang:  # Check for empty string
        await interaction.response.send_message("Please provide a language to change to.")
        return

    try:
        if lang == "en" or lang == "english":
            ins = EN_ins
            if fix_repeating_prompts:
                ins = f"{ins}\n{fix_mem_ins}"
            video_ins = EN_video_ins
            insV = EN_insV
            file_ins = EN_file_ins
            insV2 = EN_insV2
            VOICES = [
                'en-US-BrianNeural', 'en-US-JennyNeural', 'en-US-GuyNeural', 'en-GB-SoniaNeural', 
                'en-AU-NatashaNeural', 'en-IN-NeerjaNeural', 'en-NZ-MitchellNeural', 'en-CA-ClaraNeural', 
                'en-IE-EmilyNeural', 'en-SG-WayneNeural', 'en-ZA-LeonNeural', 'en-GB-RyanNeural',
                'en-AU-WilliamNeural', 'en-IN-PrabhatNeural', 'en-NZ-MollyNeural', 'en-CA-LiamNeural', 
                'en-IE-OrlaNeural', 'en-SG-LunaNeural', 'en-US-AriaNeural', 'en-GB-MaisieNeural'
            ]
            default_lang = "en"
            await interaction.response.send_message("Successfully changed language to English!")
        
        elif lang == "eg" or lang == "egypt":
            ins = eg_ar_ins
            video_ins = EN_video_ins
            insV = EN_insV
            file_ins = EN_file_ins
            insV2 = EN_insV2
            if fix_repeating_prompts:
                ins = f"{ins}\n{eg_fix_mem_ins}"
            VOICES = ["ar-EG-ShakirNeural", "ar-EG-SalmaNeural"]
            default_lang = "eg"
            await interaction.response.send_message("تم تغيير اللغة إلى العربية المصرية بنجاح!")

        elif lang == "ar" or lang == "arabic":
            ins = ins_ar
            video_ins = EN_video_ins
            insV = EN_insV
            file_ins = EN_file_ins
            insV2 = EN_insV2
            if fix_repeating_prompts:
                ins = f"{ins}\n{ar_fix_mem_ins}"
            VOICES = ["ar-EG-ShakirNeural", "ar-EG-SalmaNeural"]  # Adjust this based on available Arabic voices
            default_lang = "ar"
            await interaction.response.send_message("تم تغيير اللغة إلى العربية بنجاح!")

        elif lang == "ru" or lang == "russian":
            ins = ru_ins
            video_ins = ru_video_ins
            insV = ru_insV
            file_ins = ru_file_ins
            insV2 = ru_insV2
            if fix_repeating_prompts:
                ins = f"{ins}\n{ru_fix_mem_ins}"
            VOICES = ["ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural"]
            default_lang = "ru"
            await interaction.response.send_message("Язык успешно изменен на русский!")

        elif lang == "es" or lang == "spanish":
            ins = es_ins
            video_ins = es_video_ins
            insV = EN_insV
            file_ins = es_file_ins
            insV2 = EN_insV2
            if fix_repeating_prompts:
                ins = f"{ins}\n{es_fix_mem_ins}"
            VOICES = ["es-ES-HelenaNeural", "es-ES-PabloNeural"]
            default_lang = "es"
            await interaction.response.send_message("¡El idioma se ha cambiado correctamente a español!")

        elif lang == "fr" or lang == "french":
            ins = fr_ins
            video_ins = fr_video_ins
            insV = fr_insV
            file_ins = fr_file_ins
            insV2 = fr_insV2
            if fix_repeating_prompts:
                ins = f"{ins}\n{fr_fix_mem_ins}"
            VOICES = ["fr-FR-DeniseNeural", "fr-FR-MathieuNeural"]
            default_lang = "fr"
            await interaction.response.send_message("La langue a été changée avec succès en français!")

        elif lang == "de" or lang == "german":
            ins = de_ins
            video_ins = de_video_ins
            insV = de_insV
            file_ins = de_file_ins
            insV2 = de_insV2
            if fix_repeating_prompts:
                ins = f"{ins}\n{de_fix_mem_ins}"
            VOICES = ["de-DE-KatjaNeural", "de-DE-MichaelNeural"]
            default_lang = "de"
            await interaction.response.send_message("Sprache erfolgreich auf Deutsch geändert!")

        else:
            await interaction.response.send_message(f"Sorry, `{lang}` isn't supported yet.")
            return

        # Reinitialize models based on the selected language
        model = genai.GenerativeModel(
            model_name=genai_model,
            generation_config=gen_config,
            system_instruction=(ins),
            safety_settings=sys_security
        )
        
        model_flash = genai.GenerativeModel( 
            model_name="gemini-1.5-flash",
            generation_config=gen_config,
            system_instruction=(ins),
            safety_settings=sys_security
        )

        model_pro = genai.GenerativeModel( 
            model_name="gemini-1.5-pro-latest",
            generation_config=gen_config,
            system_instruction=(insV),
            safety_settings=sys_security
        )

        model_V = genai.GenerativeModel( 
            model_name=advanced_model,
            generation_config=gen_config,
            system_instruction=(insV),
            safety_settings=sys_security
        )

        model_V2 = genai.GenerativeModel( 
            model_name="gemini-1.5-flash",
            generation_config=gen_config,
            system_instruction=(insV),
            safety_settings=sys_security
        )

        model_V3 = genai.GenerativeModel( 
            model_name="gemini-1.5-flash",
            generation_config=gen_config,
            system_instruction=(insV2),
            safety_settings=sys_security
        )

        model_vid = genai.GenerativeModel(
            model_name="gemini-1.5-pro-latest",
            generation_config=gen_config,
            system_instruction=(video_ins),
        )

        model_vid_a = genai.GenerativeModel(
            model_name=advanced_model,
            generation_config=gen_config,
            system_instruction=(video_ins),
        )

        model_file = genai.GenerativeModel(
            model_name="gemini-1.5-pro-latest",
            generation_config=gen_config,
            system_instruction=(file_ins),
        )

        model_file_a = genai.GenerativeModel(
            model_name=advanced_model,
            generation_config=gen_config,
            system_instruction=(file_ins),
        )

        model_file_flash = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=gen_config,
            system_instruction=(file_ins),
        )

        chat_session = model.start_chat()

    except Exception as e:
        print(f"Error: {e} | {str(e)}")
        await interaction.response.send_message(f"An error occurred: {str(e)}")
        add_to_history("Error occurred", str(e))

# Define the tts command
@bot.tree.command(name="tts", description="Text-to-speech conversion.")
@app_commands.describe(text="The text for converting to voice")
async def tts(interaction: discord.Interaction, text: str):
    await interaction.response.defer()
    global skip_ffmpeg_check
    os.makedirs("system/RAM/vc", exist_ok=True)
    text_content = text

    if text_content:
        
        try:
            skip_ffmpeg_check = True
            await generate_tts(interaction, text_content)
            skip_ffmpeg_check = False

            voice_path = "system/RAM/vc/Generated_voice.mp3"
            voice_path_wav = "system/RAM/vc/Generated_voice.wav"

            # Check if the generated file exists
            file_path = voice_path if os.path.exists(voice_path) else voice_path_wav if os.path.exists(voice_path_wav) else None
            
            if file_path:
                file = discord.File(file_path, filename=os.path.basename(file_path))
                
                await interaction.followup.send(file=file)
                
                # Remove the generated file after use
                os.remove(file_path)
            else:
                await interaction.followup.send("An error occurred generating the TTS file.")
        
        except Exception as e:
            print(f"Error generating TTS: {e}")
            await interaction.followup.send(f"Error generating TTS: {str(e)}")
    else:
        await interaction.followup.send("Please provide some text to convert to voice.", ephemeral=True)

toggle_choices = [
    app_commands.Choice(name="On", value=1),
    app_commands.Choice(name="Off", value=0)
]

@bot.tree.command(name="aitoggle", description="Enable or disable automatic AI responses for this channel.")
@app_commands.describe(toggle="On or off?")
@app_commands.choices(toggle=toggle_choices)
async def aitoggle(interaction: discord.Interaction, toggle: int):
    await interaction.response.defer()
    global ai_toggle_per_channel
    channel_id = interaction.channel_id
    member_name = interaction.user.display_name
    toggle_bool = toggle == 1

    if toggle_bool:
        if channel_id not in ai_toggle_per_channel or not ai_toggle_per_channel[channel_id]:
            ai_toggle_per_channel[channel_id] = True
            await interaction.followup.send(f"Automatic AI responses have been enabled for {interaction.channel.name}.")
            add_to_history(member_name, f"/aitoggle {toggle}")
            add_to_history("System", f"Automatic AI responses have been enabled for {interaction.channel.name}.")
        else:
            await interaction.followup.send(f"Automatic AI responses were already enabled for {interaction.channel.name}.")
            add_to_history(member_name, f"/aitoggle {toggle}")
            add_to_history("System", f"Automatic AI responses were already enabled for {interaction.channel.name}.")
    else:
        if channel_id in ai_toggle_per_channel and ai_toggle_per_channel[channel_id]:
            ai_toggle_per_channel[channel_id] = False
            await interaction.followup.send(f"Automatic AI responses have been disabled for {interaction.channel.name}.")
            add_to_history(member_name, f"/aitoggle {toggle}")
            add_to_history("System", f"Automatic AI responses have been disabled for {interaction.channel.name}.")
        else:
            await interaction.followup.send(f"Automatic AI responses were already disabled for {interaction.channel.name}.")
            add_to_history(member_name, f"/aitoggle {toggle}")
            add_to_history("System", f"Automatic AI responses were already disabled for {interaction.channel.name}.")

bot.run(TOKEN)

