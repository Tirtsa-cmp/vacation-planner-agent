import chromadb

# Persistent client: data is saved to disk in the given folder, and survives between script runs
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# get_or_create avoids an error if the collection already exists from a previous run
collection = chroma_client.get_or_create_collection(name="destinations")

destinations_data = [
    {"id": "bali", "text": "Bali, Indonesia is a tropical island known for beautiful beaches, world-class surfing, lush rice terraces, and a relaxed, spiritual atmosphere. Popular with couples and solo travelers seeking relaxation combined with adventure like hiking volcanoes or visiting waterfalls. Mid-range budget destination."},
    {"id": "paris", "text": "Paris, France is a major cultural capital known for iconic landmarks like the Eiffel Tower, world-class museums like the Louvre, and fine dining. Ideal for travelers interested in history, art, architecture, and romantic city breaks. Can be a higher-budget destination depending on season."},
    {"id": "swiss_alps", "text": "The Swiss Alps offer world-class skiing and snowboarding in winter, and extensive hiking trails with stunning mountain scenery in summer. Great for active travelers and nature lovers, families, or groups looking for outdoor adventure. Higher budget due to Switzerland's cost of living."},
    {"id": "cancun", "text": "Cancun, Mexico is a popular all-inclusive beach destination with white sand beaches, warm turquoise water, and a lively nightlife scene. Great for groups, couples, and budget-conscious travelers seeking a classic beach vacation with easy logistics."},
    {"id": "kyoto", "text": "Kyoto, Japan is the cultural heart of Japan, known for ancient temples, traditional gardens, and geisha districts. Ideal for travelers interested in history, culture, and a peaceful, contemplative atmosphere. Mid to higher budget destination."}
]

# Add all documents to the collection at once
collection.add(
    documents=[d["text"] for d in destinations_data],
    ids=[d["id"] for d in destinations_data]
)

results = collection.query(
    query_texts=["a peaceful cultural trip with historic sites"],
    n_results=2
)

print(results["documents"])
print(results["distances"])