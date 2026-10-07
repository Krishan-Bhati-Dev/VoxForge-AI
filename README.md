# 🎙️ VoxForge AI

**AI-powered Blog-to-Podcast Generator**

VoxForge AI converts online blog articles into podcast-style audio using AI. Simply provide a blog URL, and the application extracts the content, generates a conversational podcast script, and converts it into speech.

## ✨ Features

* 🔗 Blog URL → Content extraction
* 🤖 AI-generated podcast script
* 🎙️ Text-to-speech audio generation
* 🔊 ElevenLabs & Edge TTS support
* ⚡ Streamlit web interface
* 🔐 Secure API key management using `.env`

## 🏗️ Workflow

```text
Blog URL
   ↓
Firecrawl
   ↓
Article Content
   ↓
AI Agent
   ↓
Podcast Script
   ↓
Text-to-Speech
   ↓
🎙️ Podcast Audio
```

## 🛠️ Tech Stack

* **Python**
* **Streamlit**
* **Agno**
* **Firecrawl**
* **OpenAI / OpenAI-compatible API**
* **ElevenLabs**
* **Edge TTS**
* **Pydub**

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/Krishan-Bhati-Dev/Blog-to-Podcast.git
cd Blog-to-Podcast
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Create a `.env` file:

```env
OPENROUTER_API_KEY=your_api_key
ELEVENLABS_API_KEY=your_api_key
FIRECRAWL_API_KEY=your_api_key
```

**Never upload `.env` or expose your API keys.**

### 5. Run

```bash
streamlit run app.py
```

## 🚀 Future Scope

* 🎬 AI-generated video podcasts
* 👥 Multi-speaker conversations
* 🌐 Multilingual podcast generation
* 📚 Batch processing of multiple articles
* ☁️ Cloud deployment
* 📡 Automated podcast publishing

## 👨‍💻 Author

**Krishan Bhati**
B.Tech CSE — Artificial Intelligence & Machine Learning

GitHub: [Krishan-Bhati-Dev](https://github.com/Krishan-Bhati-Dev)
