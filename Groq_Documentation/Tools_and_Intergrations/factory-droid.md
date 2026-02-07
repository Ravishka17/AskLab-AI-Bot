---
description: Connect Factory&#x27;s autonomous engineering agents to Groq for low-latency coding sessions with your own API key.
title: Factory Droid + Groq - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Factory Droid + Groq

[Factory Droid](https://factory.ai/) is Factory.ai's autonomous engineering agent. Pair it with Groq's LPU inference to get low-latency code generation while keeping your Groq API key on-device via Bring Your Own Key (BYOK).

## [Prerequisites](#prerequisites)

* Groq account with an API key from [console.groq.com/keys](https://console.groq.com/keys?tutorial=factory)
* Factory CLI (`droid`) installed locally — follow [Factory's Quickstart Guide](https://docs.factory.ai/cli/getting-started/quickstart) to install and authenticate

## [Setup](#setup)

1. **Configure Groq Provider** Add Groq models to your Factory configuration: Edit your Factory config file and add your Groq model definitions:  
   * **macOS/Linux:** `~/.factory/config.json`  
   * **Windows:** `%USERPROFILE%\.factory\config.json`  
JSON  
```  
{  
  "custom_models": [  
    {  
      "model_display_name": "Kimi K2 [Groq]",  
      "model": "moonshotai/kimi-k2-instruct-0905",  
      "base_url": "https://api.groq.com/openai/v1",  
      "api_key": "YOUR_GROQ_KEY",  
      "provider": "generic-chat-completion-api",  
      "max_tokens": 16384  
    },  
    {  
      "model_display_name": "GPT-OSS 120b [Groq]",  
      "model": "openai/gpt-oss-120b",  
      "base_url": "https://api.groq.com/openai/v1",  
      "api_key": "YOUR_GROQ_KEY",  
      "provider": "generic-chat-completion-api",  
      "max_tokens": 65536  
    }  
  ]  
}  
```  
Replace `YOUR_GROQ_KEY` with your API key from [console.groq.com/keys](https://console.groq.com/keys?tutorial=factory).
2. **Start Coding** Inside the CLI run `/model` and choose the Groq model you added under **Custom models**. You can now use Factory Droid with Groq's low-latency inference.

## [Recommended Groq Models](#recommended-groq-models)

[moonshotai/kimi-k2-instruct-0905Most PopularMoonshot AI — Advanced reasoning with 256K context window](https://console.groq.com/docs/model/moonshotai/kimi-k2-instruct-0905)[openai/gpt-oss-120bOpenAI — Powerful open-source model for complex coding tasks](https://console.groq.com/docs/model/openai/gpt-oss-120b)

Factory recommends models with at least 30B parameters when shipping production-critical changes.

## [Learn More](#learn-more)

* [Factory BYOK documentation](https://docs.factory.ai/cli/byok/overview) — advanced configuration options
* [Factory CLI reference](https://docs.factory.ai/reference/cli-reference) — complete command reference
* [Groq model catalog](https://console.groq.com/docs/models) — explore all available models
