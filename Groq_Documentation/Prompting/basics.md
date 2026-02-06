---
description: Learn the essential building blocks of effective prompting, including roles, instructions, context, input and output formats to get reliable results from large language models.
title: Prompt Basics - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Prompt Basics

Prompting is the methodology through which we communicate instructions, parameters, and expectations to large language models. Consider a prompt as a detailed specification document provided to the model: the more precise and comprehensive the specifications, the higher the quality of the output. This guide establishes the fundamental principles for crafting effective prompts for open-source instruction-tuned models, including Llama, Deepseek, and Gemma.

## [Why Prompts Matter](#why-prompts-matter)

Large language models require clear direction to produce optimal results. Without precise instructions, they may produce inconsistent outputs. Well-structured prompts provide several benefits:

* **Reduce development time** by minimizing iterations needed for acceptable results.
* **Enhance output consistency** to ensure responses meet validation requirements without modification.
* **Optimize resource usage** by maintaining efficient context window utilization.

## [Prompt Building Blocks](#prompt-building-blocks)

Most high-quality prompts contain five elements: **role, instructions, context, input, expected output**.

| Element             | What it does                                          |
| ------------------- | ----------------------------------------------------- |
| **Role**            | Sets persona or expertise ("You are a data analyst…") |
| **Instructions**    | Bullet-proof list of required actions                 |
| **Context**         | Background knowledge or reference material            |
| **Input**           | The data or question to transform                     |
| **Expected Output** | Schema or miniature example to lock formatting        |

### [Real-world use case](#realworld-use-case)

Here's a real-world example demonstrating how these prompt building blocks work together to extract structured data from an email. Each element plays a crucial role in ensuring accurate, consistent output:

1. **System** \- fixes the model's role so it doesn't add greetings or extra formatting.
2. **Instructions** \- lists the exact keys; pairing this with [JSON mode](https://console.groq.com/docs/structured-outputs#json-object-mode) or [tool use](https://console.groq.com/docs/tool-use) further guarantees parseable output.
3. **Context** \- gives domain hints ("Deliver to", postcode format) that raise extraction accuracy without extra examples.
4. **Input** \- the raw e-mail; keep original line breaks so the model can latch onto visual cues.
5. **Example Output** \- a miniature few-shot sample that locks the reply shape to one JSON object.

curl

```
### System
You are a data-extraction bot. Return **ONLY** valid JSON.

### Instructions
Return only JSON with keys:
- name (string)
- street (string)
- city (string)
- postcode (string)

### Context
"Ship-to" or "Deliver to" often precedes the address.
Postcodes may include letters (e.g., SW1A 1AA).

### Input
Subject: Shipping Request - Order #12345

Hi Shipping Team,

Please process the following delivery for Order #12345:

Deliver to:
Jane Smith
123 Oak Avenue
Manchester
M1 1AA

Items:
- 2x Widget Pro (SKU: WP-001)
- 1x Widget Case (SKU: WC-100)

Thanks,
Sales Team

### Example Output
{"name":"John Doe","street":"456 Pine Street","city":"San Francisco","postcode":"94105"}
```

## [Role Channels](#role-channels)

Most chat-style APIs expose **three channels**:

| Channel   | Typical Use                                                                                                          |
| --------- | -------------------------------------------------------------------------------------------------------------------- |
| system    | High-level persona & non-negotiable rules ("You are a helpful financial assistant.").                                |
| user      | The actual request or data, such as a user's message in a chat.                                                      |
| assistant | The model's response. In multi-turn conversations, the assistant role can be used to track the conversation history. |

  
The following example demonstrates how to implement a customer service chatbot using role channels. Role channels provide a structured way for the model to maintain context and generate contextually appropriate responses throughout the conversation.

PythonJavaScript

Python

```
from groq import Groq

client = Groq()

system_prompt = """
You are a helpful IT support chatbot for 'Tech Solutions'.
Your role is to assist employees with common IT issues, provide guidance on using company software, and help troubleshoot basic technical problems.
Respond clearly and patiently. If an issue is complex, explain that you will create a support ticket for a human technician.
Keep responses brief and ask a maximum of one question at a time.
"""

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": "My monitor isn't turning on.",
        },
        {
            "role": "assistant",
            "content": "Let's try to troubleshoot. Is the monitor properly plugged into a power source?",
        },
        {
            "role": "user",
            "content": "Yes, it's plugged in."
        }
    ],
    model="llama-3.3-70b-versatile",
)

print(chat_completion.choices[0].message.content)
```

Output

Is the power button on the monitor being pressed, and are any lights or indicators on the monitor turning on when you press it?

## [Prompt Priming](#prompt-priming)

Prompt priming is the practice of giving the model an **initial block of instructions or context** that influences every downstream token the model generates. Think of it as "setting the temperature of the conversation room" before anyone walks in. This usually lives in the **system** message; in single-shot prompts it's the first paragraph you write. Unlike one- or few-shot demos, priming does not need examples; the power comes from describing roles ("You are a medical billing expert"), constraints ("never reveal PII"), or seed knowledge ("assume the user's database is Postgres 16").

### [Why it Works](#why-it-works)

Large language models generate text by conditioning on **all previous tokens**, weighting earlier tokens more heavily than later ones. By positioning high-leverage tokens (role, style, rules) first, priming biases the probability distribution over next tokens toward answers that respect that frame.

### [Example (Primed Chat)](#example-primed-chat)

curl

```
### System (Priming)
You are ComplianceLlama, an expert in U.S. financial-services regulation.
Always cite the relevant CFR section and warn when user requests violate §1010.620.

### User
"Can my fintech app skip KYC if all transfers are under $500?"

### Assistant
```

Output

"Transfers below $1,000 still trigger the customer-identification program requirements in **31 CFR §1022.220**. Skipping KYC would violate FinCEN rules…"

### [When to Use](#when-to-use)

| Situation                                                          | Why priming helps                                                                                     |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| **Stable persona or voice** across many turns                      | Guarantees the model keeps the same tone (e.g., "seasoned litigator") without repeating instructions. |
| **Policy & safety guardrails**                                     | Embeds non-negotiable rules such as "do not reveal trade secrets."                                    |
| **Injecting domain knowledge** (e.g., product catalog, API schema) | Saves tokens vs. repeating specs each turn; the model treats the primed facts as ground truth.        |
| **Special formatting or citation requirements**                    | Place markdown/JSON/XML templates in the primer so every answer starts correct.                       |
| **Consistent style transfer** (pirate talk, Shakespearean English) | Role-play seeds ensure creative outputs stay on-brand.                                                |
| **Zero-shot tasks that need extra context**                        | A brief primer often outperforms verbose instructions alone.                                          |

### [Tips](#tips)

* **Keep it concise:** 300-600 tokens is usually enough; longer primers steal context window from the user.
* **Separate roles:** Use dedicated _system_, _user_, and _assistant_ roles so the model understands hierarchy.
* **Test for drift:** Over many turns, the model can "forget" earlier tokens: re-send the primer or summarize it periodically.
* **Watch for over-constraining:** Heavy persona priming can hurt factual accuracy on analytical tasks; disable or slim down when precision matters.
* **Combine with examples:** For structured outputs, prime the schema then add one-shot examples to lock formatting.

## [Core Principles](#core-principles)

1. **Lead with the must-do.** Put critical instructions first; the model weighs early tokens more heavily.
2. **Show, don't tell.** A one-line schema or table example beats a paragraph of prose.
3. **State limits explicitly.** Use "Return **only** JSON" or "less than 75 words" to eliminate chatter.
4. **Use plain verbs.** "Summarize in one bullet per metric" is clearer than "analyze."
5. **Chunk long inputs.** Delimit data with \`\`\` or <<< … >>> so the model sees clear boundaries.

## [Context Budgeting](#context-budgeting)

While many models can handle up to **128K** tokens (or more), using a longer system prompt still costs latency and money. While you might be able to fit a lot of information in the model's context window, it could increase latency and reduce the model's accuracy. As a best practice, only include what is needed for the model to generate the desired response in the context.

## [Quick Prompting Wins](#quick-prompting-wins)

Try these **10-second tweaks** before adding examples or complex logic:

| Quick Fix                                                   | Outcome                                        |
| ----------------------------------------------------------- | ---------------------------------------------- |
| Add a one-line persona (_"You are a veteran copy editor."_) | Sharper, domain-aware tone                     |
| Show a mini output sample (one-row table / tiny JSON)       | Increased formatting accuracy                  |
| Use numbered steps in instructions                          | Reduces answers with extended rambling         |
| Add "no extra prose" at the end                             | Stops model from adding greetings or apologies |

## [Common Mistakes to Avoid](#common-mistakes-to-avoid)

Review these recommended practices and solutions to avoid common prompting issues.

| Common Mistake                      | Result                        | Solution                                             |
| ----------------------------------- | ----------------------------- | ---------------------------------------------------- |
| **Hidden ask** buried mid-paragraph | Model ignores it              | Move all instructions to top bullet list             |
| **Over-stuffed context**            | Truncated or slow responses   | Summarize, remove old examples                       |
| **Ambiguous verbs** (_"analyze"_)   | Vague output                  | Be explicit (_"Summarize in one bullet per metric"_) |
| **Partial JSON keys** in sample     | Model Hallucinates extra keys | Show the **full** schema: even if brief              |

## [Parameter Tuning](#parameter-tuning)

Optimize model outputs by configuring key parameters like temperature and top-p. These settings control the balance between deterministic and creative responses, with recommended values based on your specific use case.

| Parameter       | What it does                                                                         | Safe ranges | Typical use                                            |
| --------------- | ------------------------------------------------------------------------------------ | ----------- | ------------------------------------------------------ |
| **Temperature** | Global randomness (higher = more creative)                                           | 0 - 1.0     | 0 - 0.3 facts, 0.7 - 0.9 creative                      |
| **Top-p**       | Keeps only the top p cumulative probability mass - use this or temperature, not both | 0.5 - 1.0   | 0.9 facts, 1.0 creative                                |
| **Top-k**       | Limits to the k highest-probability tokens                                           | 20 - 100    | Rarely needed; try k = 40 for deterministic extraction |

### [Quick presets](#quick-presets)

The following are recommended values to set temperature or top-p to (but not both) for various use cases:

| Scenario               | Temp | Top-p | Comments                     |
| ---------------------- | ---- | ----- | ---------------------------- |
| Factual Q&A            | 0.2  | 0.9   | Keeps dates & numbers stable |
| Data extraction (JSON) | 0.0  | 0.9   | Deterministic keys/values    |
| Creative copywriting   | 0.8  | 1.0   | Vivid language, fresh ideas  |
| Brainstorming list     | 0.7  | 0.95  | Variety without nonsense     |
| Long-form code         | 0.3  | 0.85  | Fewer hallucinated APIs      |

---

## [Controlling Length & Cost](#controlling-length--cost)

The following are recommended settings for controlling token usage and costs with length limits, stop sequences, and deterministic outputs.

| Setting                 | Purpose                                          | Tip                                              |
| ----------------------- | ------------------------------------------------ | ------------------------------------------------ |
| max\_completion\_tokens | Hard cap on completion size                      | Set 10-20 % above ideal answer length            |
| Stop sequences          | Early stop when model hits token(s)              | Use "###" or another delimiter                   |
| System length hints     | "less than 75 words" or "return only table rows" | Model respects explicit numbers                  |
| seed                    | Controls randomness deterministically            | Use same seed for consistent outputs across runs |

  
**Real-world example:**

> Invoice summarizer returns _exactly_ three bullets by stating "Provide **three** bullets, each less than 12 words" and using `max_completion_tokens=60`.

### [Stop Sequences](#stop-sequences)

The `stop` parameter allows you to define sequences where the model will stop generating tokens. This is particularly useful for:

* Creating structured outputs with clear boundaries
* Preventing the model from continuing beyond a certain point
* Implementing custom dialogue patterns

PythonJavaScript

Python

```
# Using a custom stop sequence for structured, concise output.
# The model is instructed to produce '###' at the end of the desired content.
# The API will stop generation when '###' is encountered and will NOT include '###' in the response.

from groq import Groq

client = Groq()
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Provide a 2-sentence summary of the concept of 'artificial general intelligence'. End your summary with '###'."
        }
        # Model's goal before stop sequence removal might be:
        # "Artificial general intelligence (AGI) refers to a type of AI that possesses the ability to understand, learn, and apply knowledge across a wide range of tasks at a level comparable to that of a human being. This contrasts with narrow AI, which is designed for specific tasks. ###"
    ],
    model="llama-3.1-8b-instant",
    stop=["###"],
    max_tokens=100 # Ensure enough tokens for the summary + stop sequence
)

print(chat_completion.choices[0].message.content)
```

Output

Artificial general intelligence (AGI) refers to a type of AI that possesses the ability to understand, learn, and apply knowledge across a wide range of tasks at a level comparable to that of a human being. This contrasts with narrow AI, which is designed for specific tasks.

  
When defining stop sequences:

* Include instructions in your prompt to tell the model to produce the stop sequence in the response
* Use unique patterns unlikely to appear in normal text, such as `###END###` or `</response>`
* For code generation, use language-specific endings like `}` or `;`

### [Deterministic Outputs with Seed](#deterministic-outputs-with-seed)

The `seed` parameter enables deterministic generation, making outputs consistent across multiple runs with the same parameters. This is valuable for:

* Reproducible results in research or testing
* Consistent user experiences in production
* A/B testing different prompts with controlled randomness

PythonJavaScript

Python

```
from groq import Groq

client = Groq()
chat_completion = client.chat.completions.create(
    messages=[
      { "role": "system", "content": "You are a creative storyteller." },
      { "role": "user", "content": "Write a brief opening line to a mystery novel." }
    ],
    model="llama-3.1-8b-instant",
    temperature=0.8,  # Some creativity allowed
    seed=700,  # Deterministic seed
    max_tokens=100
)

print(chat_completion.choices[0].message.content)
```

Output

"It was the night the clock tower's chimes fell silent, and Detective Jameson received a mysterious letter with a single, chilling phrase: 'The truth lies in Ravenswood.'"

  
Important notes about `seed`:

* Determinism is best-effort and is not guaranteed across model versions
* Check the `system_fingerprint` in responses to track backend changes
* Combining `seed` with a lower temperature (0.0 - 0.3) may improve determinism
* Useful for debugging and improving prompts iteratively

## [Guardrails & Safety](#guardrails--safety)

Good prompts set the rules; dedicated guardrail models enforce them. [Meta's **Llama Guard 4**](https://console.groq.com/docs/content-moderation) is designed to sit in front of: or behind: your main model, classifying prompts or outputs for safety violations (hate, self-harm, private data). Integrating a moderation step can cut violation rates without changing your core prompt structure.

When stakes are high (finance, health, compliance), pair **clear instructions** ("never reveal PII") with an automated filter that rejects or sanitizes unsafe content before it reaches the user.

## [Next Steps](#next-steps)

Ready to level up? Explore dedicated [**prompt patterns**](https://console.groq.com/docs/prompting/patterns) like zero-shot, one-shot, few-shot, chain-of-thought, and more to match the pattern to your task complexity. From there, iterate and refine to improve your prompts.
