from __future__ import annotations

import logging
from typing import Iterable

import discord
from discord.ext import commands

from .config import Settings
from .groq_chat import GroqChat, to_groq_messages
from .history import ChatMessage, HistoryStore

logger = logging.getLogger(__name__)


def _split_discord_message(content: str, *, limit: int = 1900) -> Iterable[str]:
    content = content.strip()
    if not content:
        return ["(empty response)"]

    chunks: list[str] = []
    while len(content) > limit:
        split_at = content.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(content[:split_at].rstrip())
        content = content[split_at:].lstrip("\n")
    chunks.append(content)
    return chunks


class AskLabBot(commands.Bot):
    def __init__(self, *, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
        )

        self.settings = settings
        self.groq = GroqChat(settings)
        self.history = HistoryStore(max_messages=settings.max_history_messages)

    async def setup_hook(self) -> None:
        self.add_command(self.ask)
        self.add_command(self.reset)
        self.add_command(self.ping)

    async def on_ready(self) -> None:
        logger.info("Logged in as %s (id=%s)", self.user, self.user and self.user.id)

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "Missing arguments. Try: `!ask <your question>`",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        logger.exception("Unhandled command error", exc_info=error)
        await ctx.send(
            "Sorry — something went wrong while handling that command.",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)

        if not self.user:
            return

        mention_prefixes = (self.user.mention, f"<@!{self.user.id}>")
        for prefix in mention_prefixes:
            if message.content.startswith(prefix):
                prompt = message.content[len(prefix) :].strip()
                if not prompt:
                    return
                await self._answer_in_channel(
                    channel=message.channel, author=message.author, prompt=prompt
                )
                return

    async def _answer_in_channel(
        self,
        *,
        channel: discord.abc.Messageable,
        author: discord.abc.User,
        prompt: str,
    ) -> None:
        key = getattr(channel, "id", 0) or 0

        self.history.append(key, ChatMessage(role="user", content=f"{author.display_name}: {prompt}"))
        history_messages = [
            {"role": m.role, "content": m.content} for m in self.history.get(key)
        ]

        groq_messages = to_groq_messages(self.settings.system_prompt, history_messages)

        try:
            async with channel.typing():
                response = await self.groq.complete(groq_messages)
        except Exception:
            logger.exception("Failed to generate response from Groq")
            await channel.send(
                "Sorry — I ran into an error while contacting Groq. Please try again in a moment."
            )
            return

        self.history.append(key, ChatMessage(role="assistant", content=response))

        for chunk in _split_discord_message(response):
            await channel.send(chunk, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(name="ask", help="Ask the AI a question. Usage: !ask <question>")
    async def ask(self, ctx: commands.Context, *, prompt: str) -> None:
        await self._answer_in_channel(channel=ctx.channel, author=ctx.author, prompt=prompt)

    @commands.command(name="reset", help="Reset the conversation memory for this channel.")
    async def reset(self, ctx: commands.Context) -> None:
        key = getattr(ctx.channel, "id", 0) or 0
        self.history.clear(key)
        await ctx.send(
            "Conversation memory cleared for this channel.",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command(name="ping", help="Health check.")
    async def ping(self, ctx: commands.Context) -> None:
        await ctx.send("pong")
