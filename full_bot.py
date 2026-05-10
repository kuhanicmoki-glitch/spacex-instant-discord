import requests
import time
import os
import discord
from discord.ext import tasks
from datetime import datetime

# ================== CONFIG ==================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
YOUR_USER_ID = int(os.getenv("YOUR_USER_ID"))
CIK = "0001181412"
CHECK_INTERVAL = 45
# ===========================================

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

last_seen = None
headers = {"User-Agent": "SpaceX Bot (your.email@example.com)"}

@bot.event
async def on_ready():
    print(f"✅ Full Bot is online as {bot.user}")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"🚀 **SpaceX Full Bot is now online and monitoring!** <@{YOUR_USER_ID}>")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.lower() in ["!test", "!ping", "/test"]:
        await message.channel.send(f"🧪 **Test successful!** {message.author.mention} The bot is working perfectly.")

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_filings():
    global last_seen
    url = f"https://data.sec.gov/submissions/CIK{CIK}.json"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        recent = data.get('filings', {}).get('recent', {})
        
        for i in range(min(5, len(recent.get('accessionNumber', [])))):
            acc_no = recent['accessionNumber'][i]
            
            if last_seen is None:
                last_seen = acc_no
                return
                
            if acc_no == last_seen:
                break
                
            filing = {
                'accessionNumber': acc_no,
                'filingDate': recent['filingDate'][i],
                'form': recent['form'][i],
                'primaryDocument': recent['primaryDocument'][i]
            }
            
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                link = f"https://www.sec.gov/Archives/edgar/data/{CIK.lstrip('0')}/{acc_no.replace('-','')}/{filing['primaryDocument']}"
                await channel.send(
                    f"🚨 **SpaceX Filing Alert!** <@{YOUR_USER_ID}>\n"
                    f"**{filing['form']}** filed on {filing['filingDate']}\n"
                    f"🔗 {link}"
                )
                print(f"✅ Alert sent for {filing['form']}")
            
            last_seen = recent['accessionNumber'][0]
            break
    except Exception as e:
        print(f"Error checking filings: {e}")

bot.run(DISCORD_TOKEN)
