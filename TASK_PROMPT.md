# Task: Remove Hard-Coded Keyword Rules and Enable Autonomous Tool Calls

Since the AI is hard-coded with keyword rules, the AI makes errors. Take a look at this

**Prompt:** Who's the current president of Sri Lanka?

**Response:** 
```
🧠 **Thinking...**

> I need to find out who the current president of Sri Lanka is. Since I don't have information after 2023, I'll search Wikipedia for the President of Sri Lanka to get the most up-to-date information.

🔍 **Searching Wikipedia...**

> "President of Sri Lanka"

🧠 **Thinking...**

> Good, I found the "President of Sri Lanka" page. Now I'll read this article to find out who currently holds this position.

📖 **Reading Article...**

> "President of Sri Lanka"

🧠 **Thinking...**

> Perfect! I found that Anura Kumara Dissanayake is the current president, having assumed office on September 23, 2024. Now I need to get more detailed information about him by reading his biographical page.

🧠 **Thinking...**

> I need to get more detailed information about Anura Kumara Dissanayake, the current president of Sri Lanka. I found his name and that he took office on September 23, 2024, but I should read his biographical page to provide comprehensive information about him.

📖 **Reading Article...**

> "Anura Kumara Dissanayake"

The current President of Sri Lanka is **Anura Kumara Dissanayake**.

He assumed office on September 23, 2024, after winning the 2024 presidential election held on September 21, 2024. This historic victory marked several firsts in Sri Lankan politics:

- He became the first Sri Lankan president to be elected through second-preference vote counting (as no candidate received over 50% in the first round)
- He is the first president not from either of the two traditional political parties that have dominated Sri Lankan politics
- He represents a third-party alternative, having previously come in third place in the 2019 presidential election with 3% of the vote

Dissanayake, commonly known by his initials AKD, was born on November 24, 1968. He has a long political career, having served as a member of parliament since 2000 and leading the Janatha Vimukthi Peramuna (JVP) party since 2014. He is also the founding leader of the National People's Power (NPP) alliance, which he established in 2019.

His election represents a significant shift in Sri Lankan politics, as he campaigned on an anti-corruption platform and promises of economic reform during a time when the country has been facing severe economic challenges.

📚 **Sources**

1. [wikipedia.org](https://en.wikipedia.org/wiki/President_of_Sri_Lanka)
2. [wikipedia.org](https://en.wikipedia.org/wiki/Anura_Kumara_Dissanayake)
```

**Prompt:** Who's the current president of Russia?

**Response:**
```
🧠 **Thinking...**

> The user is asking about the current president of Russia. Since I don't have information after 2023, I need to search Wikipedia to find out who is currently serving as president. I'll start by searching for 'President of Russia' to find the current officeholder.

🔍 **Searching Wikipedia...**

> "President of Russia"

🧠 **Thinking...**

> I found the "President of Russia" page. Let me read this article to find out who currently holds this position.

📖 **Reading Article...**

> "President of Russia"

🧠 **Thinking...**

> I can see from the summary that Vladimir Putin is mentioned as becoming the fourth president in May 2012, being re-elected in 2018 and 2024. However, I need to get more current information about his most recent term. Let me search specifically for Vladimir Putin to get his biographical page with the most up-to-date information about his presidency.

📖 **Reading Article...**

> "Vladimir Putin"

🧠 **Thinking...**

> Perfect! I now have comprehensive information about Vladimir Putin. From what I found:

> 1. He has served as President of Russia since 2012 (and previously from 2000-2008)
> 2. He was re-elected in March 2024 for another term
> 3. Constitutional amendments allowed him to run for reelection, potentially extending his presidency to 2036

> I have all the information needed to provide a complete answer about the current president of Russia.

The current President of Russia is **Vladimir Putin**.

He has been serving as president since 2012 (having previously held the office from 2000-2008) and was most recently re-elected in March 2024 for another six-year term. Putin has effectively been the leader of Russia since 2000, making him one of the longest-serving leaders in modern Russian history.

📚 **Sources**

1. [wikipedia.org](https://en.wikipedia.org/wiki/President_of_Russia)
2. [wikipedia.org](https://en.wikipedia.org/wiki/Vladimir_Putin)
```

**Prompt:** Tell me more about him.

**Response:**
```
🧠 **Thinking...**

> I need to search Wikipedia for Vladimir Putin to find his biographical page and get comprehensive information about him.

🧠 **Thinking...**

> I need to search Wikipedia for Vladimir Putin to find his biographical article and gather detailed information about him for the user.

🧠 **Thinking...**

> I need to search Wikipedia for Vladimir Putin to find his biographical page and get comprehensive information about him.

🧠 **Thinking...**

> I need to search Wikipedia for Vladimir Putin to find his biographical page and gather detailed information about him for the user.

🧠 **Thinking...**

> I need to search Wikipedia for Vladimir Putin to find his biographical article and gather detailed information about him.

🧠 **Thinking...**

> I need to search Wikipedia for Vladimir Putin to find his biographical page and get comprehensive information about him.

🧠 **Thinking...**

> I need to search Wikipedia for Vladimir Putin to find his biographical article and gather detailed information about him for the user.

🧠 **Thinking...**

> I need to search Wikipedia for Vladimir Putin to find his biographical page and gather detailed information about him.

🧠 **Thinking...**

> I need to search Wikipedia for Vladimir Putin to find his biographical article and get detailed information about him.

🧠 **Thinking...**

> I need to search Wikipedia for Vladimir Putin to find his biographical page and gather detailed information about him.

🧠 **Thinking...**

> I need to search Wikipedia for Vladimir Putin to find his biographical page and get comprehensive information about him.

🧠 **Thinking...**

> I need to search Wikipedia for Vladimir Putin to find his biographical article and gather detailed information about him.

🧠 **Thinking...**

> I need to search Wikipedia for Vladimir Putin to find his biographical page and gather detailed information about him for the user.

I've conducted extensive research but need to conclude. Base
```

**See the issue?** It didn't even showed the search process, when asked to tell me more about him. Since the AI is rule-based by hard-coded keywords, it can do the president related queries but fail to do other things. Instead of I want the AI to handle task solely on itself with the system prompt and function calling. Don't put rules like president, tell me about in the code.

Here are the URLs for Groq Tool Calling (function calling) docs

https://console.groq.com/docs/tool-use/remote-mcp

https://console.groq.com/docs/tool-use/local-tool-calling

Read those carefully. Also, look at this

**Prompt:** Hi

**Response:**
```
🧠 **Thinking...**

> The user has now sent seven empty messages. I will not reply again until they provide actual text or a question.

🧠 **Thinking...**

> The user has now sent eight empty messages in a row. Continuing to respond would just encourage more of the same and clutter the conversation. I'll wait silently until they provide actual text or a question.

🧠 **Thinking...**

> The user has now sent nine empty messages. I will not reply again until they provide actual text or a question.

🧠 **Thinking...**

> The user has now sent ten empty messages. I will not reply again until they provide actual text or a question.

🧠 **Thinking...**

> The user has now sent eleven empty messages. I will not reply again until they provide actual text or a question.

🧠 **Thinking...**

> The user has now sent twelve empty messages. I will not reply again until they provide actual text or a question.

🧠 **Thinking...**

> The user has now sent thirteen empty messages. I will not reply again until they provide actual text or a question.

🧠 **Thinking...**

> The user has now sent fourteen empty messages. I will not reply again until they provide actual text or a question.

🧠 **Thinking...**

> The user has now sent fifteen empty messages. I will not reply again until they provide actual text or a question.

🧠 **Thinking...**

> The user has now sent sixteen empty messages. I will not reply again until they provide actual text or a question.

🧠 **Thinking...**

> The user has now sent seventeen empty messages. I will not reply again until they provide actual text or a question.

🧠 **Thinking...**

> The user has now sent eighteen empty messages. I will not reply again until they provide actual text or a question.

🧠 **Thinking...**

> The user has now sent nineteen empty messages. I will not reply again until they provide actual text or a question.

I've conducted extensive research but need to conclude. Based on what I found:

[Provide summary]
```

The AI cannot even do a non-searching task because of the rules. Add the Thinking process for non-searching tasks should be like in below to the system prompt:

```
<think>**Initiating the Dialogue**

I've processed the user's initial "Hi!" and recognized it as a standard greeting. Now, I'm formulating a polite and welcoming response. My focus is on crafting a reply that establishes a friendly and open tone for the conversation ahead.

**Drafting a Response**

I've crafted a general, welcoming greeting: "Hello! How can I help you today?" I wanted to ensure it was universally applicable, given the lack of initial context. The goal is to set a friendly and helpful tone from the outset, paving the way for a productive conversation.
</think>

Hello! How can I help you today?