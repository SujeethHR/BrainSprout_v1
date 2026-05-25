import os
import time
import shutil
import tempfile
import logging
from flask import Flask, request, render_template, jsonify, g
from werkzeug.utils import secure_filename
from pythonjsonlogger import jsonlogger
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from models.vector_store import VectorStore
from services.storage_service import S3Storage
from services.llm_service import LLMService
from config import Config


def _setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
    ))
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if os.getenv("FLASK_DEBUG", "false").lower() == "true" else logging.INFO)


_setup_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)

vector_store = VectorStore(Config.VECTOR_DB_PATH)
storage_service = S3Storage()
llm_service = LLMService(vector_store)


@app.before_request
def _before():
    g.start_time = time.time()


@app.after_request
def _after(response):
    logger.info("request", extra={
        "method": request.method,
        "path": request.path,
        "status": response.status_code,
        "duration_ms": round((time.time() - g.start_time) * 1000, 2),
    })
    return response


@app.route('/')
def index():
    return render_template('index.html')


def process_document(file):
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, secure_filename(file.filename))

    try:
        file.save(temp_path)

        if file.filename.endswith('.pdf'):
            loader = PyPDFLoader(temp_path)
            documents = loader.load()
        elif file.filename.endswith('.txt'):
            loader = TextLoader(temp_path)
            documents = loader.load()
        else:
            raise ValueError("Unsupported file type")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        return text_splitter.split_documents(documents)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.route('/upload', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith(('.txt', '.pdf')):
            return jsonify({'error': 'Only .txt and .pdf files are supported'}), 400

        logger.info("upload_started", extra={"filename": file.filename})

        try:
            text_chunks = process_document(file)
        except Exception as e:
            logger.error("upload_process_failed", extra={"filename": file.filename, "error": str(e)})
            return jsonify({'error': f'Error processing document: {str(e)}'}), 500

        try:
            file.seek(0)
            storage_service.upload_file(file, secure_filename(file.filename))
        except Exception as e:
            logger.error("upload_s3_failed", extra={"filename": file.filename, "error": str(e)})
            return jsonify({'error': f'Error uploading to S3: {str(e)}'}), 500

        try:
            vector_store.add_documents(text_chunks)
        except Exception as e:
            logger.error("upload_vectordb_failed", extra={"filename": file.filename, "error": str(e)})
            return jsonify({'error': f'Error adding to vector store: {str(e)}'}), 500

        logger.info("upload_completed", extra={"filename": file.filename, "chunks": len(text_chunks)})
        return jsonify({'message': 'File uploaded and processed successfully', 'chunks_processed': len(text_chunks)})

    except Exception as e:
        logger.error("upload_unexpected_error", extra={"error": str(e)})
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400

    logger.info("query_started", extra={"question_length": len(data['question'])})
    t0 = time.time()

    try:
        response = llm_service.get_response(data['question'])
        logger.info("query_completed", extra={"llm_duration_ms": round((time.time() - t0) * 1000, 2)})
        return jsonify({'response': response})
    except Exception as e:
        logger.error("query_failed", extra={"error": str(e)})
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host='0.0.0.0', port=8080, debug=debug)
