# Basic Listing

> Simple memory retrieval across languages

Simple memory retrieval examples for getting started with the list memories endpoint.

## Basic Usage

<Tabs>
  <Tab title="TypeScript">
    ```typescript  theme={null}
    import Supermemory from 'supermemory';

    const client = new Supermemory({
      apiKey: process.env.SUPERMEMORY_API_KEY!
    });

    const response = await client.memories.list({ limit: 10 });
    console.log(response);
    ```
  </Tab>

  <Tab title="Python">
    ```python  theme={null}
    from supermemory import Supermemory
    import os

    client = Supermemory(api_key=os.environ.get("SUPERMEMORY_API_KEY"))
    response = client.memories.list(limit=10)
    print(response)
    ```
  </Tab>

  <Tab title="cURL">
    ```bash  theme={null}
    curl -X POST "https://api.supermemory.ai/v3/documents/list" \
      -H "Authorization: Bearer $SUPERMEMORY_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"limit": 10}'
    ```
  </Tab>
</Tabs>

## With Custom Parameters

<Tabs>
  <Tab title="TypeScript">
    ```typescript  theme={null}
    const response = await client.memories.list({
      containerTags: ["user_123"],
      limit: 20,
      sort: "updatedAt",
      order: "desc"
    });

    console.log(`Found ${response.memories.length} memories`);
    ```
  </Tab>

  <Tab title="Python">
    ```python  theme={null}
    response = client.memories.list(
        container_tags=["user_123"],
        limit=20,
        sort="updatedAt",
        order="desc"
    )

    print(f"Found {len(response.memories)} memories")
    ```
  </Tab>

  <Tab title="cURL">
    ```bash  theme={null}
    curl -X POST "https://api.supermemory.ai/v3/documents/list" \
      -H "Authorization: Bearer $SUPERMEMORY_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "containerTags": ["user_123"],
        "limit": 20,
        "sort": "updatedAt",
        "order": "desc"
      }'
    ```
  </Tab>
</Tabs>

<Info>
  Start with small `limit` values (10-20) when testing to avoid overwhelming responses.
</Info>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://supermemory.ai/docs/llms.txt
