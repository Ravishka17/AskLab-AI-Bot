---
description: A comprehensive guide to prompt engineering patterns for large language models, including Zero Shot, Few Shot, Chain of Thought, ReAct, Chain of Verification, and Chain of Density. Learn when and how to use each pattern with practical examples and tips for reliable results.
title: Prompt Engineering Patterns Guide - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Prompt Engineering Patterns Guide

This guide provides a systematic approach to selecting appropriate prompt patterns for various tasks when working with open-source language models. Implementing the correct pattern significantly improves output reliability and performance.

## [Why Patterns Matter](#why-patterns-matter)

Prompt patterns serve distinct purposes in language model interactions:

* **Zero shot** provides instructions without examples, relying on the model's existing knowledge.
* **Few shot** demonstrates specific examples for the model to follow as templates.
* **Chain of Thought** breaks complex reasoning into sequential steps for methodical problem-solving.

Selecting the appropriate pattern significantly improves output accuracy, consistency, and reliability across applications.

## [Pattern Chooser Table](#pattern-chooser-table)

The table below helps you quickly identify the most effective prompt pattern for your specific task, matching common use cases with optimal approaches to maximize model performance.

| Task Type                               | Recommended Pattern                                                | Why it works                                         |
| --------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------------------- |
| Simple Q&A, definitions                 | [**Zero shot**](#zero-shot)                                        | Model already knows; instructions suffice            |
| Extraction / classification             | [**Few shot (1-3 samples)**](#one-shot--few-shot)                  | Teaches exact labels & JSON keys                     |
| Creative writing                        | [**Zero shot + role**](#zero-shot)                                 | Freedom + persona = coherent style                   |
| Multi-step math / logic                 | [**Chain of Thought**](#chain-of-thought)                          | Forces stepwise reasoning                            |
| Edge-case heavy tasks                   | [**Few shot (2-5 samples)**](#one-shot--few-shot)                  | Covers exceptions & rare labels                      |
| Mission-critical accuracy               | [**Guided CoT + Self Consistency**](#guided-cot--self-consistency) | Multiple reasoned paths to a consensus               |
| Tool-use / knowledge-heavy tasks        | [**ReAct (Reasoning + Acting)**](#react-reasoning-and-acting)      | Thinks, calls tools, repeats for grounded solutions. |
| Concise yet comprehensive summarization | [**Chain of Density (CoD)**](#chain-of-density-cod)                | Stepwise compression keeps essentials, cuts fluff.   |
| Accuracy-critical facts                 | [**Chain of Verification (CoVe)**](#chain-of-verification-cove)    | Asks and answers its own checks, then fixes.         |

## [Customer Support Ticket Processing Use Case](#customer-support-ticket-processing-use-case)

Throughout this guide, we'll use the practical example of automating customer support ticket processing. This enterprise-relevant use case demonstrates how different prompt patterns can improve:

* Initial ticket triage and categorization
* Issue urgency assessment
* Information extraction from customer communications
* Resolution suggestions and draft responses
* Ticket summarization for team handoffs

Using AI to enhance support ticket processing can reduce agent workload, accelerate response times, ensure consistent handling, and enable better tracking of common issues. Each prompt pattern offers distinct advantages for specific aspects of the support workflow.

## [Zero Shot](#zero-shot)

Zero shot prompting tells a large-language model **exactly what you want without supplying a single demonstration**. The model leans on the general-purpose knowledge it absorbed during pre-training to infer the right output. You provide instructions but no examples, allowing the model to apply its existing understanding to the task.

### [When to use](#when-to-use)

| Use case                                                       | Why Zero Shot works                                                       |
| -------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Sentiment classification**                                   | Model has seen millions of examples during training; instructions suffice |
| **Basic information extraction** (e.g., support ticket triage) | Simple extraction of explicit data points requires minimal guidance       |
| **Urgent support ticket assessment**                           | Clear indicators of urgency are typically explicit in customer language   |
| **Standard content formatting**                                | Straightforward style adjustments like formalization or simplification    |
| **Language translation**                                       | Well-established task with clear inputs and outputs                       |
| **Content outlines and summaries**                             | Follows common structural patterns; benefits from brevity                 |

### [Support Ticket Zero Shot Example](#support-ticket-zero-shot-example)

This example demonstrates using zero shot prompting to quickly analyze a customer support ticket for essential information.

  
**Prompt:**

curl

```
Analyze the following customer support ticket and provide a JSON output containing:
- A brief 'summary' of the issue.
- The 'category' of the issue (e.g., Technical, Billing, Inquiry).
- The 'urgency' level (Low, Medium, High).
- A 'suggested_next_action' for the support team.

Ticket:
## Support Ticket ##

Ticket ID: TSK-2024-00123
Customer Name: Jane Doe
Customer Email: [email protected]
Customer ID: CUST-78910
Date Submitted: 2025-05-19 10:30 AM UTC
Product/Service: SuperWidget Pro
Subject: Cannot log in to my account

Issue Description:
I've been trying to log into my SuperWidget Pro account for the past 3 hours with no success. I keep getting an "Authentication Error (Code: 503)" message. I tried resetting my password, but I'm not receiving the reset email. I need urgent access to my project files for a client meeting this afternoon. My username is janedoe_widgets.
```

Output

JSON

```
{
  "summary": "User cannot log in due to an authentication error and is not receiving password reset emails, requiring urgent access for a client meeting.",
  "category": "Technical Issue",
  "urgency": "High",
  "suggested_next_action": "Investigate authentication error 503 and email delivery system, prioritizing resolution before the client meeting."
}
```

### [Why This Works](#why-this-works)

Zero shot prompting works effectively for this basic ticket analysis because:

1. The task involves common support concepts (categorization, urgency assessment) that models have encountered frequently in training data
2. The instruction clearly states the expected output format and fields
3. The customer's issue is described in straightforward terms with explicit mentions of errors and impact
4. No specialized domain knowledge is required for this initial assessment

The approach is ideal for quick initial triage before more detailed processing, allowing support systems to rapidly assign tickets without the overhead of examples.

### [Common Zero Shot Limitations and Challenges](#common-zero-shot-limitations-and-challenges)

1. **Ambiguous asks** \- vague instructions invite the model to hallucinate; add role + task + format cues.
2. **Hidden complexity** \- tasks that _look_ simple (e.g., nested condition extraction) often need [few shot](#one-shot--few-shot) or [chain of thought](#chain-of-thought).
3. **Over-creative output** \- for deterministic tasks, keep `temperature` at 0.2 or less.

## [One Shot & Few Shot](#one-shot--few-shot)

A **one shot prompt** includes exactly one worked example; a **few shot prompt** provides several (typically 3-8) examples. Both rely on the model's in-context learning to imitate the demonstrated input to output mapping. Because the demonstrations live in the prompt, you get the benefits of "training" without fine-tuning: you can swap tasks or tweak formats instantly by editing examples.

### [When to use](#when-to-use)

| Use case                                                        | Why One/Few Shot works                                                                            |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Structured output (JSON, SQL, XML)**                          | Examples nail the exact keys, quoting, or delimiters you need                                     |
| **Support ticket categorization** with nuanced or custom labels | A few examples teach proper categorization schemes specific to your organization                  |
| **Domain-specific extraction** from technical support tickets   | Demonstrations anchor the terminology and extraction patterns                                     |
| **Edge-case handling** for unusual tickets                      | Show examples of tricky inputs to teach disambiguation strategies                                 |
| **Consistent formatting** of support responses                  | Examples ensure adherence to company communication standards                                      |
| **Custom urgency criteria** based on business rules             | Examples demonstrate how to apply organization-specific Service Level Agreement (SLA) definitions |

### [Support Ticket Few Shot Example](#support-ticket-few-shot-example)

This example demonstrates using few shot prompting to extract detailed, structured information from support tickets according to a specific schema.

  
**Prompt:**

curl

```
### Example 1
Ticket:
## Support Ticket ##

Ticket ID: TSK-2024-00122
Customer Name: John Smith
Customer Email: [email protected]
Customer ID: CUST-45678
Date Submitted: 2024-03-14 09:15 AM UTC
Product/Service: SuperWidget Pro
Subject: Billing cycle error - double charged

Issue Description:
I was charged twice for my monthly subscription on March 10th. The first charge is $29.99 and then there's another identical charge of $29.99 on the same day. I've never had this happen before. Please refund the duplicate charge. My subscription ID is SUB-9876.

Output:
{
"ticket_id": "TSK-2024-00122",
"customer_info": {
  "name": "John Smith",
  "email": "[email protected]",
  "customer_id": "CUST-45678"
},
"submission_details": {
  "date_submitted": "2024-03-14 09:15 AM UTC",
  "product_service": "SuperWidget Pro",
  "subject": "Billing cycle error - double charged"
},
"issue_analysis": {
  "summary": "Customer was double-charged $29.99 for their monthly subscription on March 10th.",
  "category": "Billing Issue",
  "sub_category": "Double Charge",
  "urgency": "Medium",
  "subscription_id": "SUB-9876"
},
"suggested_resolution": {
  "next_step_internal": "Verify the duplicate charge and process refund.",
  "draft_response_to_customer": "Dear John, I'm sorry to hear about the duplicate charge for your SuperWidget Pro subscription. I've verified the issue and have initiated a refund of $29.99 to your original payment method. This should appear in your account within 3-5 business days. Please let me know if you have any other questions."
}
}

### Example 2
Ticket:
## Support Ticket ##

Ticket ID: TSK-2024-00115
Customer Name: Sarah Johnson
Customer Email: [email protected]
Customer ID: CUST-33456
Date Submitted: 2024-03-12 14:22 PM UTC
Product/Service: SuperWidget Lite
Subject: Feature request - dark mode

Issue Description:
I love using SuperWidget Lite but it's hard on my eyes when working late. Could you please add a dark mode option? Most apps I use have this feature now. Not urgent but would really improve my experience! Thanks for considering.

Output:
{
"ticket_id": "TSK-2024-00115",
"customer_info": {
  "name": "Sarah Johnson",
  "email": "[email protected]",
  "customer_id": "CUST-33456"
},
"submission_details": {
  "date_submitted": "2024-03-12 14:22 PM UTC",
  "product_service": "SuperWidget Lite",
  "subject": "Feature request - dark mode"
},
"issue_analysis": {
  "summary": "Customer requests adding dark mode to SuperWidget Lite to reduce eye strain when working late.",
  "category": "Feature Request",
  "sub_category": "UI Enhancement",
  "urgency": "Low"
},
"suggested_resolution": {
  "next_step_internal": "Add to product feature request backlog for consideration in upcoming sprint planning.",
  "draft_response_to_customer": "Dear Sarah, thank you for your suggestion about adding dark mode to SuperWidget Lite. I've forwarded your request to our product team for consideration in our future updates. We appreciate your feedback as it helps us improve our product. I'll make a note in your account so we can notify you if this feature becomes available."
}
}

### Task
Using the format from the examples, analyze the following ticket:

Ticket:
## Support Ticket ##

Ticket ID: TSK-2024-00123
Customer Name: Jane Doe
Customer Email: [email protected]
Customer ID: CUST-78910
Date Submitted: 2024-03-15 10:30 AM UTC
Product/Service: SuperWidget Pro
Subject: Cannot log in to my account

Issue Description:
I've been trying to log into my SuperWidget Pro account for the past 3 hours with no success. I keep getting an "Authentication Error (Code: 503)" message. I tried resetting my password, but I'm not receiving the reset email. I need urgent access to my project files for a client meeting this afternoon. My username is janedoe_widgets.
```

Output

JSON

```
{
  "ticket_id": "TSK-2024-00123",
  "customer_info": {
      "name": "Jane Doe",
      "email": "[email protected]",
      "customer_id": "CUST-78910",
      "username_mentioned": "janedoe_widgets"
  },
  "submission_details": {
      "date_submitted": "2024-03-15 10:30 AM UTC",
      "product_service": "SuperWidget Pro",
      "subject": "Cannot log in to my account"
  },
  "issue_analysis": {
      "summary": "Customer cannot log into their SuperWidget Pro account due to an Authentication Error (Code: 503) and is not receiving password reset emails.",
      "category": "Technical Issue",
      "sub_category": "Authentication",
      "urgency": "High",
      "error_codes_extracted": ["503"]
  },
  "suggested_resolution": {
      "next_step_internal": "Investigate authentication system and email delivery for user 'janedoe_widgets'. Prioritize as urgent due to client meeting time constraint.",
      "draft_response_to_customer": "Dear Jane, I'm sorry to hear you're experiencing trouble logging into your SuperWidget Pro account. I understand this is urgent due to your client meeting. I've initiated an investigation into the Authentication Error (Code: 503) and the issue with password reset emails. While our team works on this, could you please try accessing your account using a different browser or device? I'll personally follow up with you as soon as I have an update."
  }
}
```

### [Why This Works](#why-this-works)

Few shot prompting works effectively for detailed support ticket analysis because:

1. The examples provide a precise template for the expected JSON structure, including all required fields and formatting
2. The examples demonstrate proper categorization and sub-categorization according to ticket content
3. The model learns how to extract implicit information (like usernames mentioned in the text) by seeing it done in examples
4. The urgency assessment criteria (with three different urgency levels across examples) helps calibrate the model's understanding of priority
5. Response drafting follows the tone and format demonstrated in the examples, maintaining consistency with company standards

The approach is particularly valuable when you need to extract information according to a specific schema or organization-specific categorization system that might not match general knowledge patterns.

### [Tips](#tips)

* **Token budget**: If your examples are long, consider using only 2-3 to avoid excessive prompt length.
* **Diversity**: Include examples that demonstrate different categories, urgency levels, and edge cases.
* **Specificity**: Choose examples that demonstrate exactly the fields and format you want in the output.
* **Over-fitting**: Too many very similar examples can cause the model to copy content verbatim; maintain variety.
* **Order effects**: Place the most representative or complex examples last as they tend to influence the model most strongly.

## [Chain of Thought](#chain-of-thought)

Chain of Thought (CoT) is a prompt engineering technique that explicitly instructs the model to think through a problem step-by-step before producing the answer. In its simplest form you add a phrase like **"Let's think step by step."** This cue triggers the model to emit a sequence of reasoning statements (the "chain") followed by a conclusion. Zero shot CoT works effectively on arithmetic and commonsense questions, while few shot CoT supplies handcrafted exemplars for more complex domains.

### [When to use](#when-to-use)

| Problem type                        | Why CoT helps                                                   |
| ----------------------------------- | --------------------------------------------------------------- |
| **Math & logic word problems**      | Forces explicit arithmetic steps                                |
| **Multi-hop Q&A / retrieval**       | Encourages sequential evidence gathering                        |
| **Complex support ticket analysis** | Breaks down issue diagnosis into logical components             |
| **Content plans & outlines**        | Structures longform content creation                            |
| **Policy / safety analysis**        | Documents each step of reasoning for transparency               |
| **Ticket priority determination**   | Systematically assesses impact, urgency, and SLA considerations |

### [Support Ticket Chain of Thought Example](#support-ticket-chain-of-thought-example)

This example demonstrates using CoT to systematically analyze a customer support ticket to extract detailed information and make reasoned judgments about the issue.

  
**Prompt:**

curl

```
Analyze the following customer support ticket. First, let's think step by step to understand the problem, and then provide a structured JSON output.

Ticket:
## Support Ticket ##

Ticket ID: TSK-2024-00123
Customer Name: Jane Doe
Customer Email: [email protected]
Customer ID: CUST-78910
Date Submitted: 2024-03-15 10:30 AM UTC
Product/Service: SuperWidget Pro
Subject: Cannot log in to my account

Issue Description:
I've been trying to log into my SuperWidget Pro account for the past 3 hours with no success. I keep getting an "Authentication Error (Code: 503)" message. I tried resetting my password, but I'm not receiving the reset email. I need urgent access to my project files for a client meeting this afternoon. My username is janedoe_widgets.
```

Output

Let me think through this step by step:

1: First, I need to identify the customer details:

* Ticket ID: `TSK-2024-00123`
* Customer: Jane Doe (CUST-78910)
* Email: `[[email protected]](/cdn-cgi/l/email-protection)`
* Product: SuperWidget Pro
* Username mentioned: `janedoe_widgets`

2: What is the core problem?

* Customer cannot log in to SuperWidget Pro account
* Specific error: "Authentication Error (Code: 503)"
* Secondary issue: Password reset emails not being received

3: Analyzing severity and impact:

* Customer has been trying for 3 hours (persistent issue)
* Customer has an urgent need: client meeting this afternoon
* Project files are inaccessible, potentially affecting business
* This suggests a HIGH urgency level

4: Categorizing the issue:

* Primary category: Technical Issue
* Sub-category: Authentication
* Systems potentially involved: Login system, Email delivery system

5: What should support do next?

* Primary: Investigate authentication system error 503
* Secondary: Check email delivery system for password reset
* Immediate: Try alternative access methods for the customer

6: Based on this analysis, here's the structured output:

JSON

```
{
  "ticket_id": "TSK-2024-00123",
  "customer_info": {
      "name": "Jane Doe",
      "email": "[email protected]",
      "customer_id": "CUST-78910",
      "username": "janedoe_widgets"
  },
  "issue_analysis": {
      "primary_issue": "Cannot log in to account",
      "error_code": "Authentication Error (503)",
      "secondary_issue": "Password reset emails not being received",
      "category": "Technical Issue",
      "sub_category": "Authentication",
      "urgency": "High",
      "business_impact": "Customer needs access to project files for client meeting today"
  },
  "recommended_actions": {
      "immediate": "Provide alternative access method to project files if possible",
      "investigation": [
      "Check authentication system status and error code 503",
      "Verify email delivery system functionality for reset emails"
      ],
      "customer_response": "Acknowledge urgency, explain investigation steps, suggest alternative access methods, and commit to follow-up before client meeting"
  }
}
```

### [Why This Works](#why-this-works)

CoT prompting works effectively for support ticket analysis because:

1. It breaks down the complex task of ticket analysis into discrete, manageable steps
2. Each step focuses on a specific aspect of the analysis (customer details, core problem, severity, categorization, next actions)
3. The systematic approach ensures thorough consideration of all relevant information
4. The explicit reasoning reveals how urgency and categorization decisions are made
5. The step-by-step process mimics the diagnostic thinking of experienced support agents
6. The final structured output benefits from the comprehensive analysis that preceded it

The approach is particularly valuable for tickets that require nuanced analysis, urgency assessment based on business impact, or where multiple systems may be involved in the resolution.

### [Tips](#tips)

* **Structured prompting:** For consistent results, consider outlining specific steps you want the model to follow
* **Reasoning transparency:** CoT provides auditability of decision-making, which is valuable for training and quality assurance
* **Token considerations:** This approach generates more tokens than direct extraction methods
* **Temperature setting:** Use lower temperature (≤0.3) for more consistent reasoning patterns
* **Hybrid approach:** Combine with few shot examples of reasoning patterns for organization-specific analysis standards

## [Guided CoT & Self Consistency](#guided-cot--self-consistency)

Guided CoT provides a structured outline of reasoning steps for the model to follow. Rather than letting the model determine its own reasoning path, you explicitly define the analytical framework.

  
Self-Consistency replaces standard decoding in CoT with a sample-and-majority-vote strategy: the same CoT prompt is run multiple times with a higher temperature, the answer from each chain is extracted, then the most common answer is returned as the final result.

### [When to use](#when-to-use)

| Use case                                                      | Why it works                                                                   |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **Support ticket categorization** with complex business rules | Guided CoT ensures consistent application of classification criteria           |
| **SLA breach determination** with multiple factors            | Self-Consistency reduces calculation errors in deadline computations           |
| **Risk assessment** of customer issues                        | Multiple reasoning paths help identify edge cases in potential impact analysis |
| **Customer sentiment analysis** in ambiguous situations       | Consensus across multiple paths provides more reliable interpretation          |
| **Root cause analysis** for technical issues                  | Guided steps ensure thorough investigation across all system components        |
| **Draft response generation** for sensitive issues            | Self-Consistency helps avoid inappropriate or inadequate responses             |

### [Support Ticket Guided CoT Example](#support-ticket-guided-cot-example)

This example demonstrates using Guided CoT to systematically analyze a support ticket following a specific analytical framework.

  
**Prompt:**

curl

```
Analyze the following support ticket using these specific steps:

Step 1: Extract and list all customer identification information.
Step 2: Identify the primary issue and any secondary issues mentioned.
Step 3: Note any error codes or specific system behaviors reported.
Step 4: Determine urgency based on: (a) customer's stated timeframe, (b) business impact, (c) system availability.
Step 5: Classify the issue using our taxonomy (Technical, Billing, Account, or Feature Request).
Step 6: Recommend next actions for both internal team and customer communication.
Step 7: Generate a structured JSON output with all findings.

Ticket:
## Support Ticket ##

Ticket ID: TSK-2024-00123
Customer Name: Jane Doe
Customer Email: [email protected]
Customer ID: CUST-78910
Date Submitted: 2024-03-15 10:30 AM UTC
Product/Service: SuperWidget Pro
Subject: Cannot log in to my account

Issue Description:
I've been trying to log into my SuperWidget Pro account for the past 3 hours with no success. I keep getting an "Authentication Error (Code: 503)" message. I tried resetting my password, but I'm not receiving the reset email. I need urgent access to my project files for a client meeting this afternoon. My username is janedoe_widgets.
```

Output

Following the required steps:

1: Customer identification information:

* Ticket ID: `TSK-2024-00123`
* Customer Name: Jane Doe
* Customer Email: `[[email protected]](/cdn-cgi/l/email-protection)`
* Customer ID: `CUST-78910`
* Username: `janedoe_widgets`
* Product: `SuperWidget Pro`

2: Issues identified:

* Primary issue: Cannot log in to account
* Secondary issue: Not receiving password reset emails

3: Error codes and system behaviors:

* Authentication Error (Code: 503)
* Password reset system not delivering emails

4: Urgency determination:

* Customer's stated timeframe: Needs access "this afternoon" for a client meeting
* Business impact: Potential disruption to client relationship/business operations
* System availability: Authentication system appears to be functional but returning errors
* Urgency assessment: HIGH (time-sensitive with business impact)

5: Issue classification:

* Category: Technical
* Sub-category: Authentication

6: Recommended actions:

* Internal: Investigate Authentication Error 503
* Customer communication: Acknowledge urgent timeline, inform of investigation, provide alternative access method if possible

7: JSON output:

JSON

```
{
"ticket_analysis": {
  "ticket_id": "TSK-2024-00123",
  "customer_details": {
    "name": "Jane Doe",
    "email": "[email protected]",
    "customer_id": "CUST-78910",
    "username": "janedoe_widgets"
  },
  "product_info": {
    "product_name": "SuperWidget Pro"
  },
  "issue_details": {
    "primary_issue": "Cannot log in to account",
    "secondary_issues": ["Not receiving password reset emails"],
    "error_codes": ["Authentication Error (Code: 503)"],
    "system_behaviors": ["Password reset system not delivering emails"]
  },
  "urgency_assessment": {
    "level": "HIGH",
    "time_constraint": "Client meeting this afternoon",
    "business_impact": "Potential client relationship disruption"
  },
  "classification": {
    "category": "Technical",
    "sub_category": "Authentication"
  },
  "action_plan": {
    "internal_actions": [
      "Investigate Authentication Error 503",
      "Check email delivery system for reset functionality"
    ],
    "customer_response": "Acknowledge urgency, inform of investigation, offer alternative access options",
    "priority": "Immediate response required"
  }
}
}
```

### [Support Ticket Self-Consistency Example](#support-ticket-selfconsistency-example)

This conceptual example illustrates how Self-Consistency could be applied to support ticket categorization to reduce errors and increase reliability.

  
**Prompt:**

curl

```
SYSTEM: You're a support ticket analyst using Self-Consistency to categorize tickets.
For this implementation, we'll run the same analysis with different temperatures to generate multiple categorizations, then identify the most common result.

USER: Run the following Chain of Thought prompt 5 times with temperature=0.7 to classify this support ticket:

Ticket:
## Support Ticket ##

Ticket ID: TSK-2024-00123
Customer Name: Jane Doe
Customer Email: [email protected]
Customer ID: CUST-78910
Date Submitted: 2024-03-15 10:30 AM UTC
Product/Service: SuperWidget Pro
Subject: Cannot log in to my account

Issue Description:
I've been trying to log into my SuperWidget Pro account for the past 3 hours with no success. I keep getting an "Authentication Error (Code: 503)" message. I tried resetting my password, but I'm not receiving the reset email. I need urgent access to my project files for a client meeting this afternoon. My username is janedoe_widgets.
```

Output

**Run 1 (temp=0.7)**

This involves a login issue with error code 503 and missing password reset emails. Since it's primarily about account access rather than the functionality of the product itself, this falls under the Account Access category with Authentication sub-category. The urgency is High due to the client meeting. Classification:

JSON

```
{category: "Account Access", sub_category: "Authentication", urgency: "High"}
```

**Run 2 (temp=0.7)**

The customer is experiencing an Authentication Error (503) when trying to log in, and the password reset system isn't working. This is clearly a Technical Issue related to Authentication systems. Given the client meeting, urgency is High.

JSON

```
{category: "Technical Issue", sub_category: "Authentication", urgency: "High"}
```

**Run 3 (temp=0.7)**

Looking at the error code 503 and authentication failure, this is a Technical Issue. The sub-category is Authentication since it involves login systems and password reset functionality. The urgency is High due to business impact. Classification:

JSON

```
{category: "Technical Issue", sub_category: "Authentication", urgency: "High"}
```

**Run 4 (temp=0.7)**

This ticket describes an authentication problem with error code 503 and email delivery issues for password reset. It's a Technical Issue in the Authentication sub-category with High urgency. Classification:

JSON

```
{category: "Technical Issue", sub_category: "Authentication", urgency: "High"}
```

**Run 5 (temp=0.7)**

The customer can't log in (error 503) and isn't receiving password reset emails. This is a Technical Issue with the Authentication system. Urgency is High given the client meeting timeline. Classification:

JSON

```
{category: "Technical Issue", sub_category: "Authentication", urgency: "High"}
```

**Aggregated Results**

* "Technical Issue": 4 votes
* "Account Access": 1 vote

**Final Classification Based on Majority**

JSON

```
{category: "Technical Issue", sub_category: "Authentication", urgency: "High"}
```

### [Why These Approaches Work](#why-these-approaches-work)

**Guided CoT** works effectively for support ticket analysis because:

1. It ensures consistent application of organizational standards and categorization rules
2. The predefined steps guarantee comprehensive analysis of all important aspects
3. It makes the reasoning process transparent and auditable
4. The framework can encode specific business priorities or compliance requirements
5. It provides a quality control mechanism to prevent analysis gaps
  
**Self-Consistency** improves support ticket processing accuracy because:

1. Multiple reasoning paths help catch rare categorization or priority assessment errors
2. It provides increased confidence for critical decision points
3. When classifications disagree, it flags potentially ambiguous tickets for human review
4. It helps identify edge cases that might fall between standard categories
5. The consensus mechanism reduces the impact of occasional reasoning failures

### [Implementation Considerations](#implementation-considerations)

* **Guided CoT:** Can be implemented with a single prompt by providing the structured step-by-step framework.
* **Self-Consistency:** Requires multiple model calls (typically 5-20) with the same input but different temperature settings.
* **Hybrid approach:** For mission-critical tickets, consider combining both: use Guided CoT to ensure structured analysis, then apply Self-Consistency to verify the results.
* **Resource optimization:** Reserve Self-Consistency for high-priority or complex tickets where the additional compute cost is justified by the need for accuracy.
* **Confidence scoring:** Track agreement percentage across Self-Consistency runs to flag tickets that might need human review.

## [ReAct (Reasoning and Acting)](#react-reasoning-and-acting)

ReAct (Reasoning and Acting) is a prompt pattern that instructs an LLM to generate two interleaved streams:

1. **Thought / reasoning trace** \- natural-language reflection on the current state
2. **Action** \- a structured command that an external tool executes (e.g., `Search[query]`, `Calculator[expression]`, or `Call_API[args]`) followed by the tool's observation

Because the model can observe the tool's response and continue thinking, it forms a closed feedback loop. The model assesses the situation, takes an action to gather information, processes the results, and repeats if necessary.

### [When to use](#when-to-use)

| Use case                                                 | Why ReAct works                                                     |
| -------------------------------------------------------- | ------------------------------------------------------------------- |
| **Support ticket triage requiring contextual knowledge** | Enables lookup of error codes, known issues, and solutions          |
| **Ticket analysis needing real-time status checks**      | Can verify current system status and outage information             |
| **SLA calculation and breach determination**             | Performs precise time calculations with Python execution            |
| **Customer history-enriched responses**                  | Retrieves customer context from knowledge bases or documentation    |
| **Technical troubleshooting with diagnostic tools**      | Runs diagnostic scripts and interprets results                      |
| **Product-specific error resolution**                    | Searches documentation and knowledge bases for specific error codes |

### [Support Ticket ReAct Example](#support-ticket-react-example)

This example demonstrates how ReAct can be used to analyze a support ticket by accessing external information and performing calculations.

  
**Prompt:**

curl

```
SYSTEM: You are a support ticket analyst with the ability to think step-by-step and use tools to assist your analysis.
Available tools:
- SearchKnowledgeBase[query]: Searches the internal knowledge base for information.
- CalculateTimeDifference[start_time, end_time, time_zone]: Calculates the difference between two times.
- CheckSLA[ticket_id, issue_type]: Checks the SLA for a given ticket and issue type.

USER: Analyze this support ticket. Find any relevant information about the error code and assess whether there's an SLA breach. Provide your analysis as JSON.

Ticket:
## Support Ticket ##

Ticket ID: TSK-2024-00456
Customer Name: Michael Chen
Customer Email: [email protected]
Customer ID: CUST-92175
Date Submitted: 2024-03-15 15:45 PM UTC
Product/Service: SuperWidget Pro (Enterprise Plan)
Subject: Database sync failure with error DBS-4077

Issue Description:
Our production instance stopped syncing with our backup database at approximately 13:00 UTC today. The error console shows "Connection Failure: DBS-4077". According to our Enterprise SLA, sync issues should be resolved within 3 hours. This is affecting our reporting capabilities but not blocking customer transactions.
```

Output

**Thought**: I need to analyze this support ticket. There are three key tasks:

1. Understand the error code "DBS-4077".
2. Determine the time elapsed since the issue started.
3. Check if there's an SLA breach.

**First**, I'll search the knowledge base for information about the error code.

**Action**: SearchKnowledgeBase\["error code DBS-4077 SuperWidget Pro"\]

**Observation**: The knowledge base article KB00789 indicates that DBS-4077 is a "Database Synchronization Timeout" error for SuperWidget Pro. It's typically caused by network latency between the primary and replica database servers or an overloaded replica server. Recommended first steps include checking network connectivity and replica server load. This is classified as a P2 (Priority 2) issue.

**Thought**: Okay, DBS-4077 is a P2 database sync timeout. Now, I need to calculate the time elapsed. The issue started around 13:00 UTC, and the ticket was submitted at 15:45 UTC on the same day.

**Action**: CalculateTimeDifference\[start\_time="13:00 UTC", end\_time="15:45 UTC", time\_zone="UTC"\]

**Observation**: The time difference is 2 hours and 45 minutes.

**Thought**: The customer mentioned their Enterprise SLA for sync issues is 3 hours. I should verify this with our SLA tool.

**Action**: CheckSLA\[ticket\_id="TSK-2024-00456", issue\_type="Database Sync Failure"\]

**Observation**: For Enterprise Plan customers, the SLA for P2 Database Sync Failures is indeed 3 hours for resolution.

**Thought**: So, the issue has been ongoing for 2 hours and 45 minutes, and the SLA is 3 hours. This means there are only 15 minutes remaining in the SLA window.

**Final Answer**:

JSON

```
{
  "ticket_id": "TSK-2024-00456",
  "customer_info": {
      "name": "Michael Chen",
      "email": "[email protected]",
      "customer_id": "CUST-92175",
      "plan_type": "Enterprise Plan"
  },
  "issue_analysis": {
      "summary": "Production instance database sync failure with backup, error DBS-4077.",
      "error_code": "DBS-4077",
      "error_meaning": "Database Synchronization Timeout (P2)",
      "potential_causes": [
          "Network latency between primary and replica servers",
          "Overloaded replica server"
      ],
      "recommended_initial_steps": [
          "Check network connectivity between database servers",
          "Monitor replica server load"
      ],
      "category": "Technical Issue",
      "sub_category": "Database Synchronization",
      "priority_level": "P2",
      "impact_description": "Affecting reporting capabilities, but not blocking customer transactions."
  },
  "sla_assessment": {
      "sla_policy": "3 hours resolution for P2 Database Sync Failures (Enterprise Plan)",
      "issue_start_time_utc": "13:00",
      "ticket_submission_time_utc": "15:45",
      "time_elapsed_since_issue_start": "2 hours 45 minutes",
      "remaining_sla_time": "15 minutes",
      "sla_status": "At Risk",
      "sla_breach_imminent": true
  },
  "recommended_actions": {
      "internal_next_steps": [
          "Immediately assign to a database administrator or SRE.",
          "Investigate network latency and replica server load.",
          "Prepare for potential escalation if not resolved within 15 minutes."
      ],
      "customer_communication": "Acknowledge the ticket and the error. Inform the customer that we are aware of the 3-hour SLA and are actively investigating. Provide an update within 30 minutes or upon significant findings."
  }
}
```

### [Why This Works](#why-this-works)

ReAct is effective for support ticket analysis in this scenario because:

1. It enriches the ticket analysis with external knowledge about the specific error code
2. The external search provides context on the nature of the issue (network connectivity) that wasn't explicitly stated in the ticket
3. It identifies potential causes and recommended troubleshooting steps from documentation
4. The step-by-step reasoning process carefully evaluates the SLA situation by calculating elapsed time
5. The model can make a more informed assessment of urgency and escalation requirements based on gathered information
6. The resulting analysis combines ticket information with external knowledge to create a comprehensive assessment

This approach is particularly valuable for support teams dealing with specialized systems where specific error codes may require looking up technical documentation, and where SLA compliance is critical to monitor.

### [Implementation Tips](#implementation-tips)

* **Clear format specification:** Define the expected Thought/Action/Observation pattern explicitly in the system prompt
* **Tool selection:** Provide only the most relevant tools; too many options can confuse the model
* **Input structuring:** Pre-process tickets to highlight key fields like timestamps, error codes, and SLA requirements
* **Error handling:** Implement robust error handling for tool calls, as search results may be inconsistent
* **Observation management:** For lengthy search results or complex data, summarize observations to keep them focused
* **Connection to knowledge bases:** Consider connecting to internal knowledge bases rather than public search for proprietary systems
* **Security considerations:** Ensure sensitive customer information isn't exposed in external tool calls
* **Output standardization:** Format final answers as structured data (JSON) for integration with ticket management systems

## [Chain of Verification (CoVe)](#chain-of-verification-cove)

Chain of Verification (CoVe) prompting turns the model into its own fact-checker. It follows a four-phase process: first writing a draft analysis, then planning targeted verification questions, answering those questions independently to avoid bias, and finally producing a revised, "verified" response. This technique can reduce error rates significantly across knowledge-heavy tasks while adding only one extra round-trip latency.

### [When to use](#when-to-use)

| Use case                                   | Why CoVe works                                                    |
| ------------------------------------------ | ----------------------------------------------------------------- |
| **Support ticket categorization auditing** | Verifies proper categorization through targeted questions         |
| **SLA calculation verification**           | Double-checks time calculations and policy interpretation         |
| **Technical troubleshooting validation**   | Confirms logical connections between symptoms and causes          |
| **Customer response quality assurance**    | Ensures completeness and accuracy of draft responses              |
| **Incident impact assessment**             | Validates estimates of business impact through specific questions |
| **Error code interpretation**              | Cross-checks error code explanations against known documentation  |

### [Support Ticket Chain of Verification Example](#support-ticket-chain-of-verification-example)

This example demonstrates applying CoVe to analyze a customer support ticket, ensuring accuracy through self-verification.

  
**Prompt:**

curl

```
## Phase 1: Draft Analysis
USER: Analyze this support ticket and provide a complete assessment as JSON:

Ticket:
## Support Ticket ##

Ticket ID: TSK-2024-00123
Customer Name: Jane Doe
Customer Email: [email protected]
Customer ID: CUST-78910
Date Submitted: 2024-03-15 10:30 AM UTC
Product/Service: SuperWidget Pro
Subject: Cannot log in to my account

Issue Description:
I've been trying to log into my SuperWidget Pro account for the past 3 hours with no success. I keep getting an "Authentication Error (Code: 503)" message. I tried resetting my password, but I'm not receiving the reset email. I need urgent access to my project files for a client meeting this afternoon. My username is janedoe_widgets.

ASSISTANT (Draft):
{
"ticket_analysis": {
  "ticket_id": "TSK-2024-00123",
  "category": "Account Issue",
  "sub_category": "Login Problem",
  "urgency": "High",
  "impact": "Customer cannot access project files needed for client meeting",
  "error_codes": ["503"],
  "root_cause": "Password reset system failure",
  "recommended_action": "Reset password manually and investigate email delivery system"
}
}

## Phase 2: Verification Planning
ASSISTANT: To verify my analysis, I should check:
1. Is "Account Issue" the correct category, or should this be "Technical Issue"?
2. Does error code 503 relate to authentication specifically, or is it a general server error?
3. Is the root cause definitely a password reset system failure, or could it be authentication system failure?
4. Have I correctly assessed the urgency based on the timeline mentioned?
5. Is my recommended action complete and appropriate?

## Phase 3: Answer Verification Questions
ASSISTANT:
1. Reviewing the ticket, this appears to be a "Technical Issue" rather than "Account Issue" since it involves specific error codes and system functionality failures.
2. Error 503 is specifically described as an "Authentication Error" in the ticket, indicating it relates to the authentication system specifically.
3. The root cause is not definitively password reset system failure. There are two issues: authentication failure AND password reset emails not being received. The root cause could be either system or both.
4. The urgency is correctly assessed as "High" given the customer needs access for a client meeting "this afternoon."
5. The recommended action addresses the password reset but doesn't provide immediate access to files, which should be prioritized given the urgent meeting.

## Phase 4: Verified Analysis
USER: Based on your verification, provide a corrected analysis.

ASSISTANT:
{
"ticket_analysis": {
  "ticket_id": "TSK-2024-00123",
  "customer_info": {
    "name": "Jane Doe",
    "email": "[email protected]",
    "customer_id": "CUST-78910",
    "username": "janedoe_widgets"
  },
  "issue_details": {
    "category": "Technical Issue",
    "sub_category": "Authentication",
    "urgency": "High",
    "impact": "Customer cannot access project files needed for client meeting this afternoon",
    "error_codes": ["Authentication Error (503)"],
    "reported_symptoms": [
      "Cannot log into account",
      "Not receiving password reset emails"
    ]
  },
  "possible_causes": [
    "Authentication system failure",
    "Email delivery system issues",
    "Account flag requiring administrative intervention"
  ],
  "recommended_actions": [
    "Immediate: Provide temporary alternative access to project files",
    "Short-term: Manual password reset by admin",
    "Investigation: Check authentication system for Error 503",
    "Investigation: Verify email delivery system functionality"
  ],
  "response_priority": "Immediate - resolve before customer's afternoon meeting"
}
}
```

Output

JSON

```
{
  "ticket_analysis": {
      "ticket_id": "TSK-2024-00123",
      "customer_info": {
          "name": "Jane Doe",
          "email": "[email protected]",
          "customer_id": "CUST-78910",
          "username": "janedoe_widgets"
      },
      "issue_details": {
          "category": "Technical Issue",
          "sub_category": "Authentication",
          "urgency": "High",
          "impact": "Customer cannot access project files needed for client meeting this afternoon",
          "error_codes": ["Authentication Error (503)"],
          "reported_symptoms": [
              "Cannot log into account",
              "Not receiving password reset emails"
          ]
      },
      "possible_causes": [
          "Authentication system failure",
          "Email delivery system issues",
          "Account flag requiring administrative intervention"
      ],
      "recommended_actions": [
          "Immediate: Provide temporary alternative access to project files",
          "Short-term: Manual password reset by admin",
          "Investigation: Check authentication system for Error 503",
          "Investigation: Verify email delivery system functionality"
      ],
      "response_priority": "Immediate - resolve before customer's afternoon meeting"
  }
}
```

### [Why This Works](#why-this-works)

CoVe improves support ticket analysis accuracy because:

1. It creates space for the model to reconsider its initial categorization and assessment
2. The verification questions target specific aspects that might have errors or oversights
3. Answering each question independently reduces confirmation bias from the initial draft
4. The final analysis incorporates corrections identified during verification
5. The process mimics the quality control checkpoint that experienced support agents apply
6. Specific potential causes and recommended actions are better differentiated in the revised output

The approach is particularly valuable for tickets where accurate categorization affects routing, prioritization, and resolution approach. It reduces the likelihood of tickets being misrouted or incorrectly prioritized due to initial analysis errors.

### [Implementation Considerations](#implementation-considerations)

* **Process automation:** CoVe can be implemented as a pipeline with distinct prompts for each phase
* **Selective application:** Apply to high-priority tickets or those with ambiguous categorization to justify the additional processing time
* **Verification focus:** Customize verification questions based on your organization's most common analysis errors
* **Efficiency optimization:** Pre-define verification question templates for different ticket types
* **Integration points:** Consider implementing as a quality assurance step before ticket routing or customer response generation
* **Auditing value:** The verification questions and answers provide valuable transparency for training and process improvement

## [Chain of Density (CoD)](#chain-of-density-cod)

Chain of Density (CoD) is an iterative summarization technique that begins with a deliberately entity-sparse draft and progressively adds key entities while maintaining a fixed length. In each round, the model identifies 1-3 new entities it hasn't mentioned, then rewrites the summary: compressing existing text to make room for them. After several iterations, the summary achieves a higher entity-per-token density, reducing lead bias and often matching or exceeding human summaries in informativeness.

### [When to use](#when-to-use)

| Use case                               | Why CoD works                                                          |
| -------------------------------------- | ---------------------------------------------------------------------- |
| **Support ticket executive summaries** | Creates highly informative briefs within strict length limits          |
| **Agent handover notes**               | Ensures all critical details are captured in a concise format          |
| **Knowledge base entry creation**      | Progressively incorporates technical details without increasing length |
| **Customer communication summaries**   | Balances completeness with brevity for customer record notes           |
| **SLA/escalation notifications**       | Packs essential details into notification character limits             |
| **Support team daily digests**         | Summarizes multiple tickets with key details for management review     |

### [Support Ticket Chain of Density Example](#support-ticket-chain-of-density-example)

This example demonstrates using CoD to create progressively more information-dense summaries of a support ticket for different business purposes.

  
**Prompt:**

curl

```
SYSTEM: You are a detail-oriented support ticket summarizer.

USER: Support Ticket:
## Support Ticket ##

Ticket ID: TSK-2024-00123
Customer Name: Jane Doe
Customer Email: [email protected]
Customer ID: CUST-78910
Date Submitted: 2024-03-15 10:30 AM UTC
Product/Service: SuperWidget Pro
Subject: Cannot log in to my account

Issue Description:
I've been trying to log into my SuperWidget Pro account for the past 3 hours with no success. I keep getting an "Authentication Error (Code: 503)" message. I tried resetting my password, but I'm not receiving the reset email. I need urgent access to my project files for a client meeting this afternoon. My username is janedoe_widgets.

Task: Produce an increasingly dense summary of this ticket in **exactly 25±3 words**.
Run the following two-step loop **4 times**:
1. MissingEntities - List 1-2 NEW, salient entities (semicolon-separated) NOT yet in the summary.
2. DenserSummary - Rewrite the previous summary to include ALL prior entities PLUS the new ones, WITHOUT changing the word count limit.

Output as JSON array.
```

Output

JSON

```
[
  {
      "Round": 1,
      "MissingEntities": "Login issue; Authentication Error",
      "DenserSummary": "Customer cannot access account due to login issue. Authentication Error preventing access to project files needed urgently for client meeting."
  },
  {
      "Round": 2,
      "MissingEntities": "Error code 503; Password reset failure",
      "DenserSummary": "Customer experiencing Authentication Error (503) and password reset failure. Login issue blocking urgent access to project files for client meeting."
  },
  {
      "Round": 3,
      "MissingEntities": "Jane Doe; janedoe_widgets",
      "DenserSummary": "Jane Doe (janedoe_widgets) facing Authentication Error (503) and password reset failure. Login blocking urgent access to files for client meeting."
  },
  {
      "Round": 4,
      "MissingEntities": "TSK-2024-00123; Email delivery issue",
      "DenserSummary": "TSK-2024-00123: Jane Doe (janedoe_widgets) experiencing Authentication Error (503), password reset and email delivery issues. Urgent access needed for meeting."
  }
]
```

### [Why This Works](#why-this-works)

CoD is effective for support ticket summaries because:

1. It creates progressively more informative summaries while maintaining a consistent, manageable length
2. Each iteration deliberately adds key entities that were missing from previous versions
3. The process forces prioritization of the most important information elements
4. It ensures critical details (customer name, ticket ID, error code) are captured despite length constraints
5. The approach mitigates "lead bias" by considering the entire ticket, not just the opening lines
6. The resulting summaries are both concise and entity-rich, making them ideal for quick reviews

This technique is particularly valuable for creating ticket summaries that will be viewed in space-constrained interfaces such as dashboards, notifications, or mobile views, where maximum information density is essential.

### [Implementation Considerations](#implementation-considerations)

* **Word count customization:** Adjust the target word count based on your specific use case (e.g., Slack notifications, email subjects)
* **Entity priorities:** Customize the types of entities emphasized based on business needs (e.g., prioritize error codes for technical teams, SLAs for management)
* **Round optimization:** For most support tickets, 3-5 rounds achieves optimal density; more can lead to overly compressed language
* **Use case adaptation:** Create different CoD configurations for different outputs (e.g., shorter for notifications, longer for knowledge base entries)
* **Integration points:** Implement at summary generation points in your ticket workflow (e.g., ticket creation, escalation, resolution)
* **Multi-granular outputs:** Store all iterations to offer different summary densities for different consumers (e.g., tier 1 vs. management)
