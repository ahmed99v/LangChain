"""
Script to load Hugging Face embedding model and create a vector database.
This script processes documents, generates embeddings, and stores them in a FAISS vector database.
"""

import os
import pickle
from pathlib import Path
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from pypdf import PdfReader


class VectorDatabase:
    """Vector database using FAISS for efficient similarity search."""
    
    def __init__(self, embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the vector database with a Hugging Face embedding model.
        
        Args:
            embedding_model_name: Name of the Hugging Face model to use for embeddings.
                                  Default is a lightweight, fast model suitable for general use.
        """
        print(f"Loading embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.embedding_model_name = embedding_model_name  # Store model name for saving
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        print(f"Model loaded. Embedding dimension: {self.embedding_dim}")
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.documents = []  # Store original documents for retrieval
        self.metadata = []   # Store metadata (e.g., document IDs, sources)
        
    def add_documents(self, texts: List[str], metadata: Optional[List[dict]] = None):
        """
        Add documents to the vector database.
        
        Args:
            texts: List of text documents to embed and store.
            metadata: Optional list of metadata dictionaries for each document.
        """
        if not texts:
            print("No documents provided.")
            return
        
        print(f"Generating embeddings for {len(texts)} documents...")
        # Generate embeddings
        embeddings = self.embedding_model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Normalize embeddings for better cosine similarity search
        faiss.normalize_L2(embeddings)
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Store documents and metadata
        self.documents.extend(texts)
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(texts))
        
        print(f"Added {len(texts)} documents to the vector database.")
        print(f"Total documents in database: {self.index.ntotal}")
    
    def search(self, query: str, k: int = 5) -> List[dict]:
        """
        Search for similar documents in the vector database.
        
        Args:
            query: Search query text.
            k: Number of similar documents to retrieve.
            
        Returns:
            List of dictionaries containing document text, metadata, and similarity score.
        """
        if self.index.ntotal == 0:
            print("Vector database is empty. Please add documents first.")
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)
        
        # Search in FAISS index
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Prepare results
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.documents):
                # Convert L2 distance to similarity score (1 - normalized distance)
                similarity = 1 - (distance / 2.0)  # Normalize to 0-1 range
                results.append({
                    'document': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'similarity': float(similarity),
                    'rank': i + 1
                })
        
        return results
    
    def save(self, save_path: str):
        """
        Save the vector database to disk.
        
        Args:
            save_path: Path to save the database (without extension).
        """
        # Save FAISS index
        faiss.write_index(self.index, f"{save_path}.index")
        
        # Save documents and metadata
        with open(f"{save_path}.pkl", "wb") as f:
            pickle.dump({
                'documents': self.documents,
                'metadata': self.metadata,
                'embedding_model_name': self.embedding_model_name
            }, f)
        
        print(f"Vector database saved to {save_path}.index and {save_path}.pkl")
    
    def load(self, load_path: str):
        """
        Load the vector database from disk.
        
        Args:
            load_path: Path to load the database from (without extension).
        """
        # Load FAISS index
        self.index = faiss.read_index(f"{load_path}.index")
        
        # Load documents and metadata
        with open(f"{load_path}.pkl", "rb") as f:
            data = pickle.load(f)
            self.documents = data['documents']
            self.metadata = data['metadata']
            model_name = data.get('embedding_model_name', 'sentence-transformers/all-MiniLM-L6-v2')
        
        # Reload embedding model (needed for search)
        print(f"Loading embedding model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        self.embedding_model_name = model_name  # Store model name
        
        print(f"Vector database loaded. Total documents: {self.index.ntotal}")


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file.
        
    Returns:
        Extracted text from the PDF.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        total_pages = len(reader.pages)
        print(f"Processing PDF: {pdf_path} ({total_pages} pages)")
        
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text.strip():
                text += page_text + "\n"
            if page_num % 10 == 0:
                print(f"  Processed {page_num}/{total_pages} pages...")
        
        print(f"  Completed: Extracted {len(text)} characters from {total_pages} pages")
        return text
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return ""


def load_documents_from_directory(directory_path: str, include_pdfs: bool = True) -> List[str]:
    """
    Load text documents from a directory.
    
    Args:
        directory_path: Path to directory containing text files.
        include_pdfs: Whether to process PDF files in the directory.
        
    Returns:
        List of document texts.
    """
    documents = []
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f"Directory {directory_path} does not exist.")
        return documents
    
    # Supported text file extensions
    text_extensions = {'.txt', '.md', '.py', '.js', '.ts', '.json', '.csv'}
    pdf_extensions = {'.pdf'}
    
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            file_ext = file_path.suffix.lower()
            
            # Process PDF files
            if include_pdfs and file_ext in pdf_extensions:
                pdf_text = extract_text_from_pdf(str(file_path))
                if pdf_text.strip():
                    documents.append(pdf_text)
                    print(f"Loaded PDF: {file_path}")
            
            # Process text files
            elif file_ext in text_extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.strip():
                            documents.append(content)
                            print(f"Loaded: {file_path}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return documents


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into chunks for better processing.
    
    Args:
        text: Text to chunk.
        chunk_size: Size of each chunk in characters.
        chunk_overlap: Number of characters to overlap between chunks.
        
    Returns:
        List of text chunks.
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - chunk_overlap
    
    return chunks


def main():
    """Main function to demonstrate vector database creation."""
    
    # Initialize vector database with Hugging Face embedding model
    # You can change the model to any sentence-transformers model from Hugging Face
    # Popular options:
    # - "sentence-transformers/all-MiniLM-L6-v2" (fast, lightweight)
    # - "sentence-transformers/all-mpnet-base-v2" (better quality, slower)
    # - "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2" (multilingual)
    
    print("=" * 60)
    print("Creating Vector Database with Hugging Face Embeddings")
    print("=" * 60)
    
    vector_db = VectorDatabase(
        embedding_model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Example 1: Add documents directly
    print("\n--- Example 1: Adding sample documents ---")
    sample_documents = [
        "Newton's second law states that force equals mass times acceleration: F = ma",
        "Einstein's theory of relativity revolutionized our understanding of space and time",
        "Quantum mechanics describes the behavior of particles at the atomic and subatomic level",
        "The Pythagorean theorem states that in a right triangle, a² + b² = c²",
        "Calculus is the mathematical study of continuous change"
    ]
    
    metadata = [
        {"source": "physics", "topic": "mechanics"},
        {"source": "physics", "topic": "relativity"},
        {"source": "physics", "topic": "quantum"},
        {"source": "mathematics", "topic": "geometry"},
        {"source": "mathematics", "topic": "analysis"}
    ]
    
    vector_db.add_documents(sample_documents, metadata)
    
    # Example 2: Search in the database
    print("\n--- Example 2: Searching the database ---")
    queries = [
        "What is force?",
        "Tell me about quantum physics",
        "Mathematical formulas"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        results = vector_db.search(query, k=3)
        for result in results:
            print(f"  Rank {result['rank']}: Similarity={result['similarity']:.3f}")
            print(f"    Document: {result['document'][:80]}...")
            print(f"    Metadata: {result['metadata']}")
    
    # Example 3: Save the database
    print("\n--- Example 3: Saving the database ---")
    save_path = "knowledge-base/vector-stores/vector_db"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    vector_db.save(save_path)
    
    # Example 4: Load documents from directory (if docs exist)
    print("\n--- Example 4: Loading documents from directory ---")
    docs_dir = "knowledge-base/docs"
    if os.path.exists(docs_dir):
        documents = load_documents_from_directory(docs_dir)
        if documents:
            # Chunk large documents
            all_chunks = []
            for doc in documents:
                chunks = chunk_text(doc)
                all_chunks.extend(chunks)
            
            if all_chunks:
                print(f"Processing {len(all_chunks)} chunks from directory...")
                vector_db.add_documents(all_chunks)
                vector_db.save(save_path)
    
    print("\n" + "=" * 60)
    print("Vector database creation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
