from __future__ import annotations

import logging

from .bot import AskLabBot
from .config import get_settings


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    settings = get_settings()
    bot = AskLabBot(settings=settings)
    bot.run(settings.discord_bot_token)


if __name__ == "__main__":
    main()
