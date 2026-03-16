"""
Simple example: Load Hugging Face embedding model and create a basic vector database.
This is a minimal example to get started quickly.
"""

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Step 1: Load Hugging Face embedding model
print("Loading embedding model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
embedding_dim = model.get_sentence_embedding_dimension()
print(f"Model loaded! Embedding dimension: {embedding_dim}")

# Step 2: Prepare some sample documents
documents = [
    "Python is a popular programming language",
    "Machine learning is a subset of artificial intelligence",
    "Vector databases store embeddings for similarity search",
    "LangChain is a framework for building LLM applications"
]

# Step 3: Generate embeddings
print("\nGenerating embeddings...")
embeddings = model.encode(documents, convert_to_numpy=True)
print(f"Generated {len(embeddings)} embeddings")

# Step 4: Create FAISS vector database
print("\nCreating vector database...")
# Normalize embeddings for cosine similarity
faiss.normalize_L2(embeddings)
# Create FAISS index
index = faiss.IndexFlatL2(embedding_dim)
index.add(embeddings.astype('float32'))
print(f"Vector database created with {index.ntotal} documents")

# Step 5: Search in the database
print("\nSearching the database...")
query = "What is Python?"
query_embedding = model.encode([query], convert_to_numpy=True)
faiss.normalize_L2(query_embedding)

# Search for top 3 similar documents
k = 3
distances, indices = index.search(query_embedding.astype('float32'), k)

print(f"\nQuery: '{query}'")
print("Top results:")
for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
    similarity = 1 - (distance / 2.0)  # Convert distance to similarity
    print(f"{i+1}. Similarity: {similarity:.3f}")
    print(f"   Document: {documents[idx]}\n")

print("Done!")