# Query Rewriting

> Improve search accuracy with automatic query expansion and rewriting

<img src="https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/query-rewriting.png?fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=60f21f4668364b51b9759622b2ed52d1" alt="query rewriting" data-og-width="2096" width="2096" data-og-height="868" height="868" data-path="images/query-rewriting.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/query-rewriting.png?w=280&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=c2fb7a697d13e514c9879bd965485119 280w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/query-rewriting.png?w=560&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=7ef2183d2387ae9b9c6ec57a4dfa4e69 560w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/query-rewriting.png?w=840&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=f072e6219aa8cf2ea4de87406c07e942 840w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/query-rewriting.png?w=1100&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=2abc68bb0c7ad2e60cb7a642c914704d 1100w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/query-rewriting.png?w=1650&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=569c0b6f8f525ebe3808963f06834cad 1650w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/query-rewriting.png?w=2500&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=f64bd12643c30dc9c8c0a10f3d5ede40 2500w" />

Query rewriting automatically generates multiple variations of your search query to improve result coverage and accuracy. Supermemory creates several rewrites, searches through all of them, then merges and deduplicates the results.

## How Query Rewriting Works

When you enable `rewriteQuery: true`, Supermemory:

1. **Analyzes your original query** for intent and key concepts
2. **Generates multiple rewrites** with different phrasings and synonyms
3. **Executes searches** for both original and rewritten queries in parallel
4. **Merges and deduplicates** results from all queries
5. **Returns unified results** ranked by relevance

This process adds \~400ms latency but significantly improves result quality, especially for:

* **Natural language questions** ("How do neural networks learn?")
* **Ambiguous terms** that could have multiple meanings
* **Complex queries** with multiple concepts
* **Domain-specific terminology** that might have synonyms

## Basic Query Rewriting

<Tabs>
  <Tab title="TypeScript">
    ```typescript  theme={null}
    import Supermemory from 'supermemory';

    const client = new Supermemory({
      apiKey: process.env.SUPERMEMORY_API_KEY!
    });

    // Without query rewriting
    const basicResults = await client.search.documents({
      q: "How do transformers work in AI?",
      rewriteQuery: false,
      limit: 5
    });

    // With query rewriting - generates multiple query variations
    const rewrittenResults = await client.search.documents({
      q: "How do transformers work in AI?",
      rewriteQuery: true,
      limit: 5
    });

    console.log(`Basic search: ${basicResults.total} results`);
    console.log(`Rewritten search: ${rewrittenResults.total} results`);
    ```
  </Tab>

  <Tab title="Python">
    ```python  theme={null}
    from supermemory import Supermemory
    import os

    client = Supermemory(api_key=os.environ.get("SUPERMEMORY_API_KEY"))

    # Without query rewriting
    basic_results = client.search.documents(
        q="How do transformers work in AI?",
        rewrite_query=False,
        limit=5
    )

    # With query rewriting - generates multiple query variations
    rewritten_results = client.search.documents(
        q="How do transformers work in AI?",
        rewrite_query=True,
        limit=5
    )

    print(f"Basic search: {basic_results.total} results")
    print(f"Rewritten search: {rewritten_results.total} results")
    ```
  </Tab>

  <Tab title="cURL">
    ```bash  theme={null}
    # Without query rewriting
    echo "Basic search:"
    curl -X POST "https://api.supermemory.ai/v3/search" \
      -H "Authorization: Bearer $SUPERMEMORY_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "q": "How do transformers work in AI?",
        "rewriteQuery": false,
        "limit": 5
      }' | jq '.total'

    # With query rewriting
    echo "Rewritten search:"
    curl -X POST "https://api.supermemory.ai/v3/search" \
      -H "Authorization: Bearer $SUPERMEMORY_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "q": "How do transformers work in AI?",
        "rewriteQuery": true,
        "limit": 5
      }' | jq '.total'
    ```
  </Tab>
</Tabs>

**Sample Output Comparison:**

```json  theme={null}
// Without rewriting: 3 results
{
  "results": [...],
  "total": 3,
  "timing": 120
}

// With rewriting: 8 results (found more relevant content)
{
  "results": [...],
  "total": 8,
  "timing": 520  // +400ms for query processing
}
```

## Natural Language Questions

Query rewriting excels at converting conversational questions into effective search queries:

<Tabs>
  <Tab title="TypeScript">
    ```typescript  theme={null}
    // Natural language question
    const results = await client.search.documents({
      q: "What are the best practices for training deep learning models?",
      rewriteQuery: true,
      limit: 10
    });

    // The system might generate rewrites like:
    // - "deep learning model training best practices"
    // - "neural network training optimization techniques"
    // - "machine learning model training guidelines"
    // - "deep learning training methodology"
    ```
  </Tab>

  <Tab title="Python">
    ```python  theme={null}
    # Natural language question
    results = client.search.documents(
        q="What are the best practices for training deep learning models?",
        rewrite_query=True,
        limit=10
    )

    # The system might generate rewrites like:
    # - "deep learning model training best practices"
    # - "neural network training optimization techniques"
    # - "machine learning model training guidelines"
    # - "deep learning training methodology"
    ```
  </Tab>

  <Tab title="cURL">
    ```bash  theme={null}
    curl -X POST "https://api.supermemory.ai/v3/search" \
      -H "Authorization: Bearer $SUPERMEMORY_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "q": "What are the best practices for training deep learning models?",
        "rewriteQuery": true,
        "limit": 10
      }'
    ```
  </Tab>
</Tabs>

**Sample Output:**

```json  theme={null}
{
  "results": [
    {
      "documentId": "doc_123",
      "title": "Deep Learning Training Guide",
      "score": 0.92,
      "chunks": [
        {
          "content": "Best practices for training deep neural networks include proper weight initialization, learning rate scheduling, and regularization techniques...",
          "score": 0.89,
          "isRelevant": true
        }
      ]
    },
    {
      "documentId": "doc_456",
      "title": "Neural Network Optimization",
      "score": 0.87,
      "chunks": [
        {
          "content": "Effective training methodologies involve batch normalization, dropout, and gradient clipping to prevent overfitting...",
          "score": 0.85,
          "isRelevant": true
        }
      ]
    }
  ],
  "total": 12,
  "timing": 445
}
```

## Technical Term Expansion

Query rewriting helps find content using different technical terminologies:

<Tabs>
  <Tab title="TypeScript">
    ```typescript  theme={null}
    // Original query with specific terminology
    const results = await client.search.documents({
      q: "CNN architecture patterns",
      rewriteQuery: true,
      containerTags: ["research"],
      limit: 8
    });

    // System expands to include:
    // - "convolutional neural network architecture"
    // - "CNN design patterns"
    // - "convolutional network structures"
    // - "CNN architectural components"
    ```
  </Tab>

  <Tab title="Python">
    ```python  theme={null}
    # Original query with specific terminology
    results = client.search.documents(
        q="CNN architecture patterns",
        rewrite_query=True,
        container_tags=["research"],
        limit=8
    )

    # System expands to include:
    # - "convolutional neural network architecture"
    # - "CNN design patterns"
    # - "convolutional network structures"
    # - "CNN architectural components"
    ```
  </Tab>

  <Tab title="cURL">
    ```bash  theme={null}
    curl -X POST "https://api.supermemory.ai/v3/search" \
      -H "Authorization: Bearer $SUPERMEMORY_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "q": "CNN architecture patterns",
        "rewriteQuery": true,
        "containerTags": ["research"],
        "limit": 8
      }'
    ```
  </Tab>
</Tabs>

**Sample Output:**

```json  theme={null}
{
  "results": [
    {
      "documentId": "doc_789",
      "title": "Convolutional Neural Network Architectures",
      "score": 0.94,
      "chunks": [
        {
          "content": "Modern CNN architectures like ResNet and DenseNet utilize skip connections to address the vanishing gradient problem...",
          "score": 0.91,
          "isRelevant": true
        }
      ]
    },
    {
      "documentId": "doc_101",
      "title": "Deep Learning Design Patterns",
      "score": 0.88,
      "chunks": [
        {
          "content": "Convolutional layers followed by pooling operations form the fundamental building blocks of CNN architectures...",
          "score": 0.86,
          "isRelevant": true
        }
      ]
    }
  ],
  "total": 15,
  "timing": 478
}
```

## Memory Search with Query Rewriting

Query rewriting works with both document and memory search:

<Tabs>
  <Tab title="TypeScript">
    ```typescript  theme={null}
    // Memory search with query rewriting
    const memoryResults = await client.search.memories({
      q: "explain quantum entanglement simply",
      rewriteQuery: true,
      containerTag: "physics_notes",
      limit: 5
    });

    // Generates variations like:
    // - "quantum entanglement explanation"
    // - "what is quantum entanglement"
    // - "quantum entanglement basics"
    // - "simple quantum entanglement description"
    ```
  </Tab>

  <Tab title="Python">
    ```python  theme={null}
    # Memory search with query rewriting
    memory_results = client.search.memories(
        q="explain quantum entanglement simply",
        rewrite_query=True,
        container_tag="physics_notes",
        limit=5
    )

    # Generates variations like:
    # - "quantum entanglement explanation"
    # - "what is quantum entanglement"
    # - "quantum entanglement basics"
    # - "simple quantum entanglement description"
    ```
  </Tab>

  <Tab title="cURL">
    ```bash  theme={null}
    curl -X POST "https://api.supermemory.ai/v4/search" \
      -H "Authorization: Bearer $SUPERMEMORY_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "q": "explain quantum entanglement simply",
        "rewriteQuery": true,
        "containerTag": "physics_notes",
        "limit": 5
      }'
    ```
  </Tab>
</Tabs>

**Sample Output:**

```json  theme={null}
{
  "results": [
    {
      "id": "mem_456",
      "memory": "Quantum entanglement is a phenomenon where two particles become connected in such a way that measuring one instantly affects the other, regardless of distance. Think of it like having two magical coins that always land on opposite sides.",
      "similarity": 0.91,
      "title": "Simple Quantum Entanglement Explanation",
      "metadata": {
        "topic": "quantum-physics",
        "difficulty": "beginner"
      }
    },
    {
      "id": "mem_789",
      "memory": "Einstein called quantum entanglement 'spooky action at a distance' because entangled particles seem to communicate instantaneously across vast distances, challenging our understanding of locality in physics.",
      "similarity": 0.87,
      "title": "Einstein's View on Entanglement"
    }
  ],
  "total": 7,
  "timing": 412
}
```

## Complex Multi-Concept Queries

Query rewriting excels at handling queries with multiple concepts:

<Tabs>
  <Tab title="TypeScript">
    ```typescript  theme={null}
    const results = await client.search.documents({
      q: "machine learning bias fairness algorithmic discrimination",
      rewriteQuery: true,
      filters: {
        AND: [
          { key: "category", value: "ethics", negate: false }
        ]
      },
      limit: 10
    });

    // Breaks down into focused rewrites:
    // - "machine learning bias detection"
    // - "algorithmic fairness in AI"
    // - "discrimination in machine learning algorithms"
    // - "bias mitigation techniques ML"
    ```
  </Tab>

  <Tab title="Python">
    ```python  theme={null}
    results = client.search.documents(
        q="machine learning bias fairness algorithmic discrimination",
        rewrite_query=True,
        filters={
            "AND": [
                {"key": "category", "value": "ethics", "negate": False}
            ]
        },
        limit=10
    )

    # Breaks down into focused rewrites:
    # - "machine learning bias detection"
    # - "algorithmic fairness in AI"
    # - "discrimination in machine learning algorithms"
    # - "bias mitigation techniques ML"
    ```
  </Tab>

  <Tab title="cURL">
    ```bash  theme={null}
    curl -X POST "https://api.supermemory.ai/v3/search" \
      -H "Authorization: Bearer $SUPERMEMORY_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "q": "machine learning bias fairness algorithmic discrimination",
        "rewriteQuery": true,
        "filters": {
          "AND": [
            {"key": "category", "value": "ethics", "negate": false}
          ]
        },
        "limit": 10
      }'
    ```
  </Tab>
</Tabs>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://supermemory.ai/docs/llms.txt
