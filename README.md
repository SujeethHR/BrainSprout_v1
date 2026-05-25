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

## Deployment

### Docker (local)

Make sure [Docker Desktop](https://www.docker.com/products/docker-desktop/) is installed, then run:

```bash
docker compose up --build
```

The app will be available at `http://localhost:8080`.

To run in the background:

```bash
docker compose up --build -d
```

To stop:

```bash
docker compose down
```

The ChromaDB vector store is persisted in a Docker named volume (`vector_db_data`), so your uploaded documents survive container restarts.

---

### Deploy on AWS EC2

**1. Launch an EC2 instance**
- Go to AWS Console → EC2 → Launch Instance
- Choose **Ubuntu 24.04 LTS** (recommended: `t3.small` or larger — the embedding model uses ~500MB RAM)
- Set storage to **20 GB** or more
- Open inbound ports **22** (SSH) and **8080** (app) in the Security Group

**2. SSH into the instance**

```bash
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>
```

**3. Install Docker**

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
newgrp docker
```

**4. Clone the repo and create `.env`**

```bash
git clone https://github.com/SujeethHR/BrainSprout_v1.git
cd BrainSprout_v1
nano .env
```

Paste your credentials into the file (same format as the local `.env` described in the Setup section), then save.

**5. Build and run with CloudWatch logging**

```bash
docker compose -f docker-compose.yml -f docker-compose.ec2.yml up --build -d
```

This merges `docker-compose.ec2.yml`, which routes all container logs to CloudWatch under the log group `/brainsprout/app`.

**6. Access the app**

```
http://<EC2-PUBLIC-IP>:8080
```

> **Note:** ChromaDB data persists as a Docker volume on the EC2 disk. It survives `docker compose down` and restarts but is lost if you **terminate** (not stop) the instance.

---

## CI/CD

Every push and pull request to `main` triggers a GitHub Actions workflow (`.github/workflows/ci.yml`) that:

1. Builds the Docker image from scratch
2. Starts the container with dummy credentials
3. Waits for the Flask app to be ready on port 8080
4. Runs a smoke test against the `/query` endpoint to confirm the app responds correctly
5. Prints container logs (always, for debugging) and stops the container

The embedding model (`sentence-transformers/all-MiniLM-L6-v2`) is baked into the Docker image at build time, so the container starts instantly without downloading anything at runtime.

---

## Observability

The app emits structured JSON logs to stdout on every request and key event. Each log line is a valid JSON object:

```json
{"asctime": "2025-05-25 10:00:00", "name": "app.main", "levelname": "INFO", "message": "request", "method": "POST", "path": "/query", "status": 200, "duration_ms": 842.5}
{"asctime": "2025-05-25 10:00:00", "name": "app.main", "levelname": "INFO", "message": "upload_completed", "filename": "notes.pdf", "chunks": 38}
```

**Key log events:**

| Event | Fields |
|---|---|
| `request` | `method`, `path`, `status`, `duration_ms` |
| `upload_started` | `filename` |
| `upload_completed` | `filename`, `chunks` |
| `upload_s3_failed` | `filename`, `error` |
| `query_started` | `question_length` |
| `query_completed` | `llm_duration_ms` |
| `query_failed` | `error` |

**CloudWatch (on EC2)**

When running with `docker-compose.ec2.yml`, Docker ships all stdout logs to CloudWatch Logs automatically via the `awslogs` driver. No SDK or extra library is needed in the app. Logs appear in:

- Log group: `/brainsprout/app`
- Log stream: container ID (one stream per container instance)

To view logs from the AWS Console: CloudWatch → Log groups → `/brainsprout/app`.

To tail logs from the CLI:

```bash
aws logs tail /brainsprout/app --follow --region ap-south-1
```

To set up a CloudWatch alarm (e.g. alert on errors):

1. Go to CloudWatch → Log groups → `/brainsprout/app`
2. Create a **Metric Filter** with the pattern `{ $.levelname = "ERROR" }`
3. Create an **Alarm** on that metric with an SNS notification to your email

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
- Move ChromaDB from local storage to a hosted vector database (such as Pinecone or Weaviate) so the vector index persists across instance termination
- Add environment-based configuration for staging and production
- Add automated deployment step to the CI/CD pipeline (build → push to ECR → deploy to EC2)

**Model flexibility**
- Allow users to choose between different LLMs (OpenAI, Anthropic, local Ollama models)
- Add a settings page to adjust temperature and retrieval parameters without touching the code

**Monitoring and observability**
- Add CloudWatch dashboards for request latency, error rate, and upload throughput
- Integrate LangSmith to trace and debug LangChain chains
- Track token usage and API costs over time

---

## License

MIT
