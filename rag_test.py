import chromadb

# Create a Chroma client (local, in-memory mode — everything stays on your machine)
chroma_client = chromadb.Client()

# Create a collection (similar to a table in a traditional database)
collection = chroma_client.create_collection(name="destinations_test")

# Add sample documents (Chroma automatically computes embeddings for each one)
collection.add(
    documents=[
        "Bali is a tropical island in Indonesia known for beaches, surfing, rice terraces, and a relaxed atmosphere.",
        "Paris is the capital of France, famous for museums, historic architecture, and fine dining.",
        "The Swiss Alps offer world-class skiing, hiking trails, and stunning mountain scenery."
    ],
    ids=["doc1", "doc2", "doc3"]
)

# Query the collection using a natural language question
# Chroma searches by meaning (semantic similarity), not by exact keyword matching
results = collection.query(
    query_texts=["I want a relaxing beach vacation"],
    n_results=2
)

print(results)