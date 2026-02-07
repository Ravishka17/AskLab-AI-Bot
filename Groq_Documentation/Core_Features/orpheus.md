---
description: Generate expressive speech audio from text using Orpheus v1 models with vocal directions support - available in English and Arabic Saudi dialect.
title: Orpheus Text to Speech - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Orpheus Text to Speech

Generate expressive, natural-sounding speech with vocal direction controls for dynamic audio output.

## [Overview](#overview)

Orpheus text-to-speech models by [Canopy Labs](https://canopylabs.ai/) provide fast, high-quality audio generation with unique expressive capabilities. Both models offer multiple voices and low-latency inference, with the English model supporting [vocal direction controls](#vocal-directions) for expressive performances.

## [Supported Models](#supported-models)

Groq hosts two specialized Orpheus models for different language needs:

| Model ID                                                                       | Description                                   | Language       | Vocal Directions |
| ------------------------------------------------------------------------------ | --------------------------------------------- | -------------- | ---------------- |
| [canopylabs/orpheus-v1-english](https://console.groq.com/docs/model/canopylabs/orpheus-v1-english)     | Expressive English TTS with direction support | English        | ✅ Supported      |
| [canopylabs/orpheus-arabic-saudi](https://console.groq.com/docs/model/canopylabs/orpheus-arabic-saudi) | Authentic Saudi dialect synthesis             | Arabic (Saudi) | ❌ Not Supported  |

## [Pricing](#pricing)

| Model ID                        | Price                      |
| ------------------------------- | -------------------------- |
| canopylabs/orpheus-v1-english   | $22 / 1 million characters |
| canopylabs/orpheus-arabic-saudi | $40 / 1 million characters |

## [API Endpoint](#api-endpoint)

| Endpoint | Usage                 | API Endpoint                                |
| -------- | --------------------- | ------------------------------------------- |
| Speech   | Convert text to audio | https://api.groq.com/openai/v1/audio/speech |

## [Quick Start](#quick-start)

The speech endpoint accepts these parameters:

| Parameter        | Type   | Required | Description                                                                                                |
| ---------------- | ------ | -------- | ---------------------------------------------------------------------------------------------------------- |
| model            | string | Yes      | Model ID: canopylabs/orpheus-v1-english or canopylabs/orpheus-arabic-saudi                                 |
| input            | string | Yes      | Text to convert to speech (max 200 characters). Use \[directions\] for [vocal control](#vocal-directions). |
| voice            | string | Yes      | Voice persona ID to use (see [Available Voices](#available-voices))                                        |
| response\_format | string | Optional | Audio format. Defaults to "wav". The only supported format is "wav".                                       |

## [Basic Usage](#basic-usage)

EnglishArabic Saudi Dialect

### [English Model](#english-model)

Python

```
# Install the Groq SDK:
# pip install groq

# English Model Example:
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
// Install the Groq SDK:
// npm install --save groq-sdk

// English Model Example:
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

### [Arabic Saudi Dialect Model](#arabic-saudi-dialect-model)

Python

```
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

speech_file_path = "orpheus-arabic.wav" 
model = "canopylabs/orpheus-arabic-saudi"
voice = "fahad"
text = "مرحبا بكم في نموذج أورفيوس للتحويل من النص إلى الكلام. هذا مثال على جودة الصوت العربية السعودية الطبيعية."
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

const speechFilePath = "orpheus-arabic.wav";
const model = "canopylabs/orpheus-arabic-saudi";
const voice = "lulwa";
const text = "مرحبا بكم في نموذج أورفيوس للتحويل من النص إلى الكلام. هذا مثال على جودة الصوت العربية السعودية الطبيعية.";
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
  
  console.log(`Orpheus Arabic speech generated: ${speechFilePath}`);
}

main().catch((error) => {
  console.error('Error generating Arabic speech:', error);
});
```

```
curl https://api.groq.com/openai/v1/audio/speech \
  -X POST \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "canopylabs/orpheus-arabic-saudi",
    "input": "مرحبا بكم في نموذج أورفيوس للتحويل من النص إلى الكلام. هذا مثال على جودة الصوت العربية السعودية الطبيعية.",
    "voice": "noura",
    "response_format": "wav"
  }' \
  --output orpheus-arabic.wav
```

## [Vocal Directions](#vocal-directions)

Orpheus V1 English supports **vocal directions** using bracketed text like `[cheerful]` or `[whisper]` to control how the model speaks. This powerful feature enables everything from subtle conversational nuances to highly expressive character performances.

### [How Directions Work](#how-directions-work)

* **More directions** \= more expressive, acted performance
* **Fewer/no directions** \= natural, casual conversational cadence
* Use 1-2 word directions (typically adjectives or adverbs)
  
**Common use cases:**

* **Customer support**: Use no directions for natural, friendly conversations
* **Game characters**: Add expressive directions for dynamic, performative speech
* **Professional narration**: Use `[professionally]` or `[authoritatively]` for business content
* **Storytelling**: Combine multiple directions to create engaging narrative performances

### [Direction Examples](#direction-examples)

**Conversational tones:**

* `[cheerful]`, `[friendly]`, `[casual]`, `[warm]`

**Professional styles:**

* `[professionally]`, `[authoritatively]`, `[formally]`, `[confidently]`

**Expressive performance:**

* `[whisper]`, `[excited]`, `[dramatic]`, `[deadpan]`, `[sarcastic]`

**Vocal qualities:**

* `[gravelly whisper]`, `[rapid babbling]`, `[singsong]`, `[breathy]`

**Note:** There isn't an official or exhaustive list of directions; the model recognizes many natural descriptors and ignores vague or unfamiliar ones.

## [Using Vocal Directions](#using-vocal-directions)

Natural ConversationExpressive PerformanceCombining Directions

### [Natural Conversation (No Directions)](#natural-conversation-no-directions)

For customer support, AI assistants, or natural dialogue, omit directions entirely. The model defaults to conversational, human-like cadence.

* **Example (Troy):** _"I see you ordered the Bose QuietComfort Ultra earbuds, order number 7829-XK-441, tracking ID H3J7L9C2F5V8, and yeah it looks like it's been stuck in transit since, uhh, Thursday the 8th."_
* **Example (Autumn):** _"Okay so I'm looking at your account here and it shows you've got the Dell XPS 15 9530, is that right? Let me just pull up the warranty info real quick... yep that all looks good!"_

**Tip:** Pure numbers like `203` are normalized to "two hundred and three." Use hyphens (`2-0-3`) for letter-by-letter reading.

### [Expressive Performance (With Directions)](#expressive-performance-with-directions)

Add bracketed directions for more dynamic, acted performances. Great for storytelling, game characters, or engaging content.

* _"**\[cheerful singsong\]** Good morning, everyone, and welcome to another beautiful day! **\[dropping tone\]** Now, let's talk about the budget cuts happening next month."_
* _"She picked up the phone and immediately started **\[rapid babbling\]** oh my god you won't believe what just happened I have to tell you everything right now."_
* _"**\[gravelly whisper\]** Legend has it that anyone who enters those woods after dark never comes back quite the same as they were before."_
* _"**\[piercing shout\]** Will someone please answer that phone it has been ringing nonstop **\[exasperated sigh\]** for the last twenty minutes straight!"_
* _"**\[mock sympathy\]** Oh no how terrible that must be for you **\[deadpan\]** anyway let me tell you about my actual problems this week."_

### [Combining Directions](#combining-directions)

You can use multiple directions in a single sentence to create dynamic performances:

* _"**\[building intensity\]** And then the car started making this noise, and the smoke was everywhere, and— **\[crescendo\]** the whole engine just exploded right there!"_
* _"**\[slurring slightly\]** I probably shouldn't have had that last glass of wine, but honestly— **\[giggling\]** this party is way more fun than I expected!"_
* _"The auctioneer rattled off **\[fast paced\]** fifty do I hear fifty-five fifty-five now sixty sixty going once going twice sold to the woman in red!"_

## [Available Voices](#available-voices)

### [English Voices](#english-voices)

The English model includes six professionally-trained voice personas. Each voice has different strengths for expressive direction performance.

| Voice Name | Voice ID | Gender |
| ---------- | -------- | ------ |
| Autumn     | autumn   | Female |
| Diana      | diana    | Female |
| Hannah     | hannah   | Female |
| Austin     | austin   | Male   |
| Daniel     | daniel   | Male   |
| Troy       | troy     | Male   |

  
**Note:** Some voices perform better with expressive directions than others. Experiment to find the voice that works best for your use case.

AutumnDianaHannahAustinDanielTroy

Autumn

0:000:00

Diana

0:000:00

Hannah

0:000:00

Austin

0:000:00

Daniel

0:000:00

Troy

0:000:00

### [Arabic Saudi Dialect Voices](#arabic-saudi-dialect-voices)

The Arabic model offers four distinct Saudi dialect voices with authentic pronunciation and regional nuances:

| Voice Name | Voice ID | Gender |
| ---------- | -------- | ------ |
| Fahad      | fahad    | Male   |
| Sultan     | sultan   | Male   |
| Lulwa      | lulwa    | Female |
| Noura      | noura    | Female |

FahadSultanLulwaNoura

Fahad

0:000:00

Sultan

0:000:00

Lulwa

0:000:00

Noura

0:000:00

## [Use Cases](#use-cases)

Customer SupportGame CharactersProfessional NarrationContent Creation

### [Customer Support & AI Assistants](#customer-support--ai-assistants)

Use **no directions** for natural, conversational interactions that feel human and approachable.

* _"I'm looking at your account here and everything seems to be in order. Let me just check that shipping status for you real quick."_

**Best for:** Customer service bots, virtual assistants, FAQ systems

### [Game Characters & Interactive Media](#game-characters--interactive-media)

Use **expressive directions** to create memorable, dynamic character performances.

* _"**\[menacing whisper\]** You shouldn't have come here... **\[dark chuckle\]** but now that you have, let's see what you're made of."_

**Best for:** Video games, interactive storytelling, virtual worlds

### [Professional Narration & Business Content](#professional-narration--business-content)

Use **subtle professional directions** for authoritative, polished delivery.

* _"**\[professionally\]** Welcome to our quarterly earnings call. Today we'll review our performance and outline strategic initiatives for the coming quarter."_

**Best for:** Corporate videos, e-learning, business presentations

### [Content Creation & Entertainment](#content-creation--entertainment)

Combine **multiple directions** for engaging, varied performances.

* _"**\[excited\]** So you won't believe what happened next! **\[building suspense\]** The door slowly creaked open and— **\[dramatic gasp\]** there it was!"_

**Best for:** Podcasts, audiobooks, YouTube content, storytelling

## [Best Practices](#best-practices)

**Punctuation control:** Experiment with removing punctuation to give the model more freedom in choosing intonation patterns, especially for expressive performances.

**Voice selection:** Test different voices for your use case; some handle expressive directions better than others, particularly for complex emotional ranges.

**Arabic considerations:** Use proper Arabic script with diacritical marks. Test pronunciation with sample content before production deployment.

## [Limitations](#limitations)

**Input length:** The input text length is limited to 200 characters.

**Batch processing:** The [batch processing API](https://console.groq.com/docs/batch) is not supported at this time for Orpheus models.
