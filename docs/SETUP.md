# Setup Guide - Cost-Quality Optimization System

## Quick Setup (5 minutes)

### Step 1: Get Portkey API Key

1. Go to [https://app.portkey.ai](https://app.portkey.ai)
2. Sign up / Log in
3. Navigate to **API Keys** section
4. Click **Create API Key**
5. Copy your API key

### Step 2: Configure Virtual Keys

You need to set up virtual keys for the providers you want to test:

1. In Portkey dashboard, go to **Virtual Keys**
2. Click **Add Key**
3. For each provider:
   - **OpenAI**: Add your OpenAI API key
   - **Google**: Add your Google AI API key  
   - **Anthropic**: Add your Anthropic API key

### Step 3: Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:PORTKEY_API_KEY="your-portkey-api-key"
```

**Linux/Mac:**
```bash
export PORTKEY_API_KEY="your-portkey-api-key"
```

Or create a `.env` file:
```bash
cp .env.example .env
# Edit .env and add your API key
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Update Config

Edit `config.py` and update the `MODELS_TO_TEST` section with your actual provider names from Portkey:

```python
MODELS_TO_TEST = [
    {
        "name": "GPT-4o-mini",
        "provider": "openai",  # Your virtual key name in Portkey
        "model": "gpt-4o-mini",
        "expected_cost_per_1k_input": 0.00015,
        "expected_cost_per_1k_output": 0.0006
    },
    # ... add more models
]
```

### Step 6: Run Demo

```bash
python main.py
```

---

## Troubleshooting

### Error: "Connection error"

**Problem**: Can't connect to Portkey gateway

**Solution**: 
1. Check your internet connection
2. Verify PORTKEY_API_KEY is set: `echo $env:PORTKEY_API_KEY`
3. Make sure API key is valid in Portkey dashboard

### Error: "Provider virtual key not found"

**Problem**: Virtual keys not configured

**Solution**:
1. Go to Portkey dashboard → Virtual Keys
2. Make sure you've added keys for OpenAI, Google, Anthropic
3. Update `config.py` with the exact provider names

### Error: "Rate limit exceeded"

**Problem**: Too many requests to a provider

**Solution**:
1. Reduce number of models in `MODELS_TO_TEST`
2. Increase `RETRY_DELAY` in config
3. Add more provider API keys in Portkey

### Low Quality Scores

**Problem**: LLM-as-judge giving low scores

**Solution**:
1. This is normal - the judge is strict
2. Scores are relative, so recommendations still work
3. You can adjust `EVALUATION_CRITERIA` in config

### No Recommendation Generated

**Problem**: System says "More data needed"

**Solution**:
1. Add more sample prompts (minimum 10)
2. Lower `MIN_SAMPLE_SIZE` in config
3. Check `optimization_results.json` for raw data

---

## Customization

### Add More Models

Edit `config.py`:

```python
MODELS_TO_TEST = [
    # ... existing models ...
    {
        "name": "Your-Model",
        "provider": "your-provider-virtual-key",
        "model": "model-name",
        "expected_cost_per_1k_input": 0.001,
        "expected_cost_per_1k_output": 0.002
    }
]
```

### Change Evaluation Criteria

Edit `config.py`:

```python
EVALUATION_CRITERIA = {
    "custom_criterion": "Your evaluation question?",
    "another_criterion": "Another question?"
}
```

Update `quality_evaluator.py` to match your criteria in the JSON schema.

### Adjust Confidence Thresholds

Edit `config.py`:

```python
MIN_CONFIDENCE_SCORE = 0.6  # Lower = more recommendations
MIN_SAMPLE_SIZE = 5  # Lower = faster recommendations
```

### Add Your Own Prompts

Edit `main.py`:

```python
def create_sample_prompts():
    prompts = [
        PromptData(
            id="your_prompt_id",
            messages=[
                {"role": "user", "content": "Your prompt here"}
            ],
            original_model="Current-Model"
        ),
        # ... more prompts
    ]
    return prompts
```

---

## Production Deployment

### Option 1: Continuous Background Service

```bash
# Run in background
nohup python continuous_mode.py > optimization.log 2>&1 &
```

### Option 2: Scheduled Batch Processing

```bash
# Add to cron (Linux) or Task Scheduler (Windows)
# Run every hour
0 * * * * cd /path/to/project && python main.py
```

### Option 3: Docker Container

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "continuous_mode.py"]
```

---

## Monitoring Production

### Check Logs

```bash
tail -f optimization.log
```

### View Results

```bash
cat optimization_results.json | python -m json.tool
```

### Check State

```bash
cat replay_state.json | python -m json.tool
```

---

## Integration with Portkey Dashboard

All requests are automatically logged in Portkey:

1. Go to [app.portkey.ai](https://app.portkey.ai)
2. Navigate to **Logs**
3. You'll see all model requests with:
   - Cost per request
   - Latency
   - Token usage
   - Request/response details

Use this data to validate the optimization recommendations!

---

## Getting Help

- **Portkey Docs**: [https://portkey.ai/docs](https://portkey.ai/docs)
- **Discord**: [Portkey Community](https://portkey.wiki/community)
- **Issues**: Check GitHub issues or create new one

---

## Next Steps

1. ✅ Get basic demo working
2. ✅ Add your real prompts from production
3. ✅ Let it run for a few hours/days
4. ✅ Review recommendations
5. ✅ Implement model switches
6. ✅ Monitor cost savings
7. ✅ Scale to continuous operation

---

**You're ready to optimize! 🚀**
