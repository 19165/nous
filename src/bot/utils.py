from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ProgressManager:
    @staticmethod
    def format_progress_message(state: dict) -> str:
        """
        Translates the current AgentState into a user-friendly Discord message.
        """
        stage = state.get("progress_stage", "Initializing...")
        iteration = state.get("current_iteration", 1)
        max_iter = state.get("max_iterations", 3)
        status = state.get("workflow_status", "in_progress")
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Select emoji based on the stage
        emoji = "⏳"
        if "Planning" in stage:
            emoji = "📝"
        elif "Gathering" in stage:
            emoji = "🔍"
        elif "Reviewing" in stage:
            emoji = "⚖️"
        elif "Writing" in stage:
            emoji = "✍️"
        
        if status == "completed":
            return "✅ **Research Complete!** Synthesizing the final report..."
        
        if status == "failed":
            return "❌ **Research Failed.** Something went wrong during the process."

        return (
            f"> {emoji} **Current Stage:** {stage}\n"
            f"> 🔄 **Iteration:** {iteration}/{max_iter}\n"
            f"> ⏱️ *Last updated at: {timestamp}*"
        )
