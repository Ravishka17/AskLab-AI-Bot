---
description: Overview of Compound and Mini AI systems - their capabilities, differences, and use cases.
title: Systems - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Systems

Groq offers two compound AI systems that intelligently use external tools to provide more accurate, up-to-date, and capable responses than traditional LLMs alone. Both systems support web search and code execution, but differ in their approach to tool usage.

* **[Compound](https://console.groq.com/docs/compound/systems/compound)** (`groq/compound`) - Full-featured system with up to 10 tool calls per request
* **[Compound Mini](https://console.groq.com/docs/compound/systems/compound-mini)** (`groq/compound-mini`) - Streamlined system with up to 1 tool call and average 3x lower latency

Groq's compound AI systems should not be used by customers for processing protected health information as it is not a HIPAA Covered Cloud Service under Groq's Business Associate Addendum at this time.

## [Getting Started](#getting-started)

[CompoundLearn about the full-featured system with up to 10 tool calls per request](https://console.groq.com/docs/compound/systems/compound)[Compound MiniDiscover the fast, single-tool-call system with average 3x lower latency](https://console.groq.com/docs/compound/systems/compound-mini)

Both systems use the same API interface - simply change the `model` parameter to `groq/compound` or `groq/compound-mini` to get started.

## [System Comparison](#system-comparison)

| Feature                    | Compound                 | Compound Mini             |
| -------------------------- | ------------------------ | ------------------------- |
| **Tool Calls per Request** | Up to 10                 | Up to 1                   |
| **Average Latency**        | Standard                 | 3x Lower                  |
| **Token Speed**            | \~350 tps                | \~350 tps                 |
| **Best For**               | Complex multi-step tasks | Quick single-step queries |

## [Key Differences](#key-differences)

### [Compound](#compound)

* **Multiple Tool Calls**: Can perform up to **10 server-side tool calls** before returning an answer
* **Complex Workflows**: Ideal for tasks requiring multiple searches, code executions, or iterative problem-solving
* **Comprehensive Analysis**: Can gather information from multiple sources and perform multi-step reasoning
* **Use Cases**: Research tasks, complex data analysis, multi-part coding challenges

### [Compound Mini](#compound-mini)

* **Single Tool Call**: Performs up to **1 server-side tool call** before returning an answer
* **Fast Response**: Average 3x lower latency compared to Compound
* **Direct Answers**: Perfect for straightforward queries that need one piece of current information
* **Use Cases**: Quick fact-checking, single calculations, simple web searches

## [Available Tools](#available-tools)

Both systems support the same set of tools:

* **Web Search** \- Access real-time information from the web
* **Code Execution** \- Execute Python code automatically
* **Visit Website** \- Access and analyze specific website content
* **Browser Automation** \- Interact with web pages through automated browser actions
* **Wolfram Alpha** \- Access computational knowledge and mathematical calculations
  
For more information about tool capabilities, see the [Built-in Tools](https://console.groq.com/docs/compound/built-in-tools) page.

## [When to Choose Which System](#when-to-choose-which-system)

### [Choose Compound When:](#choose-compound-when)

* You need comprehensive research across multiple sources
* Your task requires iterative problem-solving
* You're building complex analytical workflows
* You need multi-step code generation and testing

### [Choose Compound Mini When:](#choose-compound-mini-when)

* You need quick answers to straightforward questions
* Latency is a critical factor for your application
* You're building real-time applications
* Your queries typically require only one tool call
