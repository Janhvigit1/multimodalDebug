Multimodal Debugger: Advanced Multi-Agent Consensus System

An advanced, multimodal developer tool that leverages state-of-the-art LLMs to analyze, debug, and provide consensus-driven resolutions for code snippets. The application supports code submission via raw text paste or screenshot uploads.

 Key Features

Multimodal Input Support: Submit raw code or simply upload a screenshot of your buggy code/terminal error.

Separation of Vision & Reasoning: * Google Gemini 2.5 Flash acts as the Vision Engine to extract raw text from screenshots.

Groq Cloud (Llama 3.3 70B) and Local Ollama (Llama 3 8B) perform pure logical reasoning and debugging concurrently on the extracted/submitted code.

Multi-Agent Consensus: A master voting engine reviews all individual model diagnoses to produce a unified, optimized "Consensus Winner" code.

Inference Speed Analytics: Real-time response latencies are calculated and plotted on an interactive bar chart.

Persistent DB Storage: Utilizes a local SQLite database to store debugging history securely, allowing users to restore previous workspaces with a single click.

Sleek, Clean UI: A custom-styled, professional dark theme interface with hidden default Streamlit deployment banners for a native software experience.

🛠️ System Architecture

                   ┌────────────────────────┐
                   │    User Code / Image   │
                   └───────────┬────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       [ Screenshot ]                     [ Raw Code ]
               │                               │
     (Gemini Vision OCR)                       │
               │                               │
               ▼                               ▼
       ┌───────────────────────────────────────────────┐
       │             Unified Code Context              │
       └───────┬───────────────┬───────────────┬───────┘
               │               │               │
               ▼               ▼               ▼
         ┌───────────┐   ┌───────────┐   ┌───────────┐
         │  Gemini   │   │   Groq    │   │  Ollama   │
         │ 2.5 Flash │   │ Llama 3.3 │   │ (Local)   │
         └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
               │               │               │
               └───────────────┼───────────────┘
                               ▼
                ┌─────────────────────────────┐
                │   Master Consensus Engine   │
                └──────────────┬──────────────┘
                               ▼
                ┌─────────────────────────────┐
                │  Optimized Winner Solution  │
                └─────────────────────────────┘


Installation & Setup

1. Clone the Repository

git clone <your-repository-url>
cd <repository-folder>


2. Install Dependencies

pip install -r requirements.txt


3. Setup Environment Variables

Create a .env file in the root directory and add your API keys:

GEMINI_API_KEY="your_gemini_api_key"
GROQ_API_KEY="your_groq_api_key"


4. Run the Application

python3 -m streamlit run app.py


Note: Ensure your local Ollama app is running on port 11434 with llama3:8b installed.

 Deployment (Streamlit Community Cloud)

Push your code (excluding the .env file) to a public GitHub repository.

Sign in to Streamlit Share using your GitHub account.

Click on Create App and select your repository, branch, and app.py as the entry file.

Go to Advanced Settings -> Secrets and paste your credentials securely:

GEMINI_API_KEY = "your_gemini_api_key_here"
GROQ_API_KEY = "your_groq_api_key_here"


Click Deploy! Your app will be live globally in under 2 minutes.