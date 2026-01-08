#!/usr/bin/env python3
"""
Discord UI components for AskLab AI Bot
"""
import discord
from config import AVAILABLE_MODELS, user_model_preferences

class ModelSelectView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.add_item(ModelDropdown(user_id))

class ModelDropdown(discord.ui.Select):
    def __init__(self, user_id):
        options = [
            discord.SelectOption(
                label="Llama 3.3 70B",
                description="Fast and versatile",
                value="llama-3.3-70b-versatile",
                emoji="🦙"
            ),
            discord.SelectOption(
                label="Kimi K2 Instruct",
                description="Precise reasoning",
                value="moonshotai/kimi-k2-instruct-0905",
                emoji="🌙"
            )
        ]
        super().__init__(
            placeholder="Choose AI model...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.user_id = user_id
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This menu is not for you!", ephemeral=True)
            return
        
        selected_model = self.values[0]
        user_model_preferences[self.user_id] = selected_model
        
        model_names = {v: k for k, v in AVAILABLE_MODELS.items()}
        model_display = model_names.get(selected_model, selected_model)
        
        await interaction.response.send_message(
            f"✅ Set model to **{model_display}**", 
            ephemeral=True
        )
        
        # Stop the view after selection
        self.view.stop()