# EduGen - AI-Powered Educational Content Generator

A research prototype that uses AI to generate personalized educational content for students and tutors.

## What is EduGen?

EduGen helps create tailored educational content:
- **For Students**: Simplifies complex course material into easy-to-understand explanations
- **For Tutors**: Generates lesson plans, study guides, and teaching materials

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt

2. **Set up Environment Variables**:
    ```bash
    # Create .env file with your Groq API keys
    GROQ_API_KEY_1=your_first_groq_key
    GROQ_API_KEY_2=your_second_groq_key

3. **Run the App**:
    ```bash
    streamlit run app.py

4. **Recommended .env Template**:
    ```bash
    # .env
    # Get your Groq API key from: https://console.groq.com
    # 1. Go to console.groq.com
    # 2. Create account/login
    # 3. Click "API Keys" in top right
    # 4. Create new key and copy it
    # 5. Paste below:

    # Minimum setup (one key):
    GROQ_API_KEY_1=your_actual_groq_key_here

    # Optional: Add second key for better reliability:
    # GROQ_API_KEY_2=your_second_groq_key_here