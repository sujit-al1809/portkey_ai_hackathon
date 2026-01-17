# 📁 Repository Structure

```
portkey_ai_hackathon/
│
├── 📄 main.py                      # Main demo entry point
├── 🔄 continuous_mode.py           # Continuous monitoring daemon
├── ⚙️  config.py                    # Configuration settings
├── 📊 models.py                    # Data models (Pydantic/dataclass)
├── 🔄 replay_engine.py             # Multi-model replay system
├── ⚖️  quality_evaluator.py         # LLM-as-judge evaluation
├── 📈 optimizer.py                 # Cost-quality trade-off analysis
├── 💾 state_manager.py             # State persistence & caching
├── 🔁 continuous_monitor.py        # Continuous operation orchestrator
│
├── 📚 docs/                        # Documentation
│   ├── 📖 SETUP.md                 # Detailed setup instructions
│   ├── 🎤 PITCH.md                 # Project pitch deck
│   └── 📋 PROJECT_SUMMARY.md       # Complete project overview
│
├── 🧪 tests/                       # Test files
│   ├── ✅ test_config.py           # Configuration validation
│   ├── 🚀 simple_test.py           # Simple API test
│   └── 📝 quickstart.py            # Quick start guide
│
├── 💾 data/                        # Data storage (gitignored)
│   ├── replay_state.json           # Processing state
│   ├── optimization_results.json   # Optimization results
│   └── evaluation_cache.json       # Evaluation cache
│
├── 🔧 Configuration Files
│   ├── .env.example                # Environment variables template
│   ├── .gitignore                  # Git ignore patterns
│   └── requirements.txt            # Python dependencies
│
├── 📖 Documentation
│   ├── README.md                   # Main documentation (you are here)
│   ├── CONTRIBUTING.md             # Contribution guidelines
│   └── LICENSE                     # MIT License
│
└── 🗂️  Other
    ├── venv/                       # Virtual environment (gitignored)
    └── __pycache__/                # Python cache (gitignored)
```

## 📊 Component Overview

### Core Components

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| 🔄 **Replay Engine** | Multi-model testing | Retries, timeout handling, cost tracking |
| ⚖️ **Quality Evaluator** | LLM-as-judge | Dimensional scoring, confidence levels |
| 📈 **Optimizer** | Trade-off analysis | Statistical analysis, recommendations |
| 💾 **State Manager** | Persistence | Incremental processing, caching |
| 🔁 **Continuous Monitor** | Orchestration | Continuous operation, batch processing |

### Data Flow

```
📥 Prompts → 🔄 Replay Engine → ⚖️ Quality Evaluator → 📈 Optimizer → 💾 State Manager → 📊 Recommendations
```

### File Sizes (Approximate)

- **Source Code**: ~2,000 lines
- **Documentation**: ~1,500 lines
- **Tests**: ~300 lines
- **Total Project**: ~4,000 lines

## 🎯 Quick Navigation

- 🚀 [Getting Started](../README.md#-quick-start)
- ⚙️ [Configuration](../README.md#-configuration)
- 📊 [How It Works](../README.md#-how-it-works)
- 🏆 [Why This Wins](../README.md#-why-this-wins)
- 🤝 [Contributing](../CONTRIBUTING.md)

## 📝 File Descriptions

### Main Application Files

- **main.py**: Demo entry point with sample prompts
- **continuous_mode.py**: Long-running daemon for continuous monitoring
- **config.py**: Central configuration for models, thresholds, criteria

### Core Logic

- **replay_engine.py**: Handles multi-model API calls with retry logic
- **quality_evaluator.py**: Implements LLM-as-judge evaluation
- **optimizer.py**: Analyzes cost-quality trade-offs
- **state_manager.py**: Manages persistence and caching
- **continuous_monitor.py**: Orchestrates the entire pipeline

### Data Models

- **models.py**: Pydantic/dataclass definitions for:
  - PromptData
  - CompletionResult
  - QualityScore
  - OptimizationRecommendation

### Documentation

- **README.md**: Main project documentation
- **docs/SETUP.md**: Detailed setup instructions
- **docs/PITCH.md**: Project pitch and value proposition
- **docs/PROJECT_SUMMARY.md**: Comprehensive overview
- **CONTRIBUTING.md**: How to contribute

### Tests

- **tests/test_config.py**: Validates Portkey configuration
- **tests/simple_test.py**: Quick API connectivity test
- **tests/quickstart.py**: Interactive getting started guide

## 🔄 Data Persistence

All data files are stored in the `data/` directory:

```
data/
├── replay_state.json           # Current processing state
├── optimization_results.json   # Historical recommendations
└── evaluation_cache.json       # Cached quality evaluations
```

These files enable:
- ♾️ Continuous operation
- 🚫 No duplicate work
- 📊 Historical analysis
- 🔄 Resume from crashes

## 🛠️ Development Workflow

1. **Setup**: Create venv, install requirements
2. **Configure**: Set Portkey API key, configure models
3. **Test**: Run test_config.py to validate setup
4. **Develop**: Make changes to core components
5. **Test**: Run simple_test.py and main.py
6. **Deploy**: Run continuous_mode.py for production

---

**📚 For more details, see the [README](../README.md)**
