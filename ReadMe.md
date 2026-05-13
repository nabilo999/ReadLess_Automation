# Read Less

A simple automation tool that downloads PDFs from Google Drive, extracts the text, optionally cleans it with AI, converts it into audio, and emails the audio files to you on a schedule.

---

# How to Use

## 1. Install Dependencies

Run the following commands:

```bash
pip install google-api-python-client google-auth
pip install pypdf
pip install gtts
pip install python-dotenv

# Optional AI features
pip install openai
```

---

## 2. Create a `.env` File

Create a `.env` file in the root directory of the project.

Add the following:

```env
# Google Drive service account credentials
SERVICE_ACCOUNT_FILE=credentials.json

# Google Drive folder ID containing PDFs
FOLDER_ID=your_folder_id

# Local folders
DOWNLOAD_DIR=downloads
TEXT_DIR=text
AUDIO_DIR=audio

# How many days back to search for PDFs
DAYS_BACK=0

# Email settings
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Optional features
CLEAN_TEXT=true
PREMIUM_TTS=true

# Only needed if using AI features
OPENAI_API_KEY=your_openai_api_key
```

---

## 3. Run the Program

```bash
python main.py
```