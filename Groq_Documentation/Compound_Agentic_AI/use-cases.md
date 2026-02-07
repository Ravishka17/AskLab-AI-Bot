---
description: Explore practical applications and examples of compound AI systems.
title: Use Cases - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Use Cases

Groq's compound systems excel at a wide range of use cases, particularly when real-time information is required.

## [Real-time Fact Checker and News Agent](#realtime-fact-checker-and-news-agent)

Your application needs to answer questions or provide information that requires up-to-the-minute knowledge, such as:

* Latest news
* Current stock prices
* Recent events
* Weather updates

Building and maintaining your own web scraping or search API integration is complex and time-consuming.

### [Solution with Compound](#solution-with-compound)

Simply send the user's query to `groq/compound`. If the query requires current information beyond its training data, it will automatically trigger its built-in web search tool to fetch relevant, live data before formulating the answer.

### [Why It's Great](#why-its-great)

* Get access to real-time information instantly without writing any extra code for search integration
* Leverage Groq's speed for a real-time, responsive experience

### [Code Example](#code-example)

Python

```
import os
from groq import Groq

# Ensure your GROQ_API_KEY is set as an environment variable
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

user_query = "What were the main highlights from the latest Apple keynote event?"
# Or: "What's the current weather in San Francisco?"
# Or: "Summarize the latest developments in fusion energy research this week."

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": user_query,
        }
    ],
    # The *only* change needed: Specify the compound model!
    model="groq/compound",
)

print(f"Query: {user_query}")
print(f"Compound Response:\n{chat_completion.choices[0].message.content}")

# You might also inspect chat_completion.choices[0].message.executed_tools
# if you want to see if/which tool was used, though it's not necessary.
```

```
import Groq from "groq-sdk";

const groq = new Groq();

export async function main() {
  const user_query = "What were the main highlights from the latest Apple keynote event?"
  // Or: "What's the current weather in San Francisco?"
  // Or: "Summarize the latest developments in fusion energy research this week."

  const completion = await groq.chat.completions.create({
    messages: [
      {
        role: "user",
        content: user_query,
      },
    ],
    // The *only* change needed: Specify the compound model!
    model: "groq/compound",
  });

  console.log(`Query: ${user_query}`);
  console.log(`Compound Response:\n${completion.choices[0]?.message?.content || ""}`);

  // You might also inspect chat_completion.choices[0].message.executed_tools
  // if you want to see if/which tool was used, though it's not necessary.
}

main();
```

```
import Groq from "groq-sdk";

const groq = new Groq();

export async function main() {
  const user_query = "What were the main highlights from the latest Apple keynote event?"
  // Or: "What's the current weather in San Francisco?"
  // Or: "Summarize the latest developments in fusion energy research this week."

  const completion = await groq.chat.completions.create({
    messages: [
      {
        role: "user",
        content: user_query,
      },
    ],
    // The *only* change needed: Specify the compound model!
    model: "groq/compound",
  });

  console.log(`Query: ${user_query}`);
  console.log(`Compound Response:\n${completion.choices[0]?.message?.content || ""}`);

  // You might also inspect chat_completion.choices[0].message.executed_tools
  // if you want to see if/which tool was used, though it's not necessary.
}

main();
```

Find the latest news and headlines

## [Natural Language Calculator and Code Extractor](#natural-language-calculator-and-code-extractor)

You want users to perform calculations, run simple data manipulations, or execute small code snippets using natural language commands within your application, without building a dedicated parser or execution environment.

### [Solution with Compound](#solution-with-compound)

Frame the user's request as a task involving computation or code. `groq/compound-mini` can recognize these requests and use its secure code execution tool to compute the result.

### [Why It's Great](#why-its-great)

* Effortlessly add computational capabilities
* Users can ask things like:  
   * "What's 15% of $540?"  
   * "Calculate the standard deviation of \[10, 12, 11, 15, 13\]"  
   * "Run this python code: print('Hello from Compound!')"

### [Code Example](#code-example)

Python

```
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Example 1: Calculation
computation_query = "Calculate the monthly payment for a $30,000 loan over 5 years at 6% annual interest."

# Example 2: Simple code execution
code_query = "What is the output of this Python code snippet: `data = {'a': 1, 'b': 2}; print(data.keys())`"

# Choose one query to run
selected_query = computation_query

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant capable of performing calculations and executing simple code when asked.",
        },
        {
            "role": "user",
            "content": selected_query,
        }
    ],
    # Use the compound model
    model="groq/compound-mini",
)

print(f"Query: {selected_query}")
print(f"Compound Mini Response:\n{chat_completion.choices[0].message.content}")
```

```
import Groq from "groq-sdk";

const groq = new Groq();

export async function main() {
  // Example 1: Calculation
  const computationQuery = "Calculate the monthly payment for a $30,000 loan over 5 years at 6% annual interest.";

  // Example 2: Simple code execution
  const codeQuery = "What is the output of this Python code snippet: `data = {'a': 1, 'b': 2}; print(data.keys())`";

  // Choose one query to run
  const selectedQuery = computationQuery;

  const completion = await groq.chat.completions.create({
    messages: [
      {
        role: "system",
        content: "You are a helpful assistant capable of performing calculations and executing simple code when asked.",
      },
      {
        role: "user",
        content: selectedQuery,
      }
    ],
    // Use the compound model
    model: "groq/compound-mini",
  });

  console.log(`Query: ${selectedQuery}`);
  console.log(`Compound Mini Response:\n${completion.choices[0]?.message?.content || ""}`);
}

main();
```

```
import Groq from "groq-sdk";

const groq = new Groq();

export async function main() {
  // Example 1: Calculation
  const computationQuery = "Calculate the monthly payment for a $30,000 loan over 5 years at 6% annual interest.";

  // Example 2: Simple code execution
  const codeQuery = "What is the output of this Python code snippet: `data = {'a': 1, 'b': 2}; print(data.keys())`";

  // Choose one query to run
  const selectedQuery = computationQuery;

  const completion = await groq.chat.completions.create({
    messages: [
      {
        role: "system",
        content: "You are a helpful assistant capable of performing calculations and executing simple code when asked.",
      },
      {
        role: "user",
        content: selectedQuery,
      }
    ],
    // Use the compound model
    model: "groq/compound-mini",
  });

  console.log(`Query: ${selectedQuery}`);
  console.log(`Compound Mini Response:\n${completion.choices[0]?.message?.content || ""}`);
}

main();
```

Perform precise and verified calculations

## [Code Debugging Assistant](#code-debugging-assistant)

Developers often need quick help understanding error messages or testing small code fixes. Searching documentation or running snippets requires switching contexts.

### [Solution with Compound](#solution-with-compound)

Users can paste an error message and ask for explanations or potential causes. Compound Mini might use web search to find recent discussions or documentation about that specific error. Alternatively, users can provide a code snippet and ask "What's wrong with this code?" or "Will this Python code run: ...?". It can use code execution to test simple, self-contained snippets.

### [Why It's Great](#why-its-great)

* Provides a unified interface for getting code help
* Potentially draws on live web data for new errors
* Executes code directly for validation
* Speeds up the debugging process

**Note**: `groq/compound-mini` uses one tool per turn, so it might search OR execute, not both simultaneously in one response.

### [Code Example](#code-example)

Python

```
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Example 1: Error Explanation (might trigger search)
debug_query_search = "I'm getting a 'Kubernetes CrashLoopBackOff' error on my pod. What are the common causes based on recent discussions?"

# Example 2: Code Check (might trigger code execution)
debug_query_exec = "Will this Python code raise an error? `import numpy as np; a = np.array([1,2]); b = np.array([3,4,5]); print(a+b)`"

# Choose one query to run
selected_query = debug_query_exec

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful coding assistant. You can explain errors, potentially searching for recent information, or check simple code snippets by executing them.",
        },
        {
            "role": "user",
            "content": selected_query,
        }
    ],
    # Use the compound model
    model="groq/compound-mini",
)

print(f"Query: {selected_query}")
print(f"Compound Mini Response:\n{chat_completion.choices[0].message.content}")
```

```
import Groq from "groq-sdk";

const groq = new Groq();

export async function main() {
  // Example 1: Error Explanation (might trigger search)
  const debugQuerySearch = "I'm getting a 'Kubernetes CrashLoopBackOff' error on my pod. What are the common causes based on recent discussions?";

  // Example 2: Code Check (might trigger code execution)
  const debugQueryExec = "Will this Python code raise an error? `import numpy as np; a = np.array([1,2]); b = np.array([3,4,5]); print(a+b)`";

  // Choose one query to run
  const selectedQuery = debugQueryExec;

  const completion = await groq.chat.completions.create({
    messages: [
      {
        role: "system",
        content: "You are a helpful coding assistant. You can explain errors, potentially searching for recent information, or check simple code snippets by executing them.",
      },
      {
        role: "user",
        content: selectedQuery,
      }
    ],
    // Use the compound model
    model: "groq/compound-mini",
  });

  console.log(`Query: ${selectedQuery}`);
  console.log(`Compound Mini Response:\n${completion.choices[0]?.message?.content || ""}`);
}

main();
```

```
import Groq from "groq-sdk";

const groq = new Groq();

export async function main() {
  // Example 1: Error Explanation (might trigger search)
  const debugQuerySearch = "I'm getting a 'Kubernetes CrashLoopBackOff' error on my pod. What are the common causes based on recent discussions?";

  // Example 2: Code Check (might trigger code execution)
  const debugQueryExec = "Will this Python code raise an error? `import numpy as np; a = np.array([1,2]); b = np.array([3,4,5]); print(a+b)`";

  // Choose one query to run
  const selectedQuery = debugQueryExec;

  const completion = await groq.chat.completions.create({
    messages: [
      {
        role: "system",
        content: "You are a helpful coding assistant. You can explain errors, potentially searching for recent information, or check simple code snippets by executing them.",
      },
      {
        role: "user",
        content: selectedQuery,
      }
    ],
    // Use the compound model
    model: "groq/compound-mini",
  });

  console.log(`Query: ${selectedQuery}`);
  console.log(`Compound Response:\n${completion.choices[0]?.message?.content || ""}`);
}

main();
```

## [Chart Generation](#chart-generation)

Need to quickly create data visualizations from natural language descriptions? Compound's code execution capabilities can help generate charts without writing visualization code directly.

### [Solution with Compound](#solution-with-compound)

Describe the chart you want in natural language, and Compound will generate and execute the appropriate Python visualization code. The model automatically parses your request, generates the visualization code using libraries like matplotlib or seaborn, and returns the chart.

### [Why It's Great](#why-its-great)

* Generate charts from simple natural language descriptions
* Supports common chart types (scatter, line, bar, etc.)
* Handles all visualization code generation and execution
* Customize data points, labels, colors, and layouts as needed

### [Usage and Results](#usage-and-results)

Scatter PlotLine PlotBar PlotPie ChartBox PlotSuperchart

shell

```
curl -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "groq/compound",
    "messages": [
      {
        "role": "user",
        "content": "Create a scatter plot showing the relationship between market cap and daily trading volume for the top 5 tech companies (AAPL, MSFT, GOOGL, AMZN, META). Use current market data."
      }
    ]
  }'
```

### [Results](#results)

![Plot result](https://console.groq.com/_next/image?url=%2Fplot-results%2Fscatterplot.png&w=3840&q=100)

Generate K-means clustering
