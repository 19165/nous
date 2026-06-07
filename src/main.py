import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

class ResearchBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True # Needed if we ever want to read messages directly
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # We will load extensions (commands) here
        logger.info("Setting up bot hooks...")
        try:
            await self.load_extension("bot.commands")
            logger.info("Successfully loaded extension: bot.commands")
        except Exception as e:
            logger.error(f"Failed to load extension bot.commands: {e}")
        
        # In a real scenario, you might want to sync here or via a command
        # await self.tree.sync()

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("------")

def main():
    if not TOKEN:
        logger.error("DISCORD_TOKEN not found in environment variables.")
        return

    bot = ResearchBot()
    
    @bot.command()
    @commands.is_owner()
    async def sync(ctx):
        """Syncs slash commands."""
        await bot.tree.sync()
        await ctx.send("Commands synced!")

    bot.run(TOKEN)

if __name__ == "__main__":
    main()
