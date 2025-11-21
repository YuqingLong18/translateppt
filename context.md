PowerPoint Translation Web Application - Context Document
Project Overview
Build a web-based application that translates PowerPoint presentations from one language to another using LLM-powered translation via OpenRouter API. The application should extract text content, translate it, replace the original text while preserving formatting, and provide the translated file for download.
Core Requirements
Functional Requirements

File Upload

Accept .pptx files (PowerPoint 2007+)
Display file name and basic info after upload
Validate file type and size (recommend max 50MB)


Text Extraction

Extract all text content from slides
Preserve text location and context
Handle text in:

Title placeholders
Body text placeholders
Text boxes
Tables
Smart Art (if possible)
Notes/speaker notes (optional feature)




Translation Configuration

Source language selection (auto-detect option preferred)
Target language selection
Font selection for translated text
API key input for OpenRouter
Model selection (default: recommend a balanced model like anthropic/claude-3.5-sonnet)


Translation Process

Send extracted text to OpenRouter API
Use specified LLM model for translation
Show progress indicator during translation
Handle API errors gracefully
Preserve formatting markers (bold, italic, etc.) if present


Text Replacement

Replace original text with translated text
Apply user-specified font to all translated text
Maintain slide structure and layout
Preserve non-text elements (images, charts, shapes)
Keep original formatting (bullet points, numbering, alignment)


Download

Generate translated .pptx file
Provide download button
Use meaningful filename (e.g., original_name_translated_[lang].pptx)



Technical Requirements
Technology Stack
Backend:

Python with Flask or FastAPI
python-pptx library for PowerPoint manipulation
requests library for API calls
Optional: langdetect for language detection

Frontend:

HTML5/CSS3
Vanilla JavaScript or lightweight framework (React/Vue optional)
File upload handling
Progress indicators/loading states
Responsive design

API Integration:

OpenRouter API (https://openrouter.ai/docs)
Support for multiple LLM models
Proper error handling and rate limiting

Project Structure
ppt-translator/
├── backend/
│   ├── app.py                 # Main application file
│   ├── translator.py          # Translation logic
│   ├── ppt_handler.py         # PowerPoint extraction/modification
│   ├── config.py              # Configuration settings
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── index.html             # Main HTML file
│   ├── styles.css             # Styling
│   └── script.js              # Frontend logic
├── uploads/                   # Temporary upload directory
├── output/                    # Temporary output directory
├── .env.example               # Environment variables template
├── .gitignore
└── README.md
Detailed Feature Specifications
1. User Interface Flow
Step 1: Upload

Drag-and-drop zone or file picker
Display selected file details

Step 2: Configure

Source language dropdown (with auto-detect option)
Target language dropdown
Font selection dropdown (common fonts + upload custom font option)
OpenRouter API key input (with visibility toggle)
Model selection dropdown (populated from OpenRouter)

Step 3: Translate

"Translate" button
Progress bar or spinner
Status messages (extracting, translating, processing)

Step 4: Download

Success message
Download button
Option to translate another file

2. PowerPoint Text Extraction Logic
Extract text from:
python# Pseudo-code structure
for slide in presentation.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            # Extract text from text_frame
        if shape.has_table:
            # Extract text from table cells
        # Handle grouped shapes recursively
Maintain metadata:

Slide index
Shape index
Original text
Shape type
Position information

3. OpenRouter API Integration
Endpoint: https://openrouter.ai/api/v1/chat/completions
Request Format:
json{
  "model": "anthropic/claude-3.5-sonnet",
  "messages": [
    {
      "role": "system",
      "content": "You are a professional translator. Translate the following text from {source_lang} to {target_lang}. Preserve any formatting markers like **bold** or *italic*. Only return the translated text without explanations."
    },
    {
      "role": "user",
      "content": "Text to translate"
    }
  ]
}
Headers:
Authorization: Bearer YOUR_API_KEY
HTTP-Referer: YOUR_SITE_URL
X-Title: PPT Translator
4. Translation Strategy
Option A: Batch Translation (Recommended)

Combine all text snippets with delimiters
Single API call for efficiency
Parse response to extract individual translations
Better for maintaining consistency

Option B: Individual Translation

Translate each text box separately
Multiple API calls
Easier error handling per snippet
Better for very large presentations

5. Font Application
Support common fonts:

Arial
Calibri
Times New Roman
Helvetica
Comic Sans MS
Courier New

Allow custom font specification:

Font name as string
Apply to all translated text
Fallback to Arial if font not available

6. Error Handling
Handle these scenarios:

Invalid file format
Corrupted PowerPoint file
API key issues (invalid, expired, no credits)
Network errors
Translation failures
Unsupported languages
File too large

Provide user-friendly error messages for each case.
Implementation Guidelines
Security Considerations

API Key Protection

Never log or store API keys
Use environment variables for server-side keys (if implementing)
Client-side keys should be user-provided


File Handling

Validate file types strictly
Implement file size limits
Clean up temporary files after processing
Use unique filenames to prevent collisions


Input Validation

Sanitize all user inputs
Validate language codes
Check font names against allowed list



Performance Optimization

File Processing

Stream large files instead of loading entirely in memory
Implement timeout limits
Consider chunking for very large presentations


API Calls

Implement retry logic with exponential backoff
Cache translations if user re-translates same file
Show estimated time based on file size



User Experience

Progress Feedback

Show current step clearly
Display percentage for longer operations
Provide cancel option


Responsive Design

Mobile-friendly interface
Works on tablets and desktops
Clear typography and spacing


Helpful Defaults

Pre-select common languages
Suggest appropriate fonts for target language
Remember user preferences (localStorage)



Dependencies
Python Backend
flask==3.0.0
python-pptx==0.6.23
requests==2.31.0
langdetect==1.0.9
python-dotenv==1.0.0
Frontend (if using build tools)
No heavy frameworks required
Consider: axios for API calls if needed
Environment Variables
env# .env.example
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
MAX_UPLOAD_SIZE=52428800  # 50MB in bytes
ALLOWED_EXTENSIONS=pptx
API Endpoints (Backend)
POST /upload

Accept file upload
Return file ID and metadata

POST /translate

Accept: file ID, source lang, target lang, font, API key, model
Process translation
Return: job ID or translated file directly

GET /download/{file_id}

Return translated .pptx file
Set appropriate headers for download

GET /models

Return list of available models from OpenRouter

GET /languages

Return supported language pairs

Testing Checklist

 Upload valid .pptx file
 Upload invalid file (should reject)
 Translate small presentation (< 10 slides)
 Translate large presentation (> 50 slides)
 Test with different fonts
 Test with various language pairs
 Test error handling (invalid API key, network error)
 Test special characters in text
 Test text with formatting (bold, italic, colors)
 Verify layout preservation
 Test on different browsers
 Test on mobile devices

Future Enhancements (Optional)

Support for multiple file formats (.ppt, .odp)
Batch translation of multiple files
Translation history/dashboard
Custom translation glossaries
Preview before download
Image text extraction (OCR) and translation
User accounts and saved API keys
Cloud storage integration (Google Drive, Dropbox)
Real-time collaboration features

Getting Started Checklist for Developer

Set up Python virtual environment
Install backend dependencies
Create basic Flask application structure
Implement file upload endpoint
Implement PowerPoint text extraction
Test extraction with sample files
Implement OpenRouter API integration
Test translation with sample text
Implement text replacement in PowerPoint
Create frontend interface
Connect frontend to backend
Test end-to-end flow
Add error handling
Add progress indicators
Test with various files and languages
Write README with setup instructions
Deploy (optional)

Notes

Keep the interface simple and intuitive
Focus on core functionality first, then add enhancements
Ensure proper cleanup of temporary files
Consider adding a demo mode with sample presentations
Document the code well for future maintenance
Make the API key input prominent but with security warning
Consider adding example presentations for testing

Resources

python-pptx documentation: https://python-pptx.readthedocs.io/
OpenRouter API docs: https://openrouter.ai/docs
Flask documentation: https://flask.palletsprojects.com/
Language codes: ISO 639-1 standard