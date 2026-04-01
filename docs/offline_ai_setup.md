# AI Assistant Setup (No API Key Required) 🤖🔌

You can set up a high-performance AI coding assistant in your editor without needing a personal Gemini or OpenAI API key. Here are the two best options:

---

## Option 1: No-Key Cloud AI (Easiest) ☁️
**Recommended Extension: [Codeium](https://codeium.com/vscode)**

Codeium is a powerful, free alternative to GitHub Copilot. It does **not** require an API key—you simply log in with your Google or GitHub account.

### 1. Installation
1.  Open your editor's **Extensions** view (`Cmd+Shift+X`).
2.  Search for **"Codeium"** and install it.
3.  Click the Codeium icon in the status bar and select **"Sign In"**.
4.  Follow the browser prompts to log in (Free Tier).

### 2. Features
-   **Autocomplete**: Real-time code suggestions as you type.
-   **Chat**: Ask questions about your codebase.
-   **Search**: Find anything in your repository using natural language.

---

## Option 2: 100% Offline Local AI (Private) 🏠
**Recommended Setup: [Continue](https://www.continue.dev/) + [Ollama](https://ollama.com/)**

If you want to work completely offline with zero data leaving your machine, you can run a local model. This requires a computer with at least 8GB of RAM.

### 1. Install Ollama
1.  Download and install **Ollama** from [ollama.com](https://ollama.com/).
2.  Open your terminal and pull a coding model:
    ```bash
    ollama run qwen2.5-coder:7b
    ```

### 2. Install Continue Extension
1.  Search for **"Continue"** in your editor's Extensions view and install it.
2.  Open the Continue sidebar and click the **Gear Icon** (Settings).
3.  In the `models` section of the `config.json`, add this snippet:
    ```json
    {
      "title": "Local Qwen (Offline)",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b"
    }
    ```

### 3. Features
-   **No Internet Required**: Works 100% offline.
-   **Zero API Keys**: No keys, no tokens, no tracking.
-   **Local Intelligence**: All reasoning happens on your CPU/GPU.

---

## Summary Comparison

| Goal | Use Option... | Why? |
| --- | --- | --- |
| **I want speed & ease** | **Option 1 (Codeium)** | High-speed cloud AI, zero setup. |
| **I want 100% Privacy** | **Option 2 (Ollama)** | Data never leaves your machine. |
| **I have an API Key** | **Continue** | Link your Gemini Key for max power. |
