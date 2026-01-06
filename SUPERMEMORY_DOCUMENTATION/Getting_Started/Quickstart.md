# Quickstart

> Make your first API call to Supermemory - add and retrieve memories.

<Tip>
  **Using Vercel AI SDK?** Check out the [AI SDK integration](https://supermemory.ai/docs/ai-sdk/overview) for the cleanest implementation with `@supermemory/tools/ai-sdk`.
</Tip>

## Memory API

**Step 1.** Sign up for [Supermemory's Developer Platform](http://console.supermemory.ai) to get the API key. Click on **API Keys -> Create API Key** to generate one.

<img src="https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/create-api.png?fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=a3216bf250253e6b33eb44a635a62b9d" alt="create api key" data-og-width="2772" width="2772" data-og-height="1282" height="1282" data-path="images/create-api.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/create-api.png?w=280&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=e2a9b1791f12c6f65eafe2203d895611 280w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/create-api.png?w=560&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=ddb6799c4cd72493ec39ed129459c0c7 560w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/create-api.png?w=840&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=6e953f5b226c3e1d50cda289dd244b6d 840w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/create-api.png?w=1100&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=d3d106b6b8c608f10ea62d42dce11c9b 1100w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/create-api.png?w=1650&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=98ff60abb2fc308c4e9ee8f9c318ad51 1650w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/create-api.png?w=2500&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=b2a167b035101ce7d0e8aae4ee8b2466 2500w" />

**Step 2.** Install the SDK and set your API key:

<Tabs>
  <Tab title="Python">
    ```bash  theme={null}
    pip install supermemory
    export SUPERMEMORY_API_KEY="YOUR_API_KEY"
    ```
  </Tab>

  <Tab title="TypeScript">
    ```bash  theme={null}
    npm install supermemory
    export SUPERMEMORY_API_KEY="YOUR_API_KEY"
    ```
  </Tab>
</Tabs>

**Step 3.** Here's everything you need to add memory to your LLM:

<Tabs>
  <Tab title="Python">
    ```python  theme={null}
    from supermemory import Supermemory

    client = Supermemory()
    USER_ID = "dhravya"

    conversation = [
        {"role": "assistant", "content": "Hello, how are you doing?"},
        {"role": "user", "content": "Hello! I am Dhravya. I am 20 years old. I love to code!"},
        {"role": "user", "content": "Can I go to the club?"},
    ]

    # Get user profile + relevant memories for context
    profile = client.profile(container_tag=USER_ID, q=conversation[-1]["content"])

    context = f"""Static profile:
    {"\n".join(profile.profile.static)}

    Dynamic profile:
    {"\n".join(profile.profile.dynamic)}

    Relevant memories:
    {"\n".join(r.content for r in profile.search_results.results)}"""

    # Build messages with memory-enriched context
    messages = [{"role": "system", "content": f"User context:\n{context}"}, *conversation]

    # response = llm.chat(messages=messages)

    # Store conversation for future context
    client.add(
        content="\n".join(f"{m['role']}: {m['content']}" for m in conversation),
        container_tag=USER_ID,
    )
    ```
  </Tab>

  <Tab title="TypeScript">
    ```typescript  theme={null}
    import Supermemory from "supermemory";

    const client = new Supermemory();
    const USER_ID = "dhravya";

    const conversation = [
      { role: "assistant", content: "Hello, how are you doing?" },
      { role: "user", content: "Hello! I am Dhravya. I am 20 years old. I love to code!" },
      { role: "user", content: "Can I go to the club?" },
    ];

    // Get user profile + relevant memories for context
    const profile = await client.profile({
      containerTag: USER_ID,
      q: conversation.at(-1)!.content,
    });

    const context = `Static profile:
    ${profile.profile.static.join("\n")}

    Dynamic profile:
    ${profile.profile.dynamic.join("\n")}

    Relevant memories:
    ${profile.searchResults.results.map((r) => r.content).join("\n")}`;

    // Build messages with memory-enriched context
    const messages = [{ role: "system", content: `User context:\n${context}` }, ...conversation];

    // const response = await llm.chat({ messages });

    // Store conversation for future context
    await client.memories.add({
      content: conversation.map((m) => `${m.role}: ${m.content}`).join("\n"),
      containerTag: USER_ID,
    });
    ```
  </Tab>
</Tabs>

That's it! Supermemory automatically:

* Extracts memories from conversations
* Builds and maintains user profiles (static facts + dynamic context)
* Returns relevant context for personalized LLM responses

Learn more about [User Profiles](/user-profiles) and [Search](/search/overview).


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://supermemory.ai/docs/llms.txt
