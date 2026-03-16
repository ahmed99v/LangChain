"""
Script to create a vector database from PDF files.
This script processes PDF files, extracts text, generates embeddings, and stores them in a FAISS vector database.
"""

import os
from pathlib import Path
from create_vector_db import VectorDatabase, extract_text_from_pdf, chunk_text


def process_pdf_to_vector_db(
    pdf_path: str,
    vector_db_path: str = "knowledge-base/vector-stores/vector_db",
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    create_new: bool = False
):
    """
    Process a PDF file and create/update a vector database.
    
    Args:
        pdf_path: Path to the PDF file to process.
        vector_db_path: Path where to save the vector database (without extension).
        embedding_model_name: Hugging Face model name for embeddings.
        chunk_size: Size of text chunks in characters.
        chunk_overlap: Number of characters to overlap between chunks.
        create_new: If True, create a new database. If False, load existing and add to it.
    """
    print("=" * 60)
    print("PDF to Vector Database Processing")
    print("=" * 60)
    
    # Check if PDF exists
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    # Initialize or load vector database
    if create_new or not os.path.exists(f"{vector_db_path}.index"):
        print("\nCreating new vector database...")
        vector_db = VectorDatabase(embedding_model_name=embedding_model_name)
    else:
        print("\nLoading existing vector database...")
        vector_db = VectorDatabase(embedding_model_name=embedding_model_name)
        vector_db.load(vector_db_path)
    
    # Extract text from PDF
    print(f"\n--- Extracting text from PDF: {pdf_path} ---")
    pdf_text = extract_text_from_pdf(str(pdf_file))
    
    if not pdf_text.strip():
        print("Error: No text could be extracted from the PDF.")
        return
    
    print(f"Extracted {len(pdf_text)} characters from PDF")
    
    # Chunk the text
    print(f"\n--- Chunking text (chunk_size={chunk_size}, overlap={chunk_overlap}) ---")
    chunks = chunk_text(pdf_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    print(f"Created {len(chunks)} text chunks")
    
    # Create metadata for each chunk
    metadata = [
        {
            "source": str(pdf_file.name),
            "chunk_index": i,
            "total_chunks": len(chunks)
        }
        for i in range(len(chunks))
    ]
    
    # Add chunks to vector database
    print(f"\n--- Adding chunks to vector database ---")
    vector_db.add_documents(chunks, metadata)
    
    # Save the vector database
    print(f"\n--- Saving vector database ---")
    os.makedirs(os.path.dirname(vector_db_path), exist_ok=True)
    vector_db.save(vector_db_path)
    
    print("\n" + "=" * 60)
    print("PDF processing complete!")
    print(f"Vector database saved to: {vector_db_path}")
    print(f"Total documents in database: {vector_db.index.ntotal}")
    print("=" * 60)
    
    return vector_db


def process_pdfs_from_directory(
    directory_path: str,
    vector_db_path: str = "knowledge-base/vector-stores/vector_db",
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    create_new: bool = False
):
    """
    Process all PDF files in a directory and create/update a vector database.
    
    Args:
        directory_path: Path to directory containing PDF files.
        vector_db_path: Path where to save the vector database (without extension).
        embedding_model_name: Hugging Face model name for embeddings.
        chunk_size: Size of text chunks in characters.
        chunk_overlap: Number of characters to overlap between chunks.
        create_new: If True, create a new database. If False, load existing and add to it.
    """
    print("=" * 60)
    print("Processing PDFs from Directory")
    print("=" * 60)
    
    directory = Path(directory_path)
    if not directory.exists():
        print(f"Error: Directory not found at {directory_path}")
        return
    
    # Find all PDF files
    pdf_files = list(directory.rglob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {directory_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s)")
    
    # Initialize or load vector database
    if create_new or not os.path.exists(f"{vector_db_path}.index"):
        print("\nCreating new vector database...")
        vector_db = VectorDatabase(embedding_model_name=embedding_model_name)
    else:
        print("\nLoading existing vector database...")
        vector_db = VectorDatabase(embedding_model_name=embedding_model_name)
        vector_db.load(vector_db_path)
    
    # Process each PDF
    for pdf_file in pdf_files:
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_file.name}")
        print(f"{'='*60}")
        
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(str(pdf_file))
        
        if not pdf_text.strip():
            print(f"Warning: No text extracted from {pdf_file.name}, skipping...")
            continue
        
        # Chunk the text
        chunks = chunk_text(pdf_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        print(f"Created {len(chunks)} text chunks")
        
        # Create metadata for each chunk
        metadata = [
            {
                "source": str(pdf_file.name),
                "file_path": str(pdf_file),
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            for i in range(len(chunks))
        ]
        
        # Add chunks to vector database
        vector_db.add_documents(chunks, metadata)
    
    # Save the vector database
    print(f"\n{'='*60}")
    print("Saving vector database...")
    os.makedirs(os.path.dirname(vector_db_path), exist_ok=True)
    vector_db.save(vector_db_path)
    
    print("\n" + "=" * 60)
    print("PDF processing complete!")
    print(f"Vector database saved to: {vector_db_path}")
    print(f"Total documents in database: {vector_db.index.ntotal}")
    print("=" * 60)
    
    return vector_db


def main():
    """Main function to process PDF files."""
    import sys
    
    # Default: process policy.pdf
    pdf_path = "knowledge-base/docs/policy.pdf"
    vector_db_path = "knowledge-base/vector-stores/vector_db"
    
    # Check if custom path provided
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    if len(sys.argv) > 2:
        vector_db_path = sys.argv[2]
    
    # Check if it's a directory or file
    path = Path(pdf_path)
    if path.is_dir():
        print(f"Processing all PDFs in directory: {pdf_path}")
        process_pdfs_from_directory(
            directory_path=pdf_path,
            vector_db_path=vector_db_path,
            create_new=True
        )
    elif path.is_file() and path.suffix.lower() == '.pdf':
        print(f"Processing PDF file: {pdf_path}")
        process_pdf_to_vector_db(
            pdf_path=pdf_path,
            vector_db_path=vector_db_path,
            create_new=True
        )
    else:
        print(f"Error: {pdf_path} is not a valid PDF file or directory")
        print("\nUsage:")
        print("  python process_pdf.py [pdf_path] [vector_db_path]")
        print("\nExamples:")
        print("  python process_pdf.py knowledge-base/docs/policy.pdf")
        print("  python process_pdf.py knowledge-base/docs/policy.pdf knowledge-base/vector-stores/my_db")
        print("  python process_pdf.py knowledge-base/docs/  # Process all PDFs in directory")


if __name__ == "__main__":
    main()