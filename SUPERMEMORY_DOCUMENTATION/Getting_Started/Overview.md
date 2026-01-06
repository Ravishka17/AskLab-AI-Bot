# Overview — What is Supermemory?

Supermemory gives your LLMs long-term memory. Instead of stateless text generation, they recall the right facts from your files, chats, and tools, so responses stay consistent, contextual, and personal.

## How does it work? (at a glance)

<img src="https://mintcdn.com/supermemory/mNihXFQpgDpUIsdK/images/232.png?fit=max&auto=format&n=mNihXFQpgDpUIsdK&q=85&s=8fbcd175c1a97443386928d0fa7b3171" alt="" data-og-width="5120" width="5120" data-og-height="2880" height="2880" data-path="images/232.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/supermemory/mNihXFQpgDpUIsdK/images/232.png?w=280&fit=max&auto=format&n=mNihXFQpgDpUIsdK&q=85&s=0ef2cecaa1e1d7dc64ea499a0a41ce18 280w, https://mintcdn.com/supermemory/mNihXFQpgDpUIsdK/images/232.png?w=560&fit=max&auto=format&n=mNihXFQpgDpUIsdK&q=85&s=2969637d9786a22b66d6db0d75870090 560w, https://mintcdn.com/supermemory/mNihXFQpgDpUIsdK/images/232.png?w=840&fit=max&auto=format&n=mNihXFQpgDpUIsdK&q=85&s=9bc0a1b0fa1fca1d4d00769717e6476f 840w, https://mintcdn.com/supermemory/mNihXFQpgDpUIsdK/images/232.png?w=1100&fit=max&auto=format&n=mNihXFQpgDpUIsdK&q=85&s=05018befcdb8a4ddcf886e5ea12eb56a 1100w, https://mintcdn.com/supermemory/mNihXFQpgDpUIsdK/images/232.png?w=1650&fit=max&auto=format&n=mNihXFQpgDpUIsdK&q=85&s=ee7b7351b7d5970c9ddff4ac84d18f6a 1650w, https://mintcdn.com/supermemory/mNihXFQpgDpUIsdK/images/232.png?w=2500&fit=max&auto=format&n=mNihXFQpgDpUIsdK&q=85&s=96960e1add751e4ee78f3c5a33e32c6b 2500w" />

* You send Supermemory text, files, and chats.
* Supermemory [intelligently indexes them](/how-it-works) and builds a semantic understanding graph on top of an entity (e.g., a user, a document, a project, an organization).
* At query time, we fetch only the most relevant context and pass it to your models.

## Supermemory is context engineering.

#### Ingestion and Extraction

Supermemory handles all the extraction, for any data type that you have.

* Text
* Conversations
* Files (PDF, Images, Docs)
* Even videos!

... and then,

We offer three ways to add context to your LLMs:

#### Memory API — Learned user context

<img src="https://mintcdn.com/supermemory/kvivCPGSB_ZCTB86/images/memory-graph.png?fit=max&auto=format&n=kvivCPGSB_ZCTB86&q=85&s=185a097d41f6c437c4a131d132b7b11a" alt="memory graph" data-og-width="2084" width="2084" data-og-height="1586" height="1586" data-path="images/memory-graph.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/supermemory/kvivCPGSB_ZCTB86/images/memory-graph.png?w=280&fit=max&auto=format&n=kvivCPGSB_ZCTB86&q=85&s=4a7efdb5eb474af75968c2379af56266 280w, https://mintcdn.com/supermemory/kvivCPGSB_ZCTB86/images/memory-graph.png?w=560&fit=max&auto=format&n=kvivCPGSB_ZCTB86&q=85&s=9d9226d9e7229c49546d62c1da482961 560w, https://mintcdn.com/supermemory/kvivCPGSB_ZCTB86/images/memory-graph.png?w=840&fit=max&auto=format&n=kvivCPGSB_ZCTB86&q=85&s=36ab6e1c5f08f6bdd6a15bdff55cbc76 840w, https://mintcdn.com/supermemory/kvivCPGSB_ZCTB86/images/memory-graph.png?w=1100&fit=max&auto=format&n=kvivCPGSB_ZCTB86&q=85&s=5418b82d4828cfb79fcabe13c4cecaef 1100w, https://mintcdn.com/supermemory/kvivCPGSB_ZCTB86/images/memory-graph.png?w=1650&fit=max&auto=format&n=kvivCPGSB_ZCTB86&q=85&s=c9b173ad45890c05999959e30bbb7d74 1650w, https://mintcdn.com/supermemory/kvivCPGSB_ZCTB86/images/memory-graph.png?w=2500&fit=max&auto=format&n=kvivCPGSB_ZCTB86&q=85&s=42fa6ab0fa78912aeae3f34c8ae46eef 2500w" />

Supermemory learns and builds the memory for the user. These are extracted facts about the user, that:

* Evolve on top of existing context about the user, **in real time**
* Handle **knowledge updates, temporal changes, forgetfulness**
* Creates a **user profile** as the default context provider for the LLM.

*This can then be provided to the LLM, to give more contextual, personalized responses.*

#### User profiles

Having the latest, evolving context about the user allows us to also create a **User Profile**. This is a combination of static and dynamic facts about the user, that the agent should **always know**
Developers can configure supermemory with what static and dynamic contents are, depending on their use case.

* Static: Information that the agent should **always** know.
* Dynamic: **Episodic** information, about last few conversations etc.

This leads to a much better retrieval system, and extremely personalized responses.

#### RAG - Advanced semantic search

Along with the user context, developers can also choose to do a search on the raw context. We provide full RAG-as-a-service, along with

* Full advanced metadata filtering
* Contextual chunking
* Works well with the memory engine

<Info>
  You can reference the full API reference for the Memory API in the API Reference tab.
</Info>

<Note>
  All three approaches share the **same context pool** when using the same user ID (`containerTag`). You can mix and match based on your needs.
</Note>

## Next steps

Head to the [**How it works**](/how-it-works) guide to understand the underlying way of how supermemory represents and learns in data.


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://supermemory.ai/docs/llms.txt
