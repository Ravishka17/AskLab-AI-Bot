---
description: Deploy and run inference with pre-made LoRA adapters on Groq. Learn about deployment options, supported models, and how to upload your existing LoRA adapters using the Fine-Tuning API.
title: LoRA Inference - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# LoRA Inference on Groq

Groq provides inference services for pre-made Low-Rank Adaptation (LoRA) adapters. LoRA is a Parameter-efficient Fine-tuning (PEFT) technique that customizes model behavior without altering base model weights. Upload your existing LoRA adapters to run specialized inference while maintaining the performance and efficiency of Groq's infrastructure.

This service is not available currently for use with regional / sovereign endpoints.

**Note**: Groq offers LoRA inference services only. We do not provide LoRA fine-tuning services - you must create your LoRA adapters externally using other providers or tools.

With LoRA inference on Groq, you can:

* **Run inference** with your pre-made LoRA adapters
* **Deploy multiple specialized adapters** alongside a single base model
* **Maintain high performance** without compromising inference speed
* **Leverage existing fine-tuned models** created with external tools

## [Enterprise Feature](#enterprise-feature)

LoRA is available exclusively to enterprise-tier customers. To get started with LoRA on GroqCloud, please reach out to [our enterprise team](https://groq.com/enterprise-access).

## [Why LoRA vs. Base Model?](#why-lora-vs-base-model)

Compared to using just the base model, LoRA adapters offer significant advantages:

* **Task-Specific Optimization**: Tune model outputs to your particular use case, enabling increased accuracy and quality of responses
* **Domain Expertise**: Adapt models to understand industry-specific terminology, context, and requirements
* **Consistent Behavior**: Ensure predictable outputs that align with your business needs and brand voice
* **Performance Maintenance**: Achieve customization without compromising the high-speed inference that Groq is known for

### [Why LoRA vs. Traditional Fine-tuning?](#why-lora-vs-traditional-finetuning)

LoRA provides several key advantages over traditional fine-tuning approaches:

**Lower Total Cost of Ownership**

LoRA reduces fine-tuning costs significantly by avoiding full base model fine-tuning. This efficiency makes it cost-effective to customize models at scale.

**Rapid Deployment with High Performance**

Smaller, task-specific LoRA adapters can match or exceed the performance of fully fine-tuned models while delivering faster inference. This translates to quicker experimentation, iteration, and real-world impact.

**Non-Invasive Model Adaptation**

Since LoRA adapters don't require changes to the base model, you avoid the complexity and liability of managing and validating a fully retrained system. Adapters are modular, independently versioned, and easily replaceable as your data evolves—simplifying governance and compliance.

**Full Control, Less Risk**

Customers keep control of how and when updates happen—no retraining, no surprise behavior changes. Just lightweight, swappable adapters that fit into existing systems with minimal disruption. And with self-service APIs, updating adapters is quick, intuitive, and doesn't require heavy engineering lift.

## [LoRA Options on GroqCloud](#lora-options-on-groqcloud)

### [Two Hosting Modalities](#two-hosting-modalities)

Groq supports LoRAs through two deployment options:

1. [LoRAs in our public cloud](#loras-public-cloud)
2. [LoRAs on a dedicated instance](#loras-dedicated-instance)

### [LoRAs (Public Cloud)](#loras-public-cloud)

Pay-per-token usage model with no dedicated hardware requirements, ideal for customers with a small number of LoRA adapters across different tasks like customer support, document summarization, and translation.

* No dedicated hardware requirements - pay per token usage
* Shared instance capabilities across customers with potential rate limiting
* Less consistent latency/throughput compared to dedicated instances
* Gradual rollout to enterprise customers only via [enterprise access form](https://groq.com/enterprise-access/)

### [LoRAs (Dedicated Instance)](#loras-dedicated-instance)

Deployed on dedicated Groq hardware instances purchased by the customer, providing optimized performance for multiple LoRA adapters and consistent inference speeds, best suited for high-traffic scenarios or customers serving personalized adapters to many end users.

* Dedicated hardware instances optimized for LoRA performance
* More consistent performance and lower average latency
* No LoRA-specific rate limiting
* Ideal for SaaS platforms with dozens of internal use cases or hundreds of customer-specific adapters

### [Supported Models](#supported-models)

LoRA support is currently available for the following models:

| Model ID             | Model                                            | Base Model                                                                                  |
| -------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| llama-3.1-8b-instant | [Llama 3.1 8B](https://console.groq.com/docs/model/llama-3.1-8b-instant) | [meta-llama/Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) |

Please reach out to our [enterprise support team](https://groq.com/enterprise-access) for additional model support.

## [LoRA Pricing](#lora-pricing)

Please reach out to our [enterprise support team](https://groq.com/enterprise-access) for pricing.

## [Getting Started](#getting-started)

To begin using LoRA on GroqCloud:

1. **Contact Enterprise Sales**: [Reach out](https://groq.com/enterprise-access) to become an enterprise-tier customer
2. **Request LoRA Access**: Inform the team that you would like access to LoRA support
3. **Create Your LoRA Adapters**: Use external providers or tools to fine-tune Groq-supported base models (exact model versions required)
4. **Upload Adapters**: Use the self-serve portal to upload your LoRA adapters to GroqCloud
5. **Deploy**: Call the unique model ID created for your specific LoRA adapter(s)

**Important**: You must fine-tune the exact base model versions that Groq supports for your LoRA adapters to work properly.

## [Using the Fine-Tuning API](#using-the-finetuning-api)

Once you have access to LoRA, you can upload and deploy your adapters using Groq's Fine-Tuning API. This process involves two API calls: one to upload your LoRA adapter files and another to register them as a fine-tuned model. When you upload your LoRA adapters, Groq will store and process your files to provide this service. LoRA adapters are your Customer Data and will only be available for your organization's use.

### [Requirements](#requirements)

* **Supported models**: Text generation models only
* **Supported ranks**: 8, 16, 32, and 64 only
* **File format**: ZIP file containing exactly 2 files

**Note**: Cold start times are proportional to the LoRA rank. Higher ranks (32, 64) will take longer to load initially but have no impact on inference performance once loaded.

### [Step 1: Prepare Your LoRA Adapter Files](#step-1-prepare-your-lora-adapter-files)

Create a ZIP file containing exactly these 2 files:

1. **`adapter_model.safetensors`** \- A safetensors file containing your LoRA weights in float16 format
2. **`adapter_config.json`** \- A JSON configuration file with required fields:  
   * `"lora_alpha"`: (integer or float) The LoRA alpha parameter  
   * `"r"`: (integer) The rank of your LoRA adapter (must be 8, 16, 32, or 64)

### [Step 2: Upload the LoRA Adapter Files](#step-2-upload-the-lora-adapter-files)

Upload your ZIP file to the `/files` endpoint with `purpose="fine_tuning"`:

curl

```
curl --location 'https://api.groq.com/openai/v1/files' \
--header "Authorization: Bearer ${TOKEN}" \
--form "file=@<file-name>.zip" \
--form 'purpose="fine_tuning"'
```

This returns a file ID that you'll use in the next step:

JSON

```
{
  "id": "file_01jxnqc8hqebx343rnkyxw47e",
  "object": "file",
  "bytes": 155220077,
  "created_at": 1749854594,
  "filename": "<file-name>.zip",
  "purpose": "fine_tuning"
}
```

### [Step 3: Register as Fine-Tuned Model](#step-3-register-as-finetuned-model)

Use the file ID to register your LoRA adapter as a fine-tuned model:

curl

```
curl --location 'https://api.groq.com/v1/fine_tunings' \
--header 'Content-Type: application/json' \
--header "Authorization: Bearer ${TOKEN}" \
--data '{
    "input_file_id": "<file-id>",
    "name": "my-lora-adapter",
    "type": "lora",
    "base_model": "llama-3.1-8b-instant"
}'
```

This returns your unique model ID:

JSON

```
{
  "id": "ft_01jxx7abvdf6pafdthfbfmb9gy",
  "object": "fine_tuning",
  "data": {
    "name": "my-lora-adapter",
    "base_model": "llama-3.1-8b-instant",
    "type": "lora",
    "fine_tuned_model": "ft:llama-3.1-8b-instant:org_01hqed9y3fexcrngzqm9qh6ya9/my-lora-adapter-ef36419a0010"
  }
}
```

### [Step 4: Use Your LoRA Model](#step-4-use-your-lora-model)

Use the returned `fine_tuned_model` ID in your inference requests just like any other model:

curl

```
curl --location 'https://api.groq.com/openai/v1/chat/completions' \
--header 'Content-Type: application/json' \
--header "Authorization: Bearer ${TOKEN}" \
--data '{
    "model": "ft:llama-3.1-8b-instant:org_01hqed9y3fexcrngzqm9qh6ya9/my-lora-adapter-ef36419a0010",
    "messages": [
        {
            "role": "user",
            "content": "Your prompt here"
        }
    ]
}'
```

## [Frequently Asked Questions](#frequently-asked-questions)

### [Does Groq offer LoRA fine-tuning services?](#does-groq-offer-lora-finetuning-services)

No. Groq provides LoRA inference services only. Customers must create their LoRA adapters externally using fine-tuning providers or tools (e.g., Hugging Face PEFT, Unsloth, or custom solutions) and then upload their pre-made adapters to Groq for inference. You must fine-tune the exact base model versions that Groq supports.

### [Will LoRA support be available to Developer tier customers?](#will-lora-support-be-available-to-developer-tier-customers)

Not at this time. LoRA support is currently exclusive to enterprise tier customers. Stay tuned for updates.

### [Does Groq have recommended fine-tuning providers?](#does-groq-have-recommended-finetuning-providers)

Stay tuned for further updates on recommended fine-tuning providers.

### [How do I get access to LoRA on GroqCloud?](#how-do-i-get-access-to-lora-on-groqcloud)

[Contact our enterprise team](https://groq.com/enterprise-access) to discuss your LoRA requirements and get started.

### [How long are LoRA adapter files retained for?](#how-long-are-lora-adapter-files-retained-for)

Your uploaded LoRA adapter files are stored and accessible solely to your organization for the entire time you use the LoRAs service. This service is not available currently for use with regional / sovereign endpoints.

## [Best Practices](#best-practices)

* **Keep LoRA rank low (8 or 16)** to minimize cold start times - higher ranks increase loading latency
* **Use float16 precision** when loading the base model during fine-tuning to maintain optimal inference accuracy
* **Avoid 4-bit quantization** during LoRA training as it may cause small accuracy drops during inference
* **Save LoRA weights in float16 format** in your `adapter_model.safetensors` file
* **Test different ranks** to find the optimal balance between adaptation quality and cold start performance
