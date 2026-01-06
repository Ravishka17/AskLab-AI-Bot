# How Supermemory Works

> Understanding the knowledge graph architecture that powers intelligent memory

Supermemory isn't just another document storage system. It's designed to mirror how human memory actually works - forming connections, evolving over time, and generating insights from accumulated knowledge.

<img src="https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/graph-view.png?fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=e05dffd1f85e514d65e962b8bcbe70c3" alt="" data-og-width="2786" width="2786" data-og-height="1662" height="1662" data-path="images/graph-view.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/graph-view.png?w=280&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=783f47a12f19bbc477d0d8151f88374a 280w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/graph-view.png?w=560&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=f2a3c56a57fc99b7ff5d9d501782aba8 560w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/graph-view.png?w=840&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=c56dcf534126dd9af5864e15780cc0d5 840w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/graph-view.png?w=1100&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=adedf3be078c9cf54367acea4688cdbd 1100w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/graph-view.png?w=1650&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=09a92a121ac17a585a1e781d9e21734c 1650w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/graph-view.png?w=2500&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=39c9f6dc57099350d6469a70bf388b2d 2500w" />

## The Mental Model

Traditional systems store files. Supermemory creates a living knowledge graph.

<CardGroup cols={2}>
  <Card title="Traditional Systems" icon="folder">
    * Static files in folders
    * No connections between content
    * Search matches keywords
    * Information stays frozen
  </Card>

  <Card title="Supermemory" icon="network">
    * Dynamic knowledge graph
    * Rich relationships between memories
    * Semantic understanding
    * Information evolves and connects
  </Card>
</CardGroup>

## Documents vs Memories

Understanding this distinction is crucial to using Supermemory effectively.

### Documents: Your Raw Input

Documents are what you provide - the raw materials:

* PDF files you upload
* Web pages you save
* Text you paste
* Images with text
* Videos to transcribe

Think of documents as books you hand to Supermemory.

### Memories: Intelligent Knowledge Units

Memories are what Supermemory creates - the understanding:

* Semantic chunks with meaning
* Embedded for similarity search
* Connected through relationships
* Dynamically updated over time

Think of memories as the insights and connections your brain makes after reading those books.

<Note>
  **Key Insight**: When you upload a 50-page PDF, Supermemory doesn't just store it. It breaks it into hundreds of interconnected memories, each understanding its context and relationships to your other knowledge.
</Note>

## Memory Relationships

<img src="https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/memories-inferred.png?fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=1755eced95305da072bcd9a598d5e3b5" alt="" data-og-width="5120" width="5120" data-og-height="2880" height="2880" data-path="images/memories-inferred.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/memories-inferred.png?w=280&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=5226a6d8248d619a17a49efc2098bf33 280w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/memories-inferred.png?w=560&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=7b211b2caf82216694900f83a652132f 560w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/memories-inferred.png?w=840&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=6a871dbb117027302904c5ce4f7b1623 840w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/memories-inferred.png?w=1100&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=f1b8c0da6d86f195379bba3960462f91 1100w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/memories-inferred.png?w=1650&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=1918d41ba800f451a351b5519b896625 1650w, https://mintcdn.com/supermemory/nafXZdsbm5CLncox/images/memories-inferred.png?w=2500&fit=max&auto=format&n=nafXZdsbm5CLncox&q=85&s=556f4c1f226a6c374aa58af415d4aca2 2500w" />

The graph connects memories through three types of relationships:

### Updates: Information Changes

When new information contradicts or updates existing knowledge, Supermemory creates an "update" relationship.

<CodeGroup>
  ```text Original Memory theme={null}
  "You work at Supermemory as a content engineer"
  ```

  ```text New Memory (Updates Original) theme={null}
  "You now work at Supermemory as the CMO"
  ```
</CodeGroup>

The system tracks which memory is latest with an `isLatest` field, ensuring searches return current information.

### Extends: Information Enriches

When new information adds to existing knowledge without replacing it, Supermemory creates an "extends" relationship.

Continuing our "working at supermemory" analogy, a memory about what you work on would extend the memory about your role given above.

<CodeGroup>
  ```text Original Memory theme={null}
  "You work at Supermemory as the CMO"
  ```

  ```text New Memory (Extension) - Separate From Previous theme={null}
  "Your work consists of ensuring the docs are up to date, making marketing campaigns, SEO, etc."
  ```
</CodeGroup>

Both memories remain valid and searchable, providing richer context.

### Derives: Information Infers

The most sophisticated relationship - when Supermemory infers new connections from patterns in your knowledge.

<CodeGroup>
  ```text Memory 1 theme={null}
  "Dhravya is the founder of Supermemory"
  ```

  ```text Memory 2 theme={null}
  "Dhravya frequently discusses AI and machine learning innovations"
  ```

  ```text Derived Memory theme={null}
  "Supermemory is likely an AI-focused company"
  ```
</CodeGroup>

These inferences help surface insights you might not have explicitly stated.

## Processing Pipeline

Understanding the pipeline helps you optimize your usage:

| Stage          | What Happens                |
| -------------- | --------------------------- |
| **Queued**     | Document waiting to process |
| **Extracting** | Content being extracted     |
| **Chunking**   | Creating memory chunks      |
| **Embedding**  | Generating vectors          |
| **Indexing**   | Building relationships      |
| **Done**       | Fully searchable            |

<Note>
  **Tip**: Larger documents and videos take longer. A 100-page PDF might take 1-2 minutes, while a 1-hour video could take 5-10 minutes.
</Note>

## Next Steps

Now that you understand how Supermemory works:

<CardGroup cols={2}>
  <Card title="Add Memories" icon="plus" href="/add-memories/overview">
    Start adding content to your knowledge graph
  </Card>

  <Card title="Search Memories" icon="search" href="/search/overview">
    Learn to query your knowledge effectively
  </Card>
</CardGroup>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://supermemory.ai/docs/llms.txt
