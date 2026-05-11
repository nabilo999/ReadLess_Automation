# Time keeping stuff
from datetime import datetime, timedelta
# Google Drive stuff
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
# PDF Reading and Extracting text
from pypdf import PdfReader
# Generating TTS
from gtts import gTTS
# Environment variable stuff
import os
import io
from dotenv import load_dotenv
# Email stuff
import smtplib
from email.message import EmailMessage
# For cleaning text (optional)
from openai import OpenAI

# Load .env
load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
FOLDER_ID = os.getenv("FOLDER_ID")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
TEXT_DIR = os.getenv("TEXT_DIR")
AUDIO_DIR = os.getenv("AUDIO_DIR")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM") 
EMAIL_TO = os.getenv("EMAIL_TO") 
DAYS_BACK = int(os.getenv("DAYS_BACK", 0))
CLEAN_TEXT = os.getenv("CLEAN_TEXT")
PREMIUM_TTS = os.getenv("PREMIUM_TTS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# connect to Google Drive API using service account credentials
def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)

# calculate the target date (eg: get the files for next week)
def get_target_date():
    target = datetime.today() + timedelta(days=DAYS_BACK)
    return target.strftime('%Y-%m-%d')  # match your filename format

#extract text from the PDF line by line
def extract_text(pdf_path):
    text = ''
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + '\n'
    return text.strip()

# save text to file to be used in TTS later
def save_text(text, filename_stem):
    os.makedirs(TEXT_DIR, exist_ok=True)
    text_path = os.path.join(TEXT_DIR, f'{filename_stem}.txt')

    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"Text saved to {text_path}")
    return text_path

# clean extracted PDF text using LLM
def clean_text_with_llm(text):

    # skip cleaning if disabled
    if str(CLEAN_TEXT).lower() != "true":
        return text

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You clean messy PDF extracted text. "
                        "Remove page numbers, headers, footers, URLs, repeated junk, "
                        "broken line breaks, random symbols, and formatting issues. "
                        "Fix split words and make the text readable while preserving meaning. "
                        "Do not summarize. Return only cleaned text."
                    )
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.1,
        )

        cleaned_text = response.choices[0].message.content.strip()

        print("Text cleaned with GPT")
        return cleaned_text

    except Exception as e:
        print(f"Error cleaning text with GPT: {e}")
        return text

# convertting to audio
def convert_to_audio(text, filename_stem):
    # check if directory exists and generate audio path
    os.makedirs(AUDIO_DIR, exist_ok=True)
    audio_path = os.path.join(AUDIO_DIR, f'{filename_stem}.mp3')

    try:
        # PREMIUM MODE → OpenAI TTS
        if PREMIUM_TTS:
            print("Using OpenAI premium TTS...")
            response = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="nova",
                input=text,
            )
            response.stream_to_file(audio_path)

        # FREE MODE → Google TTS
        else:
            print("Using free Google TTS...")
            tts = gTTS(text=text, lang='en')
            tts.save(audio_path)
        print(f"Audio saved to {audio_path}")
        return audio_path

    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

# process each PDF: extract text, save text, convert to audio, and return paths for email attachment
def process_pdf(pdf_path):
    # getting the filename without extension for naming text and audio files
    filename = os.path.basename(pdf_path)
    filename_stem = os.path.splitext(filename)[0] 

    print(f"Extracting text from: {filename_stem}")
    
    # extract the text from the PDF
    text = extract_text(pdf_path)

    # clean extracted text using GPT
    text = clean_text_with_llm(text)
    
    if text == "":
        print(f"  Warning: no text extracted from {filename_stem}")
        return None
    
    # save the text and generate the audio from that text
    text_path = save_text(text, filename_stem)
    audio_path = convert_to_audio(text, filename_stem)

    # return all the relevant info for this file to be used in cleanup later
    return {
        'pdf_path': pdf_path,
        'text_path': text_path,
        'audio_path': audio_path,
    }

def fetch_pdfs():
    # access google drive
    service = get_drive_service()
    # get target date
    date_str = get_target_date()

    # queries google drive for PDFs containing the target date
    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and name contains '{date_str}' and mimeType='application/pdf'"
    ).execute()


    #saves files so we can loop though them
    files = results.get('files', [])

    # early exit if no files found for the target date
    if not files:
        print(f"No PDFs found for date: {date_str}")
        return date_str, []

    # make sure the download directory exists (prevents crash)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # list to hold processed file info for email generation and cleanup later
    processed_files = []


    for file in files:
        print(f"Downloading: {file['name']}")

        # create a request to download the file content
        request = service.files().get_media(fileId=file['id'])
        
        # build local save path
        pdf_path = os.path.join(DOWNLOAD_DIR, file['name'])

        # download the file content to the local path
        with open(pdf_path, 'wb') as file:
            downloader = MediaIoBaseDownload(file, request)

            done = False
            while not done:
                done = downloader.next_chunk()[1]

        print(f"Saved to {pdf_path}")

        # process the downloaded PDF to extract text, save text, and convert to audio
        processed_file = process_pdf(pdf_path)

        # only add to the list if processing was successful
        if processed_file is not None:
            processed_files.append(processed_file)

    return date_str, processed_files


def send_email(subject, body, attachments=None):
    # Ensure email credentials are available
    if not EMAIL_PASSWORD:
        raise ValueError("EMAIL_PASSWORD is not set in the environment.")

    # prepare the email
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    #add attachmentsn
    for attachment_path in attachments or []:
        with open(attachment_path, 'rb') as f:
            msg.add_attachment(
                f.read(),
                maintype='audio',
                subtype='mpeg',
                filename=os.path.basename(attachment_path),
            )

# Send the email using Gmail's SMTP server
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("Email sent successfully!")

    except Exception as e:
        print(f"Error: {e}")


def delete_file(path):
    if path and os.path.exists(path):
        os.remove(path)
        print(f"Deleted temporary file: {path}")


def cleanup_temporary_files(processed_files):
    for item in processed_files:
        delete_file(item.get('pdf_path'))
        delete_file(item.get('text_path'))
        delete_file(item.get('audio_path'))
        
if __name__ == '__main__':
    target_date, processed_files = fetch_pdfs()

    if processed_files is not None and len(processed_files) > 0:
        subject = f"These are your readings for {target_date}"
        body = f"You have {len(processed_files)} readings"
        attachments = [item['audio_path'] for item in processed_files]

        try:
            send_email(subject, body, attachments)
            cleanup_temporary_files(processed_files)
        except Exception as e:
            print(f"Error during email sending or cleanup: {e}")
    else:
        print(f"No readings found for {target_date}. Skipping email.")
