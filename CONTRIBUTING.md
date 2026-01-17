# 🤝 Contributing to Cost-Quality Optimization System

First off, thank you for considering contributing to this project! 🎉

## 🌟 Ways to Contribute

- 🐛 Report bugs
- 💡 Suggest new features
- 📝 Improve documentation
- 🔧 Submit pull requests
- ⭐ Star the project

## 🚀 Getting Started

### Prerequisites

- 🐍 Python 3.8+
- 🔑 Portkey API account
- 💻 Git installed

### Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/portkey_ai_hackathon.git
   cd portkey_ai_hackathon
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Portkey API key
   ```

## 📝 Development Guidelines

### Code Style

- ✅ Use type hints
- ✅ Follow PEP 8
- ✅ Write docstrings for functions
- ✅ Keep functions focused and small
- ✅ Use meaningful variable names

### Testing

Before submitting a PR:

```bash
# Run configuration test
python tests/test_config.py

# Run simple API test
python tests/simple_test.py

# Test the main flow
python main.py
```

### Commit Messages

Use conventional commits:

- ✨ `feat:` New feature
- 🐛 `fix:` Bug fix
- 📝 `docs:` Documentation changes
- 🔧 `chore:` Maintenance tasks
- ♻️ `refactor:` Code refactoring

Example:
```
feat: add support for Claude 3.5 Sonnet model
fix: handle timeout errors in replay engine
docs: update README with new configuration options
```

## 🔀 Pull Request Process

1. Create a new branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

3. Push to your fork:
   ```bash
   git push origin feat/your-feature-name
   ```

4. Open a Pull Request with:
   - 📋 Clear description of changes
   - 🎯 Why the change is needed
   - 🧪 How you tested it
   - 📸 Screenshots (if UI changes)

## 🐛 Reporting Bugs

When reporting bugs, please include:

- 📝 Clear description of the issue
- 🔄 Steps to reproduce
- 🎯 Expected behavior
- 💥 Actual behavior
- 💻 Environment (OS, Python version)
- 📋 Error messages/logs

## 💡 Suggesting Features

We love new ideas! Please include:

- 🎯 Clear use case
- 💼 Business value
- 🏗️ Technical approach (if applicable)
- 📊 Impact assessment

## 📚 Documentation

Help improve our docs:

- 📖 Fix typos
- ✨ Add examples
- 🔍 Clarify confusing sections
- 🌍 Translations

## 🎓 Code Review Process

All submissions require review. We aim to:

- ⚡ Review within 48 hours
- 💬 Provide constructive feedback
- 🤝 Work with you to improve the PR
- 🎉 Merge when all checks pass

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Your contributions make this project better for everyone! 🌟

---

**Questions?** Feel free to open an issue or reach out to the maintainers! 📧
