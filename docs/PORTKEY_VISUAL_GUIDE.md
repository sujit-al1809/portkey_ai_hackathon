# 🎯 Portkey Integration - Visual Architecture & Step-by-Step

## How Portkey Solves Track 4 (Visual)

### The Three Models Problem

**Without Portkey:**
```
Your Code            APIs
   ↓                 ↓
┌─────────────────────────────────────┐
│  if model == "gpt-4o-mini":         │
│    openai.ChatCompletion.create()   │
│  elif model == "claude-3.5":        │
│    anthropic.messages.create()      │
│  elif model == "llama-2":           │
│    together_ai.complete()           │
│  elif model == "mistral":           │
│    mistral.chat()                   │
│  else:                              │
│    # 3 more models...               │
│                                     │
│  (7 different code paths!)          │
└─────────────────────────────────────┘
     ❌ Complex, error-prone
     ❌ Hard to maintain
     ❌ Lots of boilerplate
```

**With Portkey:**
```
Your Code        Portkey         APIs
   ↓              ↓              ↓
┌──────────────────────────────────────────┐
│ portkey_client.chat.completions.create(  │
│     model="gpt-4o-mini",                 │  ← Portkey figures out
│     messages=[...]                       │    which API to call
│ )                                        │
│                                          │
│ (Same code for ALL 7 models!)            │
└──────────────────────────────────────────┘
     ✅ Simple, clean
     ✅ Easy to maintain
     ✅ No boilerplate
     ✅ Scales to new models instantly
```

---

## Step-by-Step: How Portkey Processes Your Request

### Scenario: User Asks "How to optimize Python?"

```
┌─────────────────────────────────────────────────────────┐
│  USER REQUEST                                           │
│  "How do I optimize Python code?"                       │
└────────────────┬──────────────────────────────────────┘
                 ↓
        ┌────────────────────────┐
        │ SAVE TO HISTORY        │
        │ (in our SQLite DB)     │
        │ question: "How do I... │
        │ timestamp: now         │
        └────────┬───────────────┘
                 ↓
    ┌────────────────────────────────────────┐
    │  PORTKEY RECEIVES MULTI-MODEL REQUEST  │
    │                                         │
    │  for model in [gpt-4o-mini,            │
    │               gpt-3.5-turbo,           │
    │               claude-3.5-sonnet,       │
    │               llama-2,                 │
    │               mistral,                 │
    │               cohere,                  │
    │               palm-2]:                 │
    │                                         │
    │      portkey.chat.completions.create(  │
    │          model=model,                  │
    │          messages=[...]                │
    │      )                                 │
    └────────────────┬──────────────────────┘
                     ↓
    ┌────────────────────────────────────────────┐
    │  PORTKEY ROUTES TO PROVIDERS (PARALLEL)   │
    │                                            │
    │  Model "gpt-4o-mini"                       │
    │  ↓ Portkey detects OpenAI model            │
    │  ↓ Adds OpenAI API key (stored in Portkey) │
    │  ↓ Calls: openai.ChatCompletion.create()   │
    │  ↓ Gets: response, tokens, finish_reason   │
    │                                            │
    │  Model "claude-3.5-sonnet"                 │
    │  ↓ Portkey detects Anthropic model         │
    │  ↓ Adds Anthropic API key (in Portkey)     │
    │  ↓ Calls: anthropic.messages.create()      │
    │  ↓ Gets: response, tokens, finish_reason   │
    │                                            │
    │  Model "llama-2-70b"                       │
    │  ↓ Portkey detects Meta model              │
    │  ↓ Adds Meta API key (in Portkey)          │
    │  ↓ Calls: together_ai.complete()           │
    │  ↓ Gets: response, tokens, finish_reason   │
    │                                            │
    │  [... 4 more models in parallel ...]       │
    └────────────┬──────────────────────────────┘
                 ↓
    ┌────────────────────────────────────────┐
    │  PORTKEY STANDARDIZES RESPONSES        │
    │  (even though they came from 7         │
    │   different providers!)                │
    │                                         │
    │  All return same format:               │
    │  {                                     │
    │    choices: [{                         │
    │      message: { content: "..." },     │
    │      finish_reason: "stop"            │
    │    }],                                 │
    │    usage: {                            │
    │      prompt_tokens: 25,    ← Portkey   │
    │      completion_tokens: 150, ← gets    │
    │      total_tokens: 175    ← this!     │
    │    }                                   │
    │  }                                     │
    └────────────┬────────────────────────┘
                 ↓
    ┌────────────────────────────────────────┐
    │  OUR CODE PROCESSES STANDARDIZED DATA  │
    │                                         │
    │  for each_response in all_7_responses: │
    │                                         │
    │      # Step 1: Calculate cost          │
    │      cost = (tokens / 1000) ×          │
    │               MODEL_COST_RATE          │
    │      # Result: $0.00006, $0.000035,    │
    │      # $0.00012, etc for each model    │
    │                                         │
    │      # Step 2: Get quality via Judge   │
    │      quality = evaluate_with_portkey(  │
    │          response,                     │
    │          judge_model="claude-3.5"      │
    │      )                                 │
    │      # Result: 92%, 89%, 95%, etc      │
    │                                         │
    │      # Step 3: Check refusal           │
    │      is_refused = (                    │
    │          response.finish_reason ==     │
    │          'content_filter'              │
    │      )                                 │
    │      # Result: 0 refusals, 1 refusal   │
    └────────────┬────────────────────────┘
                 ↓
    ┌────────────────────────────────────────┐
    │  DATABASE STORAGE (Ours, not Portkey)  │
    │                                         │
    │  Store all results:                    │
    │  {                                     │
    │    gpt-4o-mini: {                      │
    │      response: "Use profiling...",     │
    │      cost: 0.00006,                    │
    │      quality: 0.923,                   │
    │      refusal_rate: 0.1%                │
    │    },                                  │
    │    gpt-3.5-turbo: {                    │
    │      response: "Try optimize lib...",  │
    │      cost: 0.000035,                   │
    │      quality: 0.895,                   │
    │      refusal_rate: 0.5%                │
    │    },                                  │
    │    [... 5 more models ...]             │
    │  }                                     │
    └────────────┬────────────────────────┘
                 ↓
    ┌────────────────────────────────────────┐
    │  GENERATE RECOMMENDATION               │
    │                                         │
    │  Compare all 7 models:                 │
    │                                         │
    │  gpt-3.5-turbo:                        │
    │  • Cost: 42.1% cheaper ✅              │
    │  • Quality: -3.2% lower ✓ (acceptable)│
    │  • Refusal: 0.5% (ok) ✓                │
    │                                         │
    │  → RECOMMEND: gpt-3.5-turbo            │
    └────────────┬────────────────────────┘
                 ↓
    ┌────────────────────────────────────────────┐
    │  RETURN RESULT TO USER                     │
    │                                             │
    │  {                                          │
    │    "recommended_model": "gpt-3.5-turbo",   │
    │    "reasoning": "Switching from            │
    │     gpt-4o-mini to gpt-3.5-turbo           │
    │     reduces cost by 42.1% with             │
    │     -3.2% quality impact",                 │
    │    "cost_reduction_percent": 42.1,         │
    │    "quality_impact_percent": -3.2,         │
    │    "models_compared": 7                    │
    │  }                                          │
    │                                             │
    │  → EXACTLY Track 4 expected output! ✅    │
    └────────────────────────────────────────────┘
```

---

## Portkey's Role at Each Stage

### Stage 1: Initial Prompt

```
Our Flask API
    ↓
    receives: "How do I optimize Python?"
    ↓
    stores in SQLite
    ↓
    ┌──────────────────────────────────┐
    │ PORTKEY STEPS IN HERE:           │
    │ "Send this prompt to 7 models"   │
    └──────────────────────────────────┘
```

**Portkey's Responsibility**:
- Know what gpt-4o-mini is (OpenAI)
- Know what claude-3.5-sonnet is (Anthropic)
- Know what llama-2-70b is (Meta)
- ... etc for all 7
- Route each call to the right provider
- Handle authentication automatically

---

### Stage 2: Multi-Model Evaluation

```python
# Our code (simple):
for model in models_list:
    response = portkey_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    process_response(response)

# What Portkey does (behind scenes):
#
# For "gpt-4o-mini":
#   • Recognizes OpenAI model
#   • Adds OPENAI_API_KEY (stored in Portkey)
#   • Calls OpenAI API
#   • Gets response, tokens, finish_reason
#
# For "claude-3.5-sonnet":
#   • Recognizes Anthropic model
#   • Adds ANTHROPIC_API_KEY (stored in Portkey)
#   • Calls Anthropic API
#   • Gets response, tokens, finish_reason
#
# [... etc for other providers ...]
```

**Portkey's Responsibility**:
- Manage all 7 API keys securely
- Know provider-specific formats
- Parallelize calls for speed
- Standardize responses
- Handle timeouts/retries

---

### Stage 3: Cost Calculation (Via Portkey Data)

```
Portkey Response:
┌─────────────────────────────────────┐
│ response.usage = {                  │
│   prompt_tokens: 25,        ← Portkey│
│   completion_tokens: 150,   ← tracked│
│   total_tokens: 175         ← these!│
│ }                                   │
└─────────────────────────────────────┘
         ↓
Our Calculation:
┌─────────────────────────────────────┐
│ for gpt-4o-mini:                    │
│   input_cost = (25 / 1000) ×        │
│                 0.00015 = $0.000004 │
│   output_cost = (150 / 1000) ×      │
│                  0.0006 = $0.00009  │
│   total = $0.000094                 │
│                                     │
│ for gpt-3.5-turbo:                  │
│   input_cost = $0.0000125           │
│   output_cost = $0.000225           │
│   total = $0.0002375                │
│   → 42.1% cheaper! ✅              │
└─────────────────────────────────────┘
```

**Portkey's Responsibility**:
- Return standardized token counts
- Works for all 7 providers
- Enables exact cost calculation

---

### Stage 4: Quality Evaluation (Using Portkey)

```
Original Response (from Model):
"Use cProfile for profiling, vectorize with NumPy..."
         ↓
         ├─ Keep in memory
         │
         ├─ Create evaluation prompt
         │
         └─ Send TO PORTKEY AGAIN!
            
            portkey_client.chat.completions.create(
                model="claude-3.5-sonnet",  ← Quality judge
                messages=[{
                    "role": "user",
                    "content": """
                    Rate this response:
                    Q: How to optimize Python?
                    A: Use cProfile...
                    
                    Rate on:
                    1. Accuracy (0-1)
                    2. Relevance (0-1)
                    3. Clarity (0-1)
                    """
                }]
            )
            ↓
            Claude (via Portkey):
            "accuracy: 0.95, relevance: 0.92, clarity: 0.89"
            ↓
            Our Calculation:
            quality = (0.95 × 0.4) + (0.92 × 0.35) + (0.89 × 0.25)
                    = 0.923 (92.3%)
```

**Portkey's Responsibility**:
- Provide access to Claude
- Return consistent evaluation format
- Works as our "judge" model

---

### Stage 5: Refusal Detection (Via Portkey)

```
Portkey returns for EVERY model response:
┌────────────────────────────────────┐
│ response.choices[0] = {            │
│   message: { content: "..." },    │
│   finish_reason: "stop"    ← Key! │
│ }                                  │
│                                    │
│ Possible finish_reason values:     │
│ • "stop" = normal completion       │
│ • "content_filter" = REFUSAL! 🚫  │
│ • "length" = too long              │
│ • "function_call" = tool use       │
└────────────────────────────────────┘
     ↓
Our Logic:
┌────────────────────────────────────┐
│ is_refusal = (                     │
│   finish_reason == 'content_filter'│
│ )                                  │
│                                    │
│ For gpt-4o-mini: False             │
│ For gpt-3.5-turbo: False           │
│ For claude: False                  │
│ → Success! No refusals             │
│                                    │
│ Over 1000 queries:                 │
│ gpt-3.5-turbo refused 5 times      │
│ refusal_rate = (5/1000) = 0.5%     │
└────────────────────────────────────┘
```

**Portkey's Responsibility**:
- Standardize finish_reason across providers
- Same field name for all 7 models
- Makes refusal detection easy

---

### Stage 6: Recommendation (Combining All Data)

```
Portkey gives us data, we analyze:

Model          Cost      Quality  Refusal  Decision
─────────────────────────────────────────────────
gpt-4o-mini    $0.00006  92.3%    0.1%     Original
gpt-3.5-turbo  $0.000035 89.1%    0.5%     ← RECOMMEND
               (-42.1%)  (-3.2%)           (best trade-off)
claude-3.5     $0.00018  95.0%    0.0%     Too expensive
llama-2        $0.00004  78.0%    2.0%     Quality too low
mistral        $0.00005  88.0%    1.0%     Avg trade-off
cohere         $0.00003  81.0%    3.0%     Low quality
palm-2         $0.00008  90.0%    0.2%     More expensive

Winner: gpt-3.5-turbo
Reason: Best cost reduction (42.1%) with acceptable 
        quality loss (only 3.2%) and low refusal rate (0.5%)
```

**Portkey's Responsibility**:
- Provided data for all 7 models
- Standardized format for comparison
- Made recommendation possible

---

## Code Examples: How Portkey Works

### Example 1: Initialize Portkey

```python
# File: backend/dashboard_api.py (top of file)

from portkey_ai import Portkey
import os

# ONE TIME: Initialize
portkey_client = Portkey(
    api_key=os.getenv('PORTKEY_API_KEY'),  # Your Portkey account
    virtual_key=os.getenv('VIRTUAL_KEY')   # API key auth
)

# Now you have access to ALL models!
# No need to initialize OpenAI, Anthropic, Meta separately
```

### Example 2: Call Single Model

```python
# Same code for ANY model
response = portkey_client.chat.completions.create(
    model="gpt-4o-mini",  # Change this, code stays same
    messages=[{
        "role": "user",
        "content": "How do I optimize Python?"
    }]
)

# Portkey figures out:
# • This is an OpenAI model
# • Find OpenAI API key in Portkey vault
# • Call OpenAI
# • Return response in standard format
```

### Example 3: Call Different Model (Same Code!)

```python
# Want to switch to gpt-3.5-turbo? Just change model name!
response = portkey_client.chat.completions.create(
    model="gpt-3.5-turbo",  # ← Changed
    messages=[{
        "role": "user",
        "content": "How do I optimize Python?"
    }]
)

# Portkey figures out:
# • This is ALSO an OpenAI model
# • Use same OpenAI API key
# • Call OpenAI
# • Return in same format
```

### Example 4: Different Provider (Still Same Code!)

```python
# Want Claude from Anthropic? Same code structure!
response = portkey_client.chat.completions.create(
    model="claude-3.5-sonnet",  # ← Different provider!
    messages=[{
        "role": "user",
        "content": "How do I optimize Python?"
    }]
)

# Portkey figures out:
# • This is Anthropic model
# • Find Anthropic API key in Portkey vault
# • Call Anthropic API (handles format differences)
# • Return in SAME standard format as OpenAI
```

**That's Portkey's magic**: Same code for 7 different models from 6 different companies!

---

## Why Track 4 Judges Will Be Impressed

**Without Portkey**: 
```
To support 7 models, you'd need ~500 lines of code
handling provider-specific APIs
```

**With Portkey**:
```
To support 7 models, you need ~100 lines of code
+ Portkey handles the complexity
```

**What judges see**:
- ✅ Clean code
- ✅ Works for all 7 models
- ✅ Easy to add more models
- ✅ Professional architecture
- ✅ Production-ready

---

## Summary: Portkey Powers Track 4

| Track 4 Requirement | Portkey Enables It | Code Location |
|-------------------|------------------|---------------|
| Replay data | Unified API for all models | dashboard_api.py #550 |
| Multi-model eval | Routes to 7 providers | dashboard_api.py #550-650 |
| Cost measurement | Provides token counts | dashboard_api.py #300 |
| Quality measurement | Can call judge model | dashboard_api.py #300 |
| Refusal detection | Standardizes finish_reason | dashboard_api.py #635 |
| Trade-off recommendation | All data in one format | dashboard_api.py #341 |

**Portkey = The infrastructure that makes everything possible.** ✅
