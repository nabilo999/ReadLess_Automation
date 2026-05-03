import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from pypdf import PdfReader
from gtts import gTTS
import io
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', 'credentials.json')
FOLDER_ID = os.getenv('FOLDER_ID', '1e4VSWDCraG60ZWDwzFm-Rq9Twvx6CnRs')
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', 'c:\\Users\\nabil\\Desktop\\automation_final proj\\Downloaded_PDFs')
TEXT_DIR = os.getenv('TEXT_DIR', 'c:\\Users\\nabil\\Desktop\\automation_final proj\\Extracted_Text')
AUDIO_DIR = os.getenv('AUDIO_DIR', 'c:\\Users\\nabil\\Desktop\\automation_final proj\\Generated_Audio')
Email_Password = os.environ.get("EMAIL_PASS")

# connect to Google Drive API using service account credentials
def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)

# calculate the target date (eg: get the files for next week)
def get_target_date():
    target = datetime.today() + timedelta(days=12)
    return target.strftime('%Y-%m-%d')  # match your filename format

def extract_text(pdf_path):
    text = ''
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + '\n'
    return text.strip()

def save_text(text, filename_stem):
    os.makedirs(TEXT_DIR, exist_ok=True)
    text_path = os.path.join(TEXT_DIR, f'{filename_stem}.txt')

    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"Text saved to {text_path}")
    return text_path

def convert_to_audio(text, filename_stem):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    audio_path = os.path.join(AUDIO_DIR, f'{filename_stem}.mp3')

    tts = gTTS(text=text, lang='en')
    tts.save(audio_path)

    print(f"Audio saved to {audio_path}")

def process_pdf(pdf_path):
    filename_stem = os.path.splitext(os.path.basename(pdf_path))[0]
    print(f"Extracting text from: {filename_stem}")
    
    text = extract_text(pdf_path)
    
    if not text:
        print(f"  Warning: no text extracted from {filename_stem}")
        return
    
    save_text(text, filename_stem)
    convert_to_audio(text, filename_stem)

def fetch_pdfs():
    service = get_drive_service()
    date_str = get_target_date()

    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and name contains '{date_str}' and mimeType='application/pdf'",
        fields='files(id, name)'
    ).execute()

    files = results.get('files', [])

    if not files:
        print(f"No PDFs found for date: {date_str}")
        return

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    for file in files:
        print(f"Downloading: {file['name']}")
        request = service.files().get_media(fileId=file['id'])
        pdf_path = os.path.join(DOWNLOAD_DIR, file['name'])

        with io.FileIO(pdf_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

        print(f"Saved to {pdf_path}")
        process_pdf(pdf_path)

if __name__ == '__main__':
    fetch_pdfs()


def send_email(subject, body):
    # credentials
    msg_from = "nabilosaido47@gmail.com"
    password = Email_Password

    # Create the email 
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = "nabilosaido47@gmail.com"

    try:
        # Connect to Gmail's SMTP and send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(msg_from, password)
            smtp.send_message(msg)
            print("Email sent successfully!")

    except Exception as e:
        print(f"Error: {e}")