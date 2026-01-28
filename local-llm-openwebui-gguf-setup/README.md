# Local LLM setup using open web ui and gguf models
Flexible UI to run multiple large language models (LLMs) locally or semi-locally, support quantised formats (GGUF), use multiple model variants (Qwen, deepseek-ai, openai/gpt-oss, nvidia/Nemotron) and present them via a clean ChatUI. They needed a system where models could be swapped, configured, tested quickly, and used via a unified UI rather than each model having its own adhoc interface.

# Tech Stack
- Python
- FastAPI
- Python dotenv
- SQL Alchemy (ORM)
- StructLog
- Async implementation
- Poetry (package manager)
- Open WebUI
- LLAMA C++

# Working video
View the working offline LLM in video https://www.loom.com/embed/010c506688ae4c5ab29649671cf7e027

---
Disclaimer: This repository contains code that has been modified for security and privacy reasons before being made open source. Its primary purpose is to contribute to the developer community and support learning. Some parts may require refactoring to run as intended. This code is provided for educational purposes only and without warranty of any kind.