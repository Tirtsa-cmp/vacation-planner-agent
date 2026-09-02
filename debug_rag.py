import chromadb

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="destinations")

test_queries = [
    "vacation destination for nature, cold, glaciers, volcanoes trip",
    "vacation destination for beach, relaxation trip",
    "vacation destination for history, culture trip"
]

for query in test_queries:
    print(f"\n--- Query: {query} ---")
    results = collection.query(query_texts=[query], n_results=3)
    for doc, dist in zip(results["documents"][0], results["distances"][0]):
        print(f"Distance: {dist:.3f} — {doc[:70]}...")