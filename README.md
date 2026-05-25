# BrainSprout

BrainSprout is a knowledge intelligence system that lets you upload your own documents and ask questions about them in plain language. It reads your files, understands the content, and answers questions using a large language model — without sending your documents to a generic AI service untouched.

It is built with a technique called RAG (Retrieval-Augmented Generation), which means the AI only looks at the parts of your documents that are relevant to your question before generating an answer.

---

## What it does

1. You upload a PDF or TXT file through the web interface.
2. The app breaks the document into small overlapping chunks of text.
3. Each chunk is converted into a numerical representation (called an embedding) and stored in a local vector database.
4. The original file is also saved to an AWS S3 bucket for persistent storage.
5. When you ask a question, the app finds the most relevant chunks from the database and sends them, along with your question, to a large language model (Llama 3.3 70B running on Groq).
6. The model returns an answer based only on your documents, and the conversation history is preserved so follow-up questions work naturally.

---

## Tech stack

| Layer | Tool |
|---|---|
| Web framework | Flask |
| Document loading | LangChain (PyPDFLoader, TextLoader) |
| Text chunking | LangChain RecursiveCharacterTextSplitter |
| Embeddings | HuggingFace sentence-transformers/all-MiniLM-L6-v2 |
| Vector database | ChromaDB (local) |
| LLM | Llama 3.3 70B via Groq API |
| File storage | AWS S3 |
| Config | python-dotenv |

---

## Project structure

```
BrainSprout/
├── app/
│   ├── main.py                 # Flask app and all routes
│   ├── config.py               # Loads environment variables
│   ├── models/
│   │   └── vector_store.py     # ChromaDB setup and search
│   ├── services/
│   │   ├── llm_service.py      # Groq LLM chain with chat history
│   │   └── storage_service.py  # AWS S3 upload and download
│   ├── templates/
│   │   └── index.html          # Web UI
│   ├── static/
│   │   └── style.css           # Styles
│   └── vector_db/              # Local ChromaDB storage (auto-created)
├── pyproject.toml
├── requirements.txt
└── .env                        # You create this (see setup)
```

---

## Prerequisites

- Python 3.13 or higher
- A [Groq](https://console.groq.com) account and API key (free tier available)
- An AWS account with an S3 bucket and IAM credentials

If you are new to these, here is what each one is:
- **Groq** is a service that lets you run large AI models very quickly via an API call. You sign up, create an API key, and use it in the app.
- **AWS S3** is a cloud file storage service. You create a bucket (a named container for files), create an IAM user with permission to access it, and get an access key and secret key.

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd BrainSprout
```

### 2. Install dependencies

If you are using `uv` (recommended):

```bash
uv sync
```

Or with pip:

```bash
pip install -r requirements.txt
```

### 3. Create a `.env` file

Create a file named `.env` in the root of the project (next to `pyproject.toml`) with the following contents:

```env
GROQ_API_KEY=your_groq_api_key_here

AWS_ACCESS_KEY=your_aws_access_key_here
AWS_SECRET_KEY=your_aws_secret_key_here
AWS_BUCKET_NAME=your_s3_bucket_name_here
AWS_REGION=your_region
```

Replace each value with your actual credentials. Do not commit this file to version control.

### 4. Run the app

```bash
cd app
python main.py
```

The app will start on `http://localhost:8080`. Open that URL in your browser.

---

## How to use

1. Open `http://localhost:8080` in your browser.
2. Click the file input under "Upload Documents" and select a `.pdf` or `.txt` file.
3. Click "Upload". You will get a confirmation showing how many text chunks were processed.
4. Type a question in the text area under "Ask Questions" and click "Ask".
5. The answer will appear in the "Response" section below.

You can upload multiple documents over time. All of them will be searchable when you ask questions.

---

## API endpoints

If you want to use the backend without the web UI:

**Upload a document**

```
POST /upload
Content-Type: multipart/form-data

file: <your .pdf or .txt file>
```

**Ask a question**

```
POST /query
Content-Type: application/json

{ "question": "What is the main topic of the document?" }
```

---

## Future scope

The current version is a working foundation. Here are meaningful directions to take it next:

**Better document support**
- Add support for Word documents (.docx), Markdown files, and web URLs
- Allow users to paste raw text directly instead of uploading a file
- Support uploading multiple files in a single request

**User and session management**
- Add user accounts so each person has their own document collection
- Persist chat history to a database so conversations survive server restarts
- Allow users to delete or manage their uploaded documents

**Smarter retrieval**
- Experiment with different embedding models for better search accuracy
- Add a re-ranking step to improve which chunks are sent to the LLM
- Implement hybrid search (combining keyword search with vector search)

**Source transparency**
- Return the specific document chunks that were used to generate each answer
- Show the user which file and page number the answer came from
- Add a confidence score so users know how well the retrieved context matched the question

**Deployment**
- Containerize the app with Docker for consistent deployment
- Move ChromaDB from local storage to a hosted vector database (such as Pinecone or Weaviate) so the vector index persists across restarts
- Add environment-based configuration for staging and production
- Set up a CI/CD pipeline

**Model flexibility**
- Allow users to choose between different LLMs (OpenAI, Anthropic, local Ollama models)
- Add a settings page to adjust temperature and retrieval parameters without touching the code

**Monitoring and observability**
- Add structured logging to track queries, upload times, and errors
- Integrate LangSmith or a similar tool to trace and debug LangChain chains
- Track token usage and API costs over time

---

## License

MIT
