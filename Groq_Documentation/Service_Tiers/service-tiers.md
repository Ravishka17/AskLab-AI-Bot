---
description: Choose between performance, on-demand, flex, and auto tiers based on latency, throughput, and reliability needs.
title: Service Tiers - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Service Tiers

Groq offers multiple service tiers so you can tune for latency, throughput, and reliability. You can distinguish these by providing the `service_tier` parameter.

* `performance`: The highest tier we have providing reliable low latency for the most critical production applications. This tier is available to our enterprise users. More info at [Performance Tier](https://console.groq.com/docs/performance-tier).
* `on_demand`: This is the default tier if you omit `service_tier`. This is the standard tier you are used to using and you get the predictable high speeds of Groq's LPU with occasional queue latency during peak times.
* `flex`: higher throughput and provided as best effort. You have high limits but may get over capacity errors. Check out [Flex Processing](https://console.groq.com/docs/flex-processing) for more info.
* `auto`: Pass this if you dont want to think about tiers and you want to leverage the best tier available to you at any given moment.

Python

```
import Groq from "groq-sdk";

const client = new Groq({ apiKey: process.env.GROQ_API_KEY });

const completion = await client.chat.completions.create({
  model: "openai/gpt-oss-120b",
  service_tier: "auto",
  messages: [{ role: "user", content: "Summarize the latest release highlights." }],
});

console.log(completion.choices[0].message.content);
```

```
import os
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

completion = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    service_tier="auto",
    messages=[{"role": "user", "content": "Summarize the latest release highlights."}],
)

print(completion.choices[0].message.content)
```

```
curl https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "service_tier": "auto",
    "messages": [
      { "role": "user", "content": "Summarize the latest release highlights." }
    ]
  }'
```

## [Batch and asynchronous workloads](#batch-and-asynchronous-workloads)

The [Batch API](https://console.groq.com/docs/batch) has its own processing window and rate limits and does **not** accept the `service_tier` parameter. Use synchronous requests when you need explicit tier control; batch jobs run independently of your per-model synchronous limits.
