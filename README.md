# CodeDoctor AI — Specialized Code Review & Bug Diagnostic Assistant

An intelligent, real-time code reviewer chatbot powered by Groq LPUs, FastAPI, and an iteratively engineered prompt system.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher
- A free Groq API key from [https://console.groq.com/keys](https://console.groq.com/keys)

### 2. Installation
Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the root directory (or rename `.env.example` to `.env`) and add your Groq key:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
```

### 4. Run the Application
Launch the application server:
```bash
python app.py
```
*(or run `uvicorn app:app --reload --port 8000`)*

Open your browser and navigate to:
👉 **http://127.0.0.1:8000**

---

## 🧪 Testing the Chatbot & Evaluating V1 vs. V2

This application includes a built-in **Rule & Persona Switcher** to demonstrate the prompt engineering lifecycle:

1. **Test Improved Version (V2 - Active by default)**:
   - Try the prompt: *"Can you give me a quick recipe for chocolate chip cookies?"*
   - **Result**: The chatbot enforces strict boundary refusal:
     > *"I am CodeDoctor, specialized strictly in code diagnostics, debugging, and software review. Please provide a code snippet or programming question."*

2. **Test Baseline Version (V1 - Pre-Fix)**:
   - Click **"Rules & Model"** in the top navigation.
   - Switch persona to **`CodeDoctor V1 (Unrestricted / Pre-Fix)`**.
   - Ask the same cookie question.
   - **Result**: Notice that V1 breaks character and outputs a baking recipe, proving role drift!

3. **Test Code Diagnosis**:
   - Provide buggy code such as:
     ```python
     def append_to_list(val, my_list=[]):
         my_list.append(val)
         return my_list
     ```
   - **Result**: CodeDoctor outputs a 4-part structured diagnosis (Diagnosis, Severity, Fixed Code, Big-O Complexity).

---

## 📁 Project Structure

```
├── app.py              # FastAPI backend with Groq streaming completions
├── index.html          # Modern dark-mode web interface with real-time SSE stream
├── static/             # Static file mirror for web serving
├── requirements.txt    # Python dependencies (fastapi, uvicorn, groq, python-dotenv)
├── .env.example        # Environment variable template
├── PROJECT_REPORT.md   # Complete academic project report with evaluation metrics
└── README.md           # Instructions and documentation
```
