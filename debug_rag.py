import chromadb

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="destinations")

results = collection.query(
    query_texts=["vacation destination for nature, cold, glaciers, volcanoes trip"],
    n_results=5  # on demande tout pour voir toutes les distances
)

for doc, dist in zip(results["documents"][0], results["distances"][0]):
    print(f"Distance: {dist:.3f} — {doc[:80]}...")