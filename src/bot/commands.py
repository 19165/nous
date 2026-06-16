import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
from src.agents.graph import stream_research_workflow
from .utils import ProgressManager

logger = logging.getLogger(__name__)

class ResearchCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="research", description="Start a research task on a specific topic")
    @app_commands.describe(topic="The topic you want to research")
    async def research(self, interaction: discord.Interaction, topic: str):
        """
        Handles the /research command with real-time streaming updates.
        """
        logger.info(f"Research command received for topic: {topic}")
        
        # 1. Acknowledge immediately to prevent "Unknown Interaction"
        await interaction.response.defer(thinking=True)
        
        last_message = ""
        final_result = None

        try:
            # 2. Start the streaming workflow
            async for state in stream_research_workflow(topic):
                # Update final_result with the latest state
                final_result = state
                
                # 3. Format progress message
                progress_msg = ProgressManager.format_progress_message(state)
                
                # 4. Only update Discord if the message has changed
                if progress_msg != last_message:
                    await interaction.edit_original_response(content=progress_msg)
                    last_message = progress_msg
                
                # Optional: slight delay to avoid overwhelming Discord API
                await asyncio.sleep(0.5)

            # 5. Extract summary and send final response
            if final_result and "summary" in final_result:
                summary = final_result["summary"]
                
                # If summary is very long, send it in parts
                if len(summary) > 2000:
                    parts = [summary[i:i+1900] for i in range(0, len(summary), 1900)]
                    # First part edits the original message
                    await interaction.edit_original_response(content=parts[0])
                    # Subsequent parts are sent as followups
                    for part in parts[1:]:
                        await interaction.followup.send(part)
                else:
                    await interaction.edit_original_response(content=summary)
            else:
                await interaction.edit_original_response(content="❌ Research completed but no summary was generated.")
            
        except Exception as e:
            logger.error(f"Error in research command: {e}")
            error_msg = f"❌ An error occurred while researching **{topic}**."
            try:
                await interaction.edit_original_response(content=error_msg)
            except:
                await interaction.followup.send(error_msg)

async def setup(bot: commands.Bot):
    await bot.add_cog(ResearchCommands(bot))
