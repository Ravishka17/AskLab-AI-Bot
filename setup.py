#!/usr/bin/env python3
"""Setup script for asklab_ai_bot package."""
from setuptools import setup, find_packages

setup(
    name="asklab-ai-bot",
    version="1.0.0",
    description="A Python Discord bot that replies using Groq's LLM API",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "discord.py>=2.0.0",
        "groq>=0.4.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "asklab-ai-bot=asklab_ai_bot.__main__:main",
        ],
    },
)
