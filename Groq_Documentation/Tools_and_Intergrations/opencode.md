---
description: Connect OpenCode&#x27;s open-source AI coding agent to Groq for fast inference in terminal, desktop, or IDE.
title: OpenCode + Groq - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# OpenCode + Groq

[OpenCode](https://opencode.ai/) is an open-source AI coding agent available as a terminal-based interface, desktop app, or IDE extension. Pair it with Groq's LPU inference to get low-latency code generation with native Groq provider support.

## [Prerequisites](#prerequisites)

* Groq account with an API key from [console.groq.com/keys](https://console.groq.com/keys)
* OpenCode installed locally — see the [OpenCode Installation Guide](https://opencode.ai/docs/) for installation instructions

## [Setup](#setup)

1. **Configure Groq Provider** Navigate to your project directory and launch OpenCode:  
curl  
```  
cd /path/to/your/project  
opencode  
```  
Inside the OpenCode TUI, run `/connect`, search for **Groq** and select it, then enter your Groq API key when prompted. Next, run `/models` and choose a Groq model from the list.  
Your API key will be stored securely in `~/.local/share/opencode/auth.json`.
2. **Start Coding** OpenCode supports all models available through Groq's API. Use plan and build modes to review implementation strategies before making changes to your codebase.

## [Recommended Groq Models](#recommended-groq-models)

[moonshotai/kimi-k2-instruct-0905Most PopularMoonshot AI — Advanced reasoning with 256K context window](https://console.groq.com/docs/model/moonshotai/kimi-k2-instruct-0905)[openai/gpt-oss-120bOpenAI — Powerful open-source model for complex coding tasks](https://console.groq.com/docs/model/openai/gpt-oss-120b)

OpenCode works best with models that have strong reasoning capabilities and large context windows for understanding your codebase.

## [Learn More](#learn-more)

* [OpenCode Documentation](https://opencode.ai/docs/) — complete guide to using OpenCode
* [OpenCode Providers Guide](https://opencode.ai/docs/providers/#groq) — detailed Groq provider setup
* [Groq model catalog](https://console.groq.com/docs/models) — explore all available models
