---
description: Prioritized capacity on GroqCloud&#x27;s multi tenant inference apis
title: Performance Tier - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Performance Tier

The Performance tier provides prioritized capacity for low, consistent latency. It includes a 99.9% availability SLA and a 99% latency guarantee aligned to your enterprise agreement.

**Enterprise only:** The Performance tier is only available on enterprise plans. [Reach out to our enterprise team](https://groq.com/enterprise-access) to get access.

## [Best Use Cases](#best-use-cases)

* User-facing or production-critical paths where latency consistency matters most.
* Workloads that need low p99 time to first token.
* If you want to easily burst beyond your limits, you can pass `service_tier=auto` in order to use your performance tier limits if they are avaiable, and burst into on\_demand. This is a great way to balance performance and costs.

## [Packaging and pricing](#packaging-and-pricing)

* Performance is delivered as provisioned throughput: you purchase input and output capacity bundles and pay for that provisioned capacity rather than per-token usage. Reach out to inquire about pricing.
* Availability SLA: 99.9% uptime and 99% low latency guarantee. (Details specified in offline agreement)

## [Model availability](#model-availability)

| Model ID                | Name                    |
| ----------------------- | ----------------------- |
| openai/gpt-oss-120b     | GPT-OSS 120B            |
| openai/gpt-oss-20b      | GPT-OSS 20B             |
| llama-3.3-70b-versatile | Llama 3.3 70B Versatile |

## [Requirements](#requirements)

* Context length (uncached) must be under 8,192 tokens

**Note**: If you want automatic context-length handling and tier mapping, use `service_tier=auto` and we'll route requests to appropriate tiers behind the scenes based on your limits and context size.
