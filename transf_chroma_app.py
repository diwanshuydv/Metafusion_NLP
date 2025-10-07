import os
from flask import Flask, request, jsonify
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import time # Import the time module

# — Init Flask
app = Flask(__name__)

# — Init ChromaDB with persistent storage
PERSIST_DIRECTORY = "./chroma_db"
client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
collection = client.get_or_create_collection("tr_collection")
# Collection persists automatically

# — Embedding model (auto-download)
model = SentenceTransformer("all-MiniLM-L6-v2")

@app.route("/insert", methods=["POST"])
def insert():
    """
    Expect JSON: { "docs": ["doc1 text", "doc2 text", ...] }
    Inserts each document and creates an embedding automatically.
    """
    data = request.get_json()
    docs = data.get("docs", [])
    ids = [f"doc{i}" for i in range(len(docs))]
    
    collection.add(documents=docs, ids=ids)
    return jsonify({"inserted": len(docs)}), 201

@app.route("/query", methods=["POST"])
def query():
    """
    Expect JSON: { "query": "search text", "top_k": 10 }
    Returns top_k similar docs with their scores,
    and includes retrieval, embedding generation, and total times.
    """
    data = request.get_json()
    query_text = data.get("query", "")
    top_k = data.get("top_k", 10)

    if not query_text:
        return jsonify({"error": "query is required"}), 400

    start_total_time = time.time() # Start total time measurement

    # Measure embedding generation time
    start_embedding_time = time.time()
    query_embedding = model.encode(query_text).tolist()
    end_embedding_time = time.time()
    embedding_generation_time = end_embedding_time - start_embedding_time

    # Measure retrieval time
    start_retrieval_time = time.time()
    results = collection.query(
        query_embeddings=[query_embedding], # Use the pre-generated embedding
        n_results=top_k
    )
    end_retrieval_time = time.time()
    retrieval_time = end_retrieval_time - start_retrieval_time

    end_total_time = time.time() # End total time measurement
    total_time = end_total_time - start_total_time

    docs = results["documents"][0]
    metadatas = results.get("metadatas", [[]])[0]
    scores = results.get("distances", [[]])[0]

    response_data = [
        {"doc": d, "meta": m, "score": s} for d, m, s in zip(docs, metadatas, scores)
    ]

    # Add timing information to the response
    response_payload = {
        "results": response_data,
        "timings": {
            "embedding_generation_time_ms": round(embedding_generation_time * 1000, 3),
            "retrieval_time_ms": round(retrieval_time * 1000, 3),
            "total_time_ms": round(total_time * 1000, 3)
        }
    }
    return jsonify(response_payload)

if __name__ == "__main__":
    os.makedirs("./chroma_db", exist_ok=True)
    app.run(host="0.0.0.0", port=6080)
