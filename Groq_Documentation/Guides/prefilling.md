---
description: Learn how to control model output by prefilling assistant messages, enabling specific output formats and maintaining conversation consistency.
title: Prefilling - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Assistant Message Prefilling

When using Groq API, you can have more control over your model output by prefilling `assistant` messages. This technique gives you the ability to direct any text-to-text model powered by Groq to:

* Skip unnecessary introductions or preambles
* Enforce specific output formats (e.g., JSON, XML)
* Maintain consistency in conversations

## [How to Prefill Assistant Messages](#how-to-prefill-assistant-messages)

To prefill, simply include your desired starting text in the `assistant` message and the model will generate a response starting with the `assistant` message.

  
**Note:** For some models, adding a newline after the prefill `assistant` message leads to better results.

  
**💡 Tip:** Use the stop sequence (`stop`) parameter in combination with prefilling for even more concise results. We recommend using this for generating code snippets.

## [Example Usage](#example-usage)

**Example 1: Controlling output format for concise code snippets**

  
When trying the below code, first try a request without the prefill and then follow up by trying another request with the prefill included to see the difference!

curlJavaScriptPythonJSON

  
shell

```
from groq import Groq

client = Groq()

completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": "Write a Python function to calculate the factorial of a number."
        },
        {
            "role": "assistant",
            "content": "```python"
        }
    ],
    stream=True,
    stop="```",
)

for chunk in completion:
    print(chunk.choices[0].delta.content or "", end="")
```
  
  
**Example 2: Extracting structured data from unstructured input**

curlJavaScriptPythonJSON

  
shell

```
from groq import Groq

client = Groq()

completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": "Extract the title, author, published date, and description from the following book as a JSON object:\n\n\"The Great Gatsby\" is a novel by F. Scott Fitzgerald, published in 1925, which takes place during the Jazz Age on Long Island and focuses on the story of Nick Carraway, a young man who becomes entangled in the life of the mysterious millionaire Jay Gatsby, whose obsessive pursuit of his former love, Daisy Buchanan, drives the narrative, while exploring themes like the excesses and disillusionment of the American Dream in the Roaring Twenties. \n"
        },
        {
            "role": "assistant",
            "content": "```json"
        }
    ],
    stream=True,
    stop="```",
)

for chunk in completion:
    print(chunk.choices[0].delta.content or "", end="")
```
