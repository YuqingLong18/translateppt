# Document Translation Prototype

Prototype web application that translates PowerPoint presentations, Word documents, and Excel workbooks using an OpenRouter-backed LLM. The app extracts document text, sends it for translation, replaces the original content while preserving layout, and provides the translated file for download.

## Features
- Upload `.pptx`, `.docx`, or `.xlsx` files up to 50MB
- Queue multiple documents per run; translations execute sequentially with per-file download links
- Configure source/target languages (auto-detect supported) and optional font override
- Supply an OpenRouter API key directly in the UI or via environment variable
- Progress feedback during upload/translation and downloadable translated output
- Mock translation mode when no API key is provided (prepends `[target]` to text)

## Project Structure
```
ppt-translator/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── document_handler.py
│   ├── translator.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── styles.css
├── output/
│   └── .gitkeep
├── uploads/
│   └── .gitkeep
├── .env.example
├── .gitignore
└── README.md
```

## Prerequisites
- Python 3.10+
- Node.js **not required** (vanilla frontend)
- OpenRouter account & API key for real translations (optional for mock mode)

## Setup
1. Create and activate a virtual environment:
   ```bash
   python3 -m venv translateppt
   source translateppt/bin/activate
   ```
2. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Configure environment variables:
   - Set `CREDENTIAL_DB_URL` to point to your credential database API (default: `http://localhost:3000`)
   - (Optional) Export `OPENROUTER_API_KEY` so you do not need to paste it for each run:
     ```bash
     export OPENROUTER_API_KEY="sk-..."
     export CREDENTIAL_DB_URL="http://localhost:3000"
     ```

## Authentication
The app uses a centralized credential database for authentication. Users must log in with their username and password before accessing the translation interface. The credential database should be running separately (see `/index` project for setup).

- Login page: `/login`
- Main app: `/` (requires authentication)
- Logout: Click "Logout" link in header

## Running the App
1. Start the Flask backend from the project root:
   ```bash
   export FLASK_APP=backend.app:create_app
   flask run --reload
   ```
2. Open the interface at [http://localhost:5000](http://localhost:5000). Static assets are served by Flask.

## Translation Flow
1. Upload or drag one or more supported files to build your translation queue
2. Choose language settings and optional font override
3. Provide an OpenRouter API key (or rely on the `.env` value)
4. Click **Translate** to process the queue; each download link appears as soon as it is ready
5. Review any failures listed beneath the download list, then download the translated documents

If no API key is supplied, the backend returns mock translations (`[lang] original text`) to illustrate the flow.

## Windows Executable Build
To create a double-clickable `.exe` that bundles the backend and frontend, run the following on a Windows machine with Python 3.10+ installed:

1. Create a virtual environment and install dependencies plus PyInstaller:
   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\activate
   pip install -r backend/requirements.txt pyinstaller
   ```
2. Build the executable using the provided spec:
   ```powershell
   pyinstaller translateppt.spec --clean --noconfirm
   ```
3. After the build completes, launch `dist/TranslatePPT/TranslatePPT.exe`. The launcher starts Flask, opens `http://127.0.0.1:5000` in your default browser, and writes uploads/output alongside the `.exe`.

Place an `.env` file (or set the `OPENROUTER_API_KEY` environment variable) in the same directory as the `.exe` if you want the translator to run with real OpenRouter credentials. You can distribute the entire `dist/TranslatePPT` folder as a portable app and double-click `TranslatePPT.exe` to start translating locally.

## API Overview
| Method | Endpoint         | Description                           |
| :----- | :--------------- | :------------------------------------ |
| GET    | `/health`        | Service health check                  |
| POST   | `/upload`        | Upload source document                |
| POST   | `/translate`     | Trigger translation for uploaded file |
| GET    | `/download/<id>` | Download translated document          |
| GET    | `/languages`     | List supported languages              |

## Next Steps
- Persist uploads/output in durable storage
- Handle PowerPoint SmartArt, speaker notes, and additional formatting nuances
- Add server-side job queue for long-running translations
- Add automated tests and CI pipeline
