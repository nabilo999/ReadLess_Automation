### How to run:
- Run the following commads
    ```bash
        pip install google-api-python-client google-auth
        pip install pypdf
        pip install openai
        pip install python-dotenv
    ```
- Create an `.env` file in the root directory of the project.

- Add the following environment variables to the `.env` file:
    '''
    # Google Drive API credentials file
    SERVICE_ACCOUNT_FILE=credentials.json

    # Google Drive folder to scan for PDFs
    FOLDER_ID=your_folder_id

    # Local folders for processing files
    DOWNLOAD_DIR=path_to_download_folder
    TEXT_DIR=path_to_text_output_folder
    AUDIO_DIR=path_to_audio_output_folder

    # How far back to look for files (in days)
    DAYS_BACK= 0

    # Email settings (set your own sender/receiver)
    EMAIL_PASSWORD=your_email_password
    EMAIL_FROM=your_email
    EMAIL_TO=your_email

    # Optional settings ('true' or 'false')
    CLEAN_TEXT=true
    PREMIUM_TTS=true

    # OpenAI API key (only needed if using AI features)
    OPENAI_API_KEY=your_openai_key
'''