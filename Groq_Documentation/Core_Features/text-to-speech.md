---
description: Instantly generate lifelike audio from text using Groq&#x27;s fast text-to-speech API with support for multiple voices and languages.
title: Text to Speech - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Text to Speech

Learn how to instantly generate lifelike audio from text.

## [Overview](#overview)

The Groq API speech endpoint provides fast text-to-speech (TTS), enabling you to convert text to spoken audio in seconds. With support for English and Arabic voices, you can create life-like audio content for customer support agents, game characters, narration, and more.

## [API Endpoint](#api-endpoint)

| Endpoint | Usage                 | API Endpoint                                |
| -------- | --------------------- | ------------------------------------------- |
| Speech   | Convert text to audio | https://api.groq.com/openai/v1/audio/speech |

## [Supported Models](#supported-models)

| Model ID                                                                       | Language       | Description                                  |
| ------------------------------------------------------------------------------ | -------------- | -------------------------------------------- |
| [canopylabs/orpheus-v1-english](https://console.groq.com/docs/model/canopylabs/orpheus-v1-english)     | English        | Expressive TTS with vocal direction controls |
| [canopylabs/orpheus-arabic-saudi](https://console.groq.com/docs/model/canopylabs/orpheus-arabic-saudi) | Arabic (Saudi) | Authentic Saudi dialect synthesis            |

## [Quick Start](#quick-start)

The speech endpoint takes four key inputs:

* **model:** `canopylabs/orpheus-v1-english` or `canopylabs/orpheus-arabic-saudi`
* **input:** the text to generate audio from
* **voice:** the desired voice for output
* **response format:** defaults to `"wav"`

Python

```
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

speech_file_path = "orpheus-english.wav" 
model = "canopylabs/orpheus-v1-english"
voice = "troy"
text = "Welcome to Orpheus text-to-speech. [cheerful] This is an example of high-quality English audio generation with vocal directions support."
response_format = "wav"

response = client.audio.speech.create(
    model=model,
    voice=voice,
    input=text,
    response_format=response_format
)

response.write_to_file(speech_file_path)
```

```
import fs from "fs";
import Groq from 'groq-sdk';

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY
});

const speechFilePath = "orpheus-english.wav";
const model = "canopylabs/orpheus-v1-english";
const voice = "hannah";
const text = "Welcome to Orpheus text-to-speech. [cheerful] This is an example of high-quality English audio generation with vocal directions support.";
const responseFormat = "wav";

async function main() {
  const response = await groq.audio.speech.create({
    model: model,
    voice: voice,
    input: text,
    response_format: responseFormat
  });
  
  const buffer = Buffer.from(await response.arrayBuffer());
  await fs.promises.writeFile(speechFilePath, buffer);
  
  console.log(`Orpheus English speech generated: ${speechFilePath}`);
}

main().catch((error) => {
  console.error('Error generating speech:', error);
});
```

```
curl https://api.groq.com/openai/v1/audio/speech \
  -X POST \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "canopylabs/orpheus-v1-english",
    "input": "Welcome to Orpheus text-to-speech. [cheerful] This is an example of high-quality English audio generation with vocal directions support.",
    "voice": "austin",
    "response_format": "wav"
  }' \
  --output orpheus-english.wav
```

## [Next Steps](#next-steps)

For comprehensive documentation on available voices, vocal directions, use cases, and best practices, see the Orpheus documentation:

[Orpheus Text to SpeechLearn about vocal directions, available voices, use cases, and best practices for generating expressive speech](https://console.groq.com/docs/text-to-speech/orpheus)
