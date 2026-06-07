import discord
from discord import app_commands
from discord.ext import commands
import logging
from src.agents.graph import run_research_workflow

logger = logging.getLogger(__name__)

class ResearchCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="research", description="Start a research task on a specific topic")
    @app_commands.describe(topic="The topic you want to research")
    async def research(self, interaction: discord.Interaction, topic: str):
        """
        Handles the /research command.
        """
        logger.info(f"Research command received for topic: {topic}")
        
        # Acknowledge the request immediately (3-second timeout rule)
        await interaction.response.defer(thinking=True)
        
        try:
            # Inform user that research has started
            await interaction.followup.send(f"🔍 I've started researching **{topic}**. This might take a moment...")
            
            # Invoke LangGraph workflow
            result = await run_research_workflow(topic)
            
            # Extract summary from state
            summary = result.get("summary", "No summary generated.")
            
            # Send the final result
            # We use followup.send again. Note: 2000 character limit applies.
            if len(summary) > 2000:
                # Basic splitting if needed, but the writer should aim for conciseness
                parts = [summary[i:i+1900] for i in range(0, len(summary), 1900)]
                for part in parts:
                    await interaction.followup.send(part)
            else:
                await interaction.followup.send(summary)
            
        except Exception as e:
            logger.error(f"Error in research command: {e}")
            await interaction.followup.send(f"❌ An error occurred while researching **{topic}**.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ResearchCommands(bot))
