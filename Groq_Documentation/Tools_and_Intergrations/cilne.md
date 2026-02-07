---
description: Connect Cline&#x27;s AI coding assistant to Groq for ultra-fast inference in VS Code, Cursor, JetBrains IDEs, or via CLI.
title: Cline + Groq - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Cline + Groq

[Cline](https://cline.bot/) is a powerful CLI tool and AI coding assistant available as an extension for VS Code, Cursor, JetBrains, and VSCodium, and Windsurf IDEs. Pair it with Groq's LPU inference to get ultra-fast response times for interactive development workflows with native Groq provider support.

## [Prerequisites](#prerequisites)

* Groq account with an API key from [console.groq.com/keys](https://console.groq.com/keys)
* Cline installation:  
   * **IDE Extension:** Follow the [Cline Installation Guide](https://docs.cline.bot/getting-started/installing-cline) for VS Code, Cursor, JetBrains IDEs, VSCodium, or Windsurf  
   * **CLI:** Follow the [Cline CLI Installation](https://docs.cline.bot/cline-cli/installation) guide (requires Node.js version 20 or higher, Node.js 22 recommended)

## [Setup](#setup)

1. **Configure Groq Provider** **IDE Extension:**  
   * Open Cline settings (click the settings icon ⚙️ in the Cline panel, or use Command Palette → "Cline: Open Settings")  
   * Select **"Groq"** from the "API Provider" dropdown  
   * Paste your Groq API key into the "Groq API Key" field  
   * Choose your desired model from the "Model" dropdown  
**CLI:**  
   * During the `cline auth` authentication wizard, select Groq as your provider and enter your Groq API key  
   * Alternatively, configure Groq in your Cline settings after installation  
Your API key is stored securely in your editor's settings or CLI configuration.
2. **Start Coding** **IDE Extension:** Open the Cline panel and start chatting or use code generation features. Groq's ultra-fast inference will provide near-instant responses. **CLI:** Run `cline` for interactive mode or `cline "your task"` for single command execution.

## [Recommended Groq Models](#recommended-groq-models)

[moonshotai/kimi-k2-instruct-0905Most PopularMoonshot AI — Advanced reasoning with 256K context window](https://console.groq.com/docs/model/moonshotai/kimi-k2-instruct-0905)[openai/gpt-oss-120bOpenAI — Powerful open-source model for complex coding tasks](https://console.groq.com/docs/model/openai/gpt-oss-120b)

Cline automatically fetches available models from the Groq API, so you'll always see the latest options in the model dropdown.

## [Learn More](#learn-more)

* [Cline Installation Guide](https://docs.cline.bot/getting-started/installing-cline) — install Cline IDE extension for VS Code, Cursor, JetBrains, or VSCodium/Windsurf
* [Cline CLI Installation](https://docs.cline.bot/cline-cli/installation) — install and get started with Cline CLI
* [Cline Groq Provider Configuration](https://docs.cline.bot/provider-config/groq) — detailed Groq provider setup and supported models
* [Groq model catalog](https://console.groq.com/docs/models) — explore all available Groq models
