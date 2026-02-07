---
description: Explore the built-in tools available in Groq&#x27;s Compound systems for web search, code execution, and more.
title: Built-in Tools - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Built-in Tools

Compound systems come equipped with a comprehensive set of built-in tools that can be intelligently called to answer user queries. These tools not only expand the capabilities of language models by providing access to real-time information, computational power, and interactive environments, but also eliminate the need to build and maintain the underlying infrastructure for these tools yourself.

Built-in tools with Compound systems are not HIPAA Covered Cloud Services under Groq's Business Associate Addendum at this time. These tools are also not available currently for use with regional / sovereign endpoints.

## [Default Tools](#default-tools)

The tools enabled by default vary depending on your Compound system version:

| Version                        | [Web Search](https://console.groq.com/docs/web-search) | [Code Execution](https://console.groq.com/docs/code-execution) | [Visit Website](https://console.groq.com/docs/visit-website) |
| ------------------------------ | ------------------------------ | -------------------------------------- | ------------------------------------ |
| Newer than 2025-07-23 (Latest) | ✅                              | ✅                                      | ✅                                    |
| 2025-07-23 (Default)           | ✅                              | ✅                                      | ❌                                    |

All tools are automatically enabled by default. Compound systems intelligently decide when to use each tool based on the user's query.

  
For more information on how to set your Compound system version, see the [Compound System Versioning](https://console.groq.com/docs/compound#system-versioning) page.

## [Available Tools](#available-tools)

These are all the available built-in tools on Groq's Compound systems.

| Tool                                           | Description                                                                      | Identifier          | [Supported Compound Version](https://console.groq.com/docs/compound#system-versioning) |
| ---------------------------------------------- | -------------------------------------------------------------------------------- | ------------------- | -------------------------------------------------------------- |
| [Web Search](https://console.groq.com/docs/web-search)                 | Access real-time web content and up-to-date information with automatic citations | web\_search         | All versions                                                   |
| [Visit Website](https://console.groq.com/docs/visit-website)           | Fetch and analyze content from specific web pages                                | visit\_website      | latest                                                         |
| [Browser Automation](https://console.groq.com/docs/browser-automation) | Interact with web pages through automated browser actions                        | browser\_automation | latest                                                         |
| [Code Execution](https://console.groq.com/docs/code-execution)         | Execute Python code automatically in secure sandboxed environments               | code\_interpreter   | All versions                                                   |
| [Wolfram Alpha](https://console.groq.com/docs/wolfram-alpha)           | Access computational knowledge and mathematical calculations                     | wolfram\_alpha      | latest                                                         |

  
Jump to the [Configuring Tools](#configuring-tools) section to learn how to enable specific tools via their identifiers. Some tools are only available on certain Compound system versions - [learn more about how to set your Compound version here](https://console.groq.com/docs/compound#system-versioning).

## [Configuring Tools](#configuring-tools)

You can customize which tools are available to Compound systems using the `compound_custom.tools.enabled_tools` parameter. This allows you to restrict or specify exactly which tools should be available for a particular request.

  
For a list of available tool identifiers, see the [Available Tools](#available-tools) section.

### [Example: Enable Specific Tools](#example-enable-specific-tools)

Python

```
from groq import Groq

client = Groq(
    default_headers={
        "Groq-Model-Version": "latest"
    }
)

response = client.chat.completions.create(
    model="groq/compound",
    messages=[
        {
            "role": "user",
            "content": "Search for recent AI developments and then visit the Groq website"
        }
    ],
    compound_custom={
        "tools": {
            "enabled_tools": ["web_search", "visit_website"]
        }
    }
)
```

```
import Groq from "groq-sdk";

const groq = new Groq({
  defaultHeaders: {
    "Groq-Model-Version": "latest"
  }
});

const response = await groq.chat.completions.create({
  model: "groq/compound",
  messages: [
    {
      role: "user",
      content: "Search for recent AI developments and then visit the Groq website"
    }
  ],
  compound_custom: {
    tools: {
      enabled_tools: ["web_search", "visit_website"]
    }
  }
});
```

```
curl "https://api.groq.com/openai/v1/chat/completions" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GROQ_API_KEY}" \
  -H "Groq-Model-Version: latest" \
  -d '{
        "messages": [
          {
            "role": "user",
            "content": "Search for recent AI developments and then visit the Groq website"
          }
        ],
        "model": "groq/compound",
        "compound_custom": {
          "tools": {
            "enabled_tools": ["web_search", "visit_website"]
          }
        }
      }'
```

### [Example: Code Execution Only](#example-code-execution-only)

Python

```
from groq import Groq

client = Groq()

response = client.chat.completions.create(
    model="groq/compound",
    messages=[
        {
            "role": "user", 
            "content": "Calculate the square root of 12345"
        }
    ],
    compound_custom={
        "tools": {
            "enabled_tools": ["code_interpreter"]
        }
    }
)
```

```
import Groq from "groq-sdk";

const groq = new Groq();

const response = await groq.chat.completions.create({
  model: "groq/compound",
  messages: [
    {
      role: "user",
      content: "Calculate the square root of 12345"
    }
  ],
  compound_custom: {
    tools: {
      enabled_tools: ["code_interpreter"]
    }
  }
});
```

```
curl "https://api.groq.com/openai/v1/chat/completions" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GROQ_API_KEY}" \
  -d '{
        "messages": [
          {
            "role": "user",
            "content": "Calculate the square root of 12345"
          }
        ],
        "model": "groq/compound",
        "compound_custom": {
          "tools": {
            "enabled_tools": ["code_interpreter"]
          }
        }
      }'
```

## [Pricing](#pricing)

See the [Pricing](https://groq.com/pricing) page for detailed information on costs for each tool.
