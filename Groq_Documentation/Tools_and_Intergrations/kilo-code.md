---
description: Connect Kilo Code&#x27;s AI-powered coding assistant to Groq for ultra-fast inference in VS Code, Cursor, or JetBrains IDEs.
title: Kilo Code + Groq - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Kilo Code + Groq

[Kilo Code](https://kilo.ai/) is an AI-powered coding assistant available as an extension for VS Code, Cursor, and JetBrains IDEs. Pair it with Groq's LPU inference to get ultra-fast response times for interactive development workflows with native Groq provider support.

## [Prerequisites](#prerequisites)

* Groq account with an API key from [console.groq.com/keys](https://console.groq.com/keys)
* Kilo Code installed in your IDE (VS Code, Cursor, or JetBrains) — follow the [Kilo Code installation guide](https://kilo.ai/docs/getting-started/installing) for your IDE

## [Setup](#setup)

1. **Configure Groq Provider** Open Kilo Code settings (click the gear icon in the Kilo Code panel) and:  
   * Select **"Groq"** from the "API Provider" dropdown  
   * Paste your Groq API key into the "Groq API Key" field  
   * Choose your desired model from the "Model" dropdown  
For detailed Groq provider configuration, see the [Kilo Code Groq Provider Guide](https://kilo.ai/docs/providers/groq).
2. **Start Coding** Open the Kilo Code panel and start chatting or use autocomplete features. Groq's ultra-fast inference will provide near-instant responses.

## [Recommended Groq Models](#recommended-groq-models)

[moonshotai/kimi-k2-instruct-0905Most PopularMoonshot AI — Advanced reasoning with 256K context window](https://console.groq.com/docs/model/moonshotai/kimi-k2-instruct-0905)[openai/gpt-oss-120bOpenAI — Powerful open-source model for complex coding tasks](https://console.groq.com/docs/model/openai/gpt-oss-120b)

Kilo Code automatically fetches available models from the Groq API, so you'll always see the latest options in the model dropdown.

## [Learn More](#learn-more)

* [Kilo Code Documentation](https://kilo.ai/docs/getting-started/installing) — complete installation and setup guide
* [Kilo Code Groq Provider Guide](https://kilo.ai/docs/providers/groq) — detailed Groq configuration and model information
* [Groq model catalog](https://console.groq.com/docs/models) — explore all available models
