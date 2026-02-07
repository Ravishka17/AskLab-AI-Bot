---
description: Learn how to process large-scale workloads asynchronously and cost-effectively with the Groq Batch API for chat, audio, and translation tasks.
title: Groq Batch API - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Groq Batch API

Process large-scale workloads asynchronously with our Batch API.

## [What is Batch Processing?](#what-is-batch-processing)

Batch processing lets you run thousands of API requests at scale by submitting your workload as an asynchronous batch of requests to Groq with 50% lower cost, no impact to your standard rate limits, and 24-hour to 7 day processing window.

## [Overview](#overview)

While some of your use cases may require synchronous API requests, asynchronous batch processing is perfect for use cases that don't need immediate reponses or for processing a large number of queries that standard rate limits cannot handle, such as processing large datasets, generating content in bulk, and running evaluations.

Compared to using our synchronous API endpoints, our Batch API has:

* **Higher rate limits:** Process thousands of requests per batch with no impact on your standard API rate limits
* **Cost efficiency:** 50% cost discount compared to synchronous APIs

## [Model Availability and Pricing](#model-availability-and-pricing)

The Batch API can currently be used to execute queries for chat completion (both text and vision), audio transcription, and audio translation inputs with the following models:

Chat CompletionsAudio TranscriptionsAudio Translations

| Model ID                                      | Model                                                                         |
| --------------------------------------------- | ----------------------------------------------------------------------------- |
| openai/gpt-oss-20b                            | [GPT-OSS 20B](https://console.groq.com/docs/model/openai/gpt-oss-20b)                                 |
| openai/gpt-oss-120b                           | [GPT-OSS 120B](https://console.groq.com/docs/model/openai/gpt-oss-120b)                               |
| meta-llama/llama-4-maverick-17b-128e-instruct | [Llama 4 Maverick](https://console.groq.com/docs/model/meta-llama/llama-4-maverick-17b-128e-instruct) |
| meta-llama/llama-4-scout-17b-16e-instruct     | [Llama 4 Scout](https://console.groq.com/docs/model/meta-llama/llama-4-scout-17b-16e-instruct)        |
| llama-3.3-70b-versatile                       | [Llama 3.3 70B](https://console.groq.com/docs/model/llama-3.3-70b-versatile)                          |
| llama-3.1-8b-instant                          | [Llama 3.1 8B Instant](https://console.groq.com/docs/model/llama-3.1-8b-instant)                      |
| meta-llama/llama-guard-4-12b                  | [Llama Guard 4 12B](https://console.groq.com/docs/model/meta-llama/llama-guard-4-12b)                 |

| Model ID               | Model                                                        |
| ---------------------- | ------------------------------------------------------------ |
| whisper-large-v3       | [Whisper Large V3](https://console.groq.com/docs/model/whisper-large-v3)             |
| whisper-large-v3-turbo | [Whisper Large V3 Turbo](https://console.groq.com/docs/model/whisper-large-v3-turbo) |

| Model ID         | Model                                            |
| ---------------- | ------------------------------------------------ |
| whisper-large-v3 | [Whisper Large V3](https://console.groq.com/docs/model/whisper-large-v3) |

Pricing is at a 50% cost discount compared to [synchronous API pricing. ](https://groq.com/pricing)

**Note:** The batch discount does not stack with [prompt caching](https://console.groq.com/docs/prompt-caching) discounts. All batch tokens are billed at the 50% batch rate regardless of cache status.

## [Getting Started](#getting-started)

Our Batch API endpoints allow you to collect a group of requests into a single file, kick off a batch processing job to execute the requests within your file, query for the status of your batch, and eventually retrieve the results when your batch is complete.

Multiple batch jobs can be submitted at once.

Each batch has a processing window, during which we'll process as many requests as our capacity allows while maintaining service quality for all users. We allow for setting a batch window from 24 hours to 7 days and recommend setting a longer batch window allow us more time to complete your batch jobs instead of expiring them.

### [1\. Prepare Your Batch File](#1-prepare-your-batch-file)

A batch is composed of a list of API requests and every batch job starts with a JSON Lines (JSONL) file that contains the requests you want processed. Each line in this file represents a single API call.

The Groq Batch API currently supports:

* Chat completion requests through [/v1/chat/completions](https://console.groq.com/docs/text-chat)
* Audio transcription requests through [/v1/audio/transcriptions](https://console.groq.com/docs/speech-to-text)
* Audio translation requests through [/v1/audio/translations](https://console.groq.com/docs/speech-to-text)

The structure for each line must include:

* `custom_id`: Your unique identifier for tracking the batch request
* `method`: The HTTP method (currently `POST` only)
* `url`: The API endpoint to call (one of: `/v1/chat/completions`, `/v1/audio/transcriptions`, or `/v1/audio/translations`)
* `body`: The parameters of your request matching our synchronous API format. See our API Reference [here. ](https://console.groq.com/docs/api-reference#chat-create)

The following is an example of a JSONL batch file with different types of requests:

Chat CompletionsAudio TranscriptionsAudio TranslationsMixed Batch

JSON

```
{"custom_id": "request-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "llama-3.1-8b-instant", "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "What is 2+2?"}]}}
{"custom_id": "request-2", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "llama-3.1-8b-instant", "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "What is 2+3?"}]}}
{"custom_id": "request-3", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "llama-3.1-8b-instant", "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "count up to 1000000. starting with 1, 2, 3. print all the numbers, do not stop until you get to 1000000."}]}}
```

JSON

```
{"custom_id":"job-cb6d01f6-1","method":"POST","url":"/v1/audio/transcriptions","body":{"model":"whisper-large-v3","language":"en","url":"https://github.com/voxserv/audio_quality_testing_samples/raw/refs/heads/master/testaudio/8000/test01_20s.wav","response_format":"verbose_json","timestamp_granularities":["segment"]}}
{"custom_id":"job-cb6d01f6-2","method":"POST","url":"/v1/audio/transcriptions","body":{"model":"whisper-large-v3","language":"en","url":"https://github.com/voxserv/audio_quality_testing_samples/raw/refs/heads/master/testaudio/8000/test01_20s.wav","response_format":"verbose_json","timestamp_granularities":["segment"]}}
{"custom_id":"job-cb6d01f6-3","method":"POST","url":"/v1/audio/transcriptions","body":{"model":"distil-whisper-large-v3-en","language":"en","url":"https://github.com/voxserv/audio_quality_testing_samples/raw/refs/heads/master/testaudio/8000/test01_20s.wav","response_format":"verbose_json","timestamp_granularities":["segment"]}}
```

JSON

```
{"custom_id":"job-cb6d01f6-1","method":"POST","url":"/v1/audio/translations","body":{"model":"whisper-large-v3","language":"en","url":"https://console.groq.com/audio/batch/sample-zh.wav","response_format":"verbose_json","timestamp_granularities":["segment"]}}
```

JSON

```
{"custom_id": "chat-request-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "llama-3.1-8b-instant", "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "What is quantum computing?"}]}}
{"custom_id": "audio-request-1", "method": "POST", "url": "/v1/audio/transcriptions", "body": {"model": "whisper-large-v3", "language": "en", "url": "https://github.com/voxserv/audio_quality_testing_samples/raw/refs/heads/master/testaudio/8000/test01_20s.wav", "response_format": "verbose_json", "timestamp_granularities": ["segment"]}}
{"custom_id": "chat-request-2", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Explain machine learning in simple terms."}]}}
{"custom_id":"audio-request-2","method":"POST","url":"/v1/audio/translations","body":{"model":"whisper-large-v3","language":"en","url":"https://console.groq.com/audio/batch/sample-zh.wav","response_format":"verbose_json","timestamp_granularities":["segment"]}}
```

#### [Converting Sync Calls to Batch Format](#converting-sync-calls-to-batch-format)

If you're familiar with making synchronous API calls, converting them to batch format is straightforward. Here's how a regular API call transforms into a batch request:

Chat CompletionsAudio TranscriptionsAudio Translations

JSON

```
# Your typical synchronous API call in Python:
response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "user", "content": "What is quantum computing?"}
    ]
)

# The same call in batch format (must be on a single line as JSONL):
{"custom_id": "quantum-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "What is quantum computing?"}]}}
```

JSON

```
# Your typical synchronous API call in Python:
response = client.audio.transcriptions.create(
    model="whisper-large-v3",
    language="en",
    url="https://example.com/audio-file.wav",
    response_format="verbose_json",
    timestamp_granularities=["segment"]
)

# The same call in batch format (must be on a single line as JSONL):
{"custom_id": "audio-1", "method": "POST", "url": "/v1/audio/transcriptions", "body": {"model": "whisper-large-v3", "language": "en", "url": "https://example.com/audio-file.wav", "response_format": "verbose_json", "timestamp_granularities": ["segment"]}}
```

JSON

```
# Your typical synchronous API call in Python:
response = client.audio.translations.create(
    model="whisper-large-v3",
    language="en",
    url="https://example.com/audio-file.wav",
    response_format="verbose_json",
    timestamp_granularities=["segment"]
)

# The same call in batch format (must be on a single line as JSONL):
{"custom_id": "audio-1", "method": "POST", "url": "/v1/audio/translations", "body": {"model": "whisper-large-v3", "language": "en", "url": "https://example.com/audio-file.wav", "response_format": "verbose_json", "timestamp_granularities": ["segment"]}}
```

### [2\. Upload Your Batch File](#2-upload-your-batch-file)

Upload your `.jsonl` batch file using the Files API endpoint for when kicking off your batch job:

**Note:** The Files API currently only supports `.jsonl` files 50,000 lines or less and up to maximum of 200MB in size. There is no limit for the number of batch jobs you can submit. We recommend submitting multiple shorter batch files for a better chance of completion.

Python

```
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

file_path = "batch_file.jsonl"
response = client.files.create(file=open(file_path, "rb"), purpose="batch")

print(response)
```

```
import fs from 'fs';
import Groq from 'groq-sdk';

const groq = new Groq();

async function main() {
  const filePath = 'batch_file.jsonl'; // Path to your JSONL file

  const response = await groq.files.create({
    purpose: 'batch',
    file: fs.createReadStream(filePath)
  });

  console.log(response);
}

main();
```

```
curl https://api.groq.com/openai/v1/files \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -F purpose="batch" \
  -F "file=@batch_file.jsonl"
```

You will receive a JSON response that contains the ID (`id`) for your file object that you will then use to create your batch job:

JSON

```
{
    "id":"file_01jh6x76wtemjr74t1fh0faj5t",
    "object":"file",
    "bytes":966,
    "created_at":1736472501,
    "filename":"input_file.jsonl",
    "purpose":"batch"
}
```

### [3\. Create Your Batch Job](#3-create-your-batch-job)

Once you've uploaded your `.jsonl` file, you can use the file object ID (in this case, `file_01jh6x76wtemjr74t1fh0faj5t` as shown in Step 2) to create a batch:

**Note:** The completion window for batch jobs can be set from to 24 hours (`24h`) to 7 days (`7d`). We recommend setting a longer batch window to have a better chance for completed batch jobs rather than expirations for when we are under heavy load.

Python

```
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

response = client.batches.create(
    completion_window="24h",
    endpoint="/v1/chat/completions",
    input_file_id="file_01jh6x76wtemjr74t1fh0faj5t",
)
print(response.to_json())
```

```
import Groq from 'groq-sdk';

const groq = new Groq();

async function main() {
  const response = await groq.batches.create({
    completion_window: "24h",
    endpoint: "/v1/chat/completions",
    input_file_id: "file_01jh6x76wtemjr74t1fh0faj5t",
  });
  console.log(response);
}

main();
```

```
curl https://api.groq.com/openai/v1/batches \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input_file_id": "file_01jh6x76wtemjr74t1fh0faj5t",
    "endpoint": "/v1/chat/completions",
    "completion_window": "24h"
  }'
```

This request will return a Batch object with metadata about your batch, including the batch `id` that you can use to check the status of your batch:

JSON

```
{
    "id":"batch_01jh6xa7reempvjyh6n3yst2zw",
    "object":"batch",
    "endpoint":"/v1/chat/completions",
    "errors":null,
    "input_file_id":"file_01jh6x76wtemjr74t1fh0faj5t",
    "completion_window":"24h",
    "status":"validating",
    "output_file_id":null,
    "error_file_id":null,
    "finalizing_at":null,
    "failed_at":null,
    "expired_at":null,
    "cancelled_at":null,
    "request_counts":{
        "total":0,
        "completed":0,
        "failed":0
    },
    "metadata":null,
    "created_at":1736472600,
    "expires_at":1736559000,
    "cancelling_at":null,
    "completed_at":null,
    "in_progress_at":null
}
```

### [4\. Check Batch Status](#4-check-batch-status)

You can check the status of a batch any time your heart desires with the batch `id` (in this case, `batch_01jh6xa7reempvjyh6n3yst2zw` from the above Batch response object), which will also return a Batch object:

Python

```
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

response = client.batches.retrieve("batch_01jh6xa7reempvjyh6n3yst2zw")

print(response.to_json())
```

```
import Groq from 'groq-sdk';

const groq = new Groq();

async function main() {
  const response = await groq.batches.retrieve("batch_01jh6xa7reempvjyh6n3yst2zw");
  console.log(response);
}

main();
```

```
curl https://api.groq.com/openai/v1/batches/batch_01jh6xa7reempvjyh6n3yst2zw \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json"
```

The status of a given batch job can return any of the following status codes:

| Status       | Description                                                                |
| ------------ | -------------------------------------------------------------------------- |
| validating   | batch file is being validated before the batch processing begins           |
| failed       | batch file has failed the validation process                               |
| in\_progress | batch file was successfully validated and the batch is currently being run |
| finalizing   | batch has completed and the results are being prepared                     |
| completed    | batch has been completed and the results are ready                         |
| expired      | batch was not able to be completed within the processing window            |
| cancelling   | batch is being cancelled (may take up to 10 minutes)                       |
| cancelled    | batch was cancelled                                                        |

When your batch job is complete, the Batch object will return an `output_file_id` and/or an `error_file_id` that you can then use to retrieve your results (as shown below in Step 5). Here's an example:

JSON

```
{
    "id":"batch_01jh6xa7reempvjyh6n3yst2zw",
    "object":"batch",
    "endpoint":"/v1/chat/completions",
    "errors":[
        {
            "code":"invalid_method",
            "message":"Invalid value: 'GET'. Supported values are: 'POST'","param":"method",
            "line":4
        }
    ],
    "input_file_id":"file_01jh6x76wtemjr74t1fh0faj5t",
    "completion_window":"24h",
    "status":"completed",
    "output_file_id":"file_01jh6xa97be52b7pg88czwrrwb",
    "error_file_id":"file_01jh6xa9cte52a5xjnmnt5y0je",
    "finalizing_at":null,
    "failed_at":null,
    "expired_at":null,
    "cancelled_at":null,
    "request_counts":
    {
        "total":3,
        "completed":2,
        "failed":1
    },
    "metadata":null,
    "created_at":1736472600,
    "expires_at":1736559000,
    "cancelling_at":null,
    "completed_at":1736472607,
    "in_progress_at":1736472601
}
```

### [5\. Retrieve Batch Results](#5-retrieve-batch-results)

Now for the fun. Once the batch is complete, you can retrieve the results using the `output_file_id` from your Batch object (in this case, `file_01jh6xa97be52b7pg88czwrrwb` from the above Batch response object) and write it to a file on your machine (`batch_output.jsonl` in this case) to view them:

Python

```
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

response = client.files.content("file_01jh6xa97be52b7pg88czwrrwb")
response.write_to_file("batch_results.jsonl")
print("Batch file saved to batch_results.jsonl")
```

```
import fs from 'fs';
import Groq from 'groq-sdk';

const groq = new Groq();

async function main() {
  const response = await groq.files.content("file_01jh6xa97be52b7pg88czwrrwb");
  fs.writeFileSync("batch_results.jsonl", await response.text());
  console.log("Batch file saved to batch_results.jsonl");
}

main();
```

```
curl https://api.groq.com/openai/v1/files/file_01jh6xa97be52b7pg88czwrrwb/content \
  -H "Authorization: Bearer $GROQ_API_KEY" > batch_output.jsonl
```

The output `.jsonl` file will have one response line per successful request line of your batch file. Each line includes the original `custom_id`for mapping results, a unique batch request ID, and the response:

JSON

```
{"id": "batch_req_123", "custom_id": "my-request-1", "response": {"status_code": 200, "request_id": "req_abc", "body": {"id": "completion_xyz", "model": "llama-3.1-8b-instant", "choices": [{"index": 0, "message": {"role": "assistant", "content": "Hello!"}}], "usage": {"prompt_tokens": 20, "completion_tokens": 5, "total_tokens": 25}}}, "error": null}
```

Any failed or expired requests in the batch will have their error information written to an error file that can be accessed via the batch's `error_file_id`.

**Note:** Results may not appears in the same order as your batch request submissions. Always use the `custom_id` field to match results with your original request.

## [List Batches](#list-batches)

The `/batches` endpoint provides two ways to access your batch information: browsing all batches with cursor-based pagination (using the `cursor` parameter), or fetching specific batches by their IDs.

### [Iterate Over All Batches](#iterate-over-all-batches)

You can view all your batch jobs by making a call to `https://api.groq.com/openai/v1/batches`. Use the `cursor` parameter with the `next_cursor` value from the previous response to get the next page of results:

Python

```
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Initial request - gets first page of batches
response = client.batches.list()
print("First page:", response)

# If there's a next cursor, use it to get the next page
if response.paging and response.paging.get("next_cursor"):
    next_response = client.batches.list(
        extra_query={
            "cursor": response.paging.get("next_cursor")
        }  # Use the next_cursor for next page
    )
    print("Next page:", next_response)
```

```
import Groq from 'groq-sdk';

const groq = new Groq();

async function main() {
  // Initial request - gets first page of batches
  const response = await groq.batches.list();
  console.log('First page:', response);

  // If there's a next cursor, use it to get the next page
  if (response.paging && response.paging.next_cursor) {
    const nextResponse = await groq.batches.list({
      query: {
        cursor: response.paging.next_cursor, // Use the next_cursor for next page
      },
    });
    console.log('Next page:', nextResponse);
  }
}

main();
```

```
# Initial request - gets first page of batches
curl "https://api.groq.com/openai/v1/batches" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json"

# Use the next_cursor from the paging object in the response above
# Replace 'cursor_abc123' with the actual next_cursor from your previous response
curl "https://api.groq.com/openai/v1/batches?cursor=cursor_abc123" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json"
```

The paginated response includes a `paging` object with the `next_cursor` for the next page:

JSON

```
{
  "object": "list",
  "data": [
    {
      "id": "batch_01jh6xa7reempvjyh6n3yst111",
      "object": "batch",
      "status": "completed",
      "created_at": 1736472600,
      // ... other batch fields
    }
    // ... more batches
  ],
  "paging": {
    "next_cursor": "cursor_eyJpZCI6ImJhdGNoXzAxamg2eGE3cmVlbXB2ankifQ"
  }
}
```

### [Get Specific Batches](#get-specific-batches)

You can check the status of multiple batches at once by providing multiple batch IDs as query parameters to the same `/batches` endpoint. This is useful when you have submitted multiple batch jobs and want to monitor their progress efficiently:

Python

```
import os
import requests

# Set up headers
headers = {
    "Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}",
    "Content-Type": "application/json",
}

# Define batch IDs to check
batch_ids = [
    "batch_01jh6xa7reempvjyh6n3yst111",
    "batch_01jh6xa7reempvjyh6n3yst222",
    "batch_01jh6xa7reempvjyh6n3yst333",
]

# Build query parameters using requests params
url = "https://api.groq.com/openai/v1/batches"
params = [("id", batch_id) for batch_id in batch_ids]

# Make the request
response = requests.get(url, headers=headers, params=params)
print(response.json())
```

```
async function main() {
  const batchIds = [
    "batch_01jh6xa7reempvjyh6n3yst111",
    "batch_01jh6xa7reempvjyh6n3yst222",
    "batch_01jh6xa7reempvjyh6n3yst333"
  ];

  // Build query parameters using URLSearchParams
  const url = new URL('https://api.groq.com/openai/v1/batches');
  batchIds.forEach(id => url.searchParams.append('id', id));

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${process.env.GROQ_API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    console.log(data);
  } catch (error) {
    console.error('Error:', error);
  }
}

main();
```

```
curl "https://api.groq.com/openai/v1/batches?id=batch_01jh6xa7reempvjyh6n3yst111&id=batch_01jh6xa7reempvjyh6n3yst222&id=batch_01jh6xa7reempvjyh6n3yst333" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json"
```

The multi-batch status request returns a JSON object with a `data` array containing the complete batch information for each requested batch:

JSON

```
{
  "object": "list",
  "data": [
    {
      "id": "batch_01jh6xa7reempvjyh6n3yst111",
      "object": "batch",
      "endpoint": "/v1/chat/completions",
      "errors": null,
      "input_file_id": "file_01jh6x76wtemjr74t1fh0faj5t",
      "completion_window": "24h",
      "status": "validating",
      "output_file_id": null,
      "error_file_id": null,
      "finalizing_at": null,
      "failed_at": null,
      "expired_at": null,
      "cancelled_at": null,
      "request_counts": {
        "total": 0,
        "completed": 0,
        "failed": 0
      },
      "metadata": null,
      "created_at": 1736472600,
      "expires_at": 1736559000,
      "cancelling_at": null,
      "completed_at": null,
      "in_progress_at": null
    },
    {
      "id": "batch_01jh6xa7reempvjyh6n3yst222",
      "object": "batch",
      "endpoint": "/v1/chat/completions",
      "errors": null,
      "input_file_id": "file_01jh6x76wtemjr74t1fh0faj6u",
      "completion_window": "24h",
      "status": "in_progress",
      "output_file_id": null,
      "error_file_id": null,
      "finalizing_at": null,
      "failed_at": null,
      "expired_at": null,
      "cancelled_at": null,
      "request_counts": {
        "total": 100,
        "completed": 15,
        "failed": 0
      },
      "metadata": null,
      "created_at": 1736472650,
      "expires_at": 1736559050,
      "cancelling_at": null,
      "completed_at": null,
      "in_progress_at": 1736472651
    },
    {
      "id": "batch_01jh6xa7reempvjyh6n3yst333",
      "object": "batch",
      "endpoint": "/v1/chat/completions",
      "errors": null,
      "input_file_id": "file_01jh6x76wtemjr74t1fh0faj7v",
      "completion_window": "24h",
      "status": "completed",
      "output_file_id": "file_01jh6xa97be52b7pg88czwrrwc",
      "error_file_id": null,
      "finalizing_at": null,
      "failed_at": null,
      "expired_at": null,
      "cancelled_at": null,
      "request_counts": {
        "total": 50,
        "completed": 50,
        "failed": 0
      },
      "metadata": null,
      "created_at": 1736472700,
      "expires_at": 1736559100,
      "cancelling_at": null,
      "completed_at": 1736472800,
      "in_progress_at": 1736472701
    }
  ]
}
```

**Note:** You can only request up to 200 batch IDs in a single request.

## [Batch Size](#batch-size)

The Files API supports JSONL files up to 50,000 lines and 200MB in size. Multiple batch jobs can be submitted at once.

**Note:** Consider splitting very large workloads into multiple smaller batches (e.g. 1000 requests per batch) for a better chance at completion rather than expiration for when we are under heavy load.

## [Batch Expiration](#batch-expiration)

Each batch has a processing window (24 hours to 7 days) during which we'll process as many requests as our capacity allows while maintaining service quality for all users.

We recommend setting a longer batch window for a better chance of completing your batch job rather than returning expired jobs when we are under heavy load.

Batch jobs that do not complete within their processing window will have a status of `expired`.

In cases where your batch job expires:

* You are only charged for successfully completed requests
* You can access all completed results and see which request IDs were not processed
* You can resubmit any uncompleted requests in a new batch

## [Data Expiration](#data-expiration)

Input, intermediate files, and results from processed batches will be stored securely for up to 30 days in Groq's systems. You may also immediately delete once a processed batch is retrieved.

## [Rate limits](#rate-limits)

The Batch API rate limits are separate than existing per-model rate limits for synchronous requests. Using the Batch API will not consume tokens from your standard per-model limits, which means you can conveniently leverage batch processing to increase the number of tokens you process with us.

See your limits [here. ](https://console.groq.com/settings/limits)
