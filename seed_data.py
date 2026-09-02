import chromadb

chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Delete the old collection if it exists, to start fresh with the new richer dataset
try:
    chroma_client.delete_collection(name="destinations")
except Exception:
    pass

collection = chroma_client.get_or_create_collection(name="destinations")

destinations = [
    {"id": "israel", "text": "Israel offers a unique mix of history, religion, culture, and Mediterranean beaches. Highlights include Jerusalem's Old City, Tel Aviv's vibrant beach and nightlife scene, floating in the Dead Sea, and desert adventures in the Negev. Great for travelers interested in history, culture, food, and a mix of city and nature. Mid-range budget destination."},
    {"id": "greece", "text": "Greece is famous for whitewashed island villages, crystal-clear Aegean Sea beaches, ancient ruins like the Acropolis, and delicious Mediterranean food. Ideal for couples, culture lovers, and beach relaxation. Mid-range budget, varies by island."},
    {"id": "italy", "text": "Italy offers rich history, world-class art, iconic cities like Rome, Florence, and Venice, and outstanding food and wine. Great for culture lovers, foodies, and romantic getaways. Mid to higher budget destination."},
    {"id": "spain", "text": "Spain combines vibrant cities, stunning beaches, flamenco culture, and excellent tapas and nightlife. Barcelona, Madrid, and the Costa del Sol are popular. Great for groups, couples, and culture-and-beach combo trips. Mid-range budget."},
    {"id": "portugal", "text": "Portugal offers charming coastal towns, historic Lisbon, affordable prices, and beautiful beaches in the Algarve. Great value destination for culture, food, and relaxed beach time. Budget-friendly for Western Europe."},
    {"id": "turkey", "text": "Turkey blends European and Asian cultures, with highlights like Istanbul's historic mosques and bazaars, Cappadocia's hot air balloons, and Mediterranean beach resorts. Great for culture, adventure, and affordable luxury. Budget to mid-range."},
    {"id": "egypt", "text": "Egypt is known for ancient pyramids, the Nile River, Red Sea diving and snorkeling, and rich history. Ideal for history enthusiasts and adventure travelers interested in diving. Budget-friendly destination."},
    {"id": "jordan", "text": "Jordan features the ancient city of Petra, desert adventures in Wadi Rum, and floating in the Dead Sea. Great for history and adventure travelers seeking a unique Middle Eastern experience. Mid-range budget."},
    {"id": "dubai", "text": "Dubai offers ultra-modern architecture, luxury shopping, desert safaris, and beach resorts. Ideal for travelers wanting a mix of luxury, adventure, and modern city experiences. Higher budget destination."},
    {"id": "maldives", "text": "The Maldives is a luxury tropical paradise with overwater bungalows, pristine white beaches, and world-class diving and snorkeling. Ideal for honeymooners and couples seeking ultimate relaxation. Higher budget destination."},
    {"id": "seychelles", "text": "Seychelles offers pristine beaches, lush jungle, and luxury island resorts. Great for honeymoons and relaxing tropical getaways with a focus on nature and privacy. Higher budget destination."},
    {"id": "vietnam", "text": "Vietnam offers stunning landscapes from Ha Long Bay to rice terraces, vibrant street food culture, and affordable travel. Great for backpackers, culture lovers, and food enthusiasts. Budget-friendly."},
    {"id": "cambodia", "text": "Cambodia is home to the ancient temples of Angkor Wat, a rich cultural history, and affordable travel costs. Ideal for history and culture enthusiasts on a budget. Budget-friendly destination."},
    {"id": "philippines", "text": "The Philippines offers thousands of islands with white-sand beaches, world-class diving, and friendly local culture. Great for beach lovers, divers, and island-hopping adventures. Budget to mid-range."},
    {"id": "sri_lanka", "text": "Sri Lanka combines beaches, tea plantations, ancient temples, and wildlife safaris in a compact island. Great for travelers wanting variety - nature, culture, and relaxation. Budget-friendly."},
    {"id": "nepal", "text": "Nepal is a premier destination for trekking and mountaineering, home to the Himalayas including Everest Base Camp routes. Ideal for serious hikers and adventure seekers. Budget-friendly, though gear and permits add cost."},
    {"id": "peru", "text": "Peru offers Machu Picchu, Andean mountain treks, Amazon rainforest experiences, and rich Incan history. Great for adventure travelers and history enthusiasts. Mid-range budget."},
    {"id": "argentina", "text": "Argentina features Patagonia's dramatic landscapes, tango culture in Buenos Aires, and excellent steak and wine. Great for adventure travelers and culture lovers. Mid-range budget."},
    {"id": "brazil", "text": "Brazil offers vibrant Rio de Janeiro beaches, the Amazon rainforest, and lively carnival culture. Great for beach lovers, nature enthusiasts, and those seeking vibrant nightlife. Mid-range budget."},
    {"id": "chile", "text": "Chile spans deserts, glaciers, and Patagonian wilderness, offering incredible landscape diversity. Great for adventure travelers and nature photographers. Mid-range budget."},
    {"id": "mexico_city", "text": "Mexico City offers rich history, world-class museums, incredible street food, and vibrant neighborhoods. Great for culture lovers and foodies seeking an affordable big-city experience. Budget-friendly."},
    {"id": "costa_rica", "text": "Costa Rica is known for rainforests, volcanoes, wildlife, and eco-tourism adventures like zip-lining and surfing. Ideal for nature lovers and adventure travelers. Mid-range budget."},
    {"id": "belize", "text": "Belize offers Caribbean beaches, the Great Blue Hole for diving, and Mayan ruins in a laid-back setting. Great for divers, snorkelers, and adventure travelers. Mid-range budget."},
    {"id": "canada_banff", "text": "Banff, Canada offers turquoise glacial lakes, dramatic Rocky Mountain scenery, and excellent hiking and skiing. Great for nature lovers and outdoor adventurers in all seasons. Mid to higher budget."},
    {"id": "alaska", "text": "Alaska offers glaciers, wildlife viewing, and dramatic wilderness landscapes. Ideal for nature lovers seeking a remote adventure with whale watching and hiking. Higher budget destination."},
    {"id": "new_zealand", "text": "New Zealand offers dramatic landscapes combining mountains, glaciers, fjords, and volcanic areas. Great for adventure travelers interested in hiking, extreme sports, and stunning nature. Mid to higher budget destination."},
    {"id": "australia", "text": "Australia offers the Great Barrier Reef, unique wildlife, vibrant cities like Sydney, and vast outback landscapes. Great for beach lovers, nature enthusiasts, and adventure travelers. Higher budget due to distance and costs."},
    {"id": "fiji", "text": "Fiji offers tropical islands, coral reefs, and a relaxed South Pacific atmosphere. Ideal for honeymooners and travelers seeking a remote beach paradise. Higher budget destination due to travel distance."},
    {"id": "thailand_islands", "text": "Thailand's southern islands like Koh Phi Phi and Koh Samui offer stunning limestone cliffs, turquoise water, and vibrant beach parties. Great for young travelers and beach lovers. Budget-friendly."},
    {"id": "morocco", "text": "Morocco offers a mix of desert adventure, vibrant markets, historic medinas, and Atlas Mountains hiking. Great for travelers interested in culture, adventure, and a more affordable exotic destination."},
    {"id": "south_africa", "text": "South Africa combines wildlife safaris, stunning coastline, wine country, and vibrant cities like Cape Town. Great for adventure travelers seeking wildlife and diverse landscapes. Mid-range budget."},
    {"id": "kenya", "text": "Kenya is a premier safari destination with the Maasai Mara offering incredible wildlife viewing including the Great Migration. Ideal for wildlife enthusiasts and adventure travelers. Mid to higher budget due to safari costs."},
    {"id": "tanzania", "text": "Tanzania offers safari adventures in the Serengeti, plus Mount Kilimanjaro for trekkers, and Zanzibar's beaches. Great for combining wildlife, adventure, and beach relaxation. Higher budget destination."},
    {"id": "iceland", "text": "Iceland is known for dramatic cold-climate nature: glaciers, active volcanoes, geothermal hot springs, and the Northern Lights. Ideal for adventurous nature lovers seeking a unique, rugged landscape. Higher budget destination due to cost of living, but shoulder season travel can reduce costs."},
    {"id": "norway", "text": "Norway offers dramatic fjords, the Northern Lights, and stunning hiking trails. Great for nature lovers and photographers seeking Scandinavian scenery. Higher budget destination."},
    {"id": "scotland", "text": "Scotland offers dramatic highlands, historic castles, and charming cities like Edinburgh. Great for history lovers and hikers seeking rugged natural beauty. Mid-range budget."},
    {"id": "ireland", "text": "Ireland features green rolling hills, dramatic coastal cliffs, and a rich pub culture with traditional music. Great for road trips, nature lovers, and culture enthusiasts. Mid-range budget."},
    {"id": "croatia", "text": "Croatia offers stunning Adriatic coastline, historic old towns like Dubrovnik, and island hopping. Great for beach lovers and history enthusiasts seeking a more affordable Mediterranean alternative. Mid-range budget."},
    {"id": "germany", "text": "Germany combines historic cities, castles, beer culture, and Christmas markets. Great for culture lovers and history enthusiasts. Mid-range budget."},
    {"id": "netherlands", "text": "The Netherlands offers charming canals in Amsterdam, tulip fields, and cycling culture. Great for city breaks and cultural exploration. Mid to higher budget."},
    {"id": "switzerland_alps", "text": "The Swiss Alps offer world-class skiing and snowboarding in winter, and extensive hiking trails with stunning mountain scenery in summer. Great for active travelers and nature lovers, families, or groups looking for outdoor adventure. Higher budget due to Switzerland's cost of living."},
    {"id": "austria", "text": "Austria offers alpine scenery, classical music heritage in Vienna, and charming towns like Salzburg. Great for culture lovers and winter sports enthusiasts. Mid to higher budget."},
    {"id": "kyoto_japan", "text": "Kyoto, Japan is the cultural heart of Japan, known for ancient temples, traditional gardens, and geisha districts. Ideal for travelers interested in history, culture, and a peaceful, contemplative atmosphere. Mid to higher budget destination."},
    {"id": "tokyo", "text": "Tokyo offers a fascinating blend of ultra-modern technology and traditional culture, incredible food, and vibrant neighborhoods. Great for city lovers, foodies, and pop culture enthusiasts. Higher budget destination."},
    {"id": "south_korea", "text": "South Korea offers vibrant Seoul, K-pop culture, delicious food, and historic palaces alongside modern technology. Great for young travelers and culture enthusiasts. Mid-range budget."},
    {"id": "bali", "text": "Bali, Indonesia is a tropical island known for beautiful beaches, world-class surfing, lush rice terraces, and a relaxed, spiritual atmosphere. Popular with couples and solo travelers seeking relaxation combined with adventure like hiking volcanoes or visiting waterfalls. Mid-range budget destination."},
    {"id": "paris_france", "text": "Paris, France is a major cultural capital known for iconic landmarks like the Eiffel Tower, world-class museums like the Louvre, and fine dining. Ideal for travelers interested in history, art, architecture, and romantic city breaks. Can be a higher-budget destination depending on season."},
    {"id": "cancun_mexico", "text": "Cancun, Mexico is a popular all-inclusive beach destination with white sand beaches, warm turquoise water, and a lively nightlife scene. Great for groups, couples, and budget-conscious travelers seeking a classic beach vacation with easy logistics."},
    {"id": "hawaii", "text": "Hawaii offers volcanic landscapes, stunning beaches, lush rainforests, and unique island culture. Great for honeymooners, families, and nature lovers seeking a mix of relaxation and outdoor adventure. Higher budget destination."},
    {"id": "las_vegas", "text": "Las Vegas offers world-class entertainment, casinos, nightlife, and easy access to natural wonders like the Grand Canyon. Great for groups and travelers seeking entertainment and nightlife. Mid-range budget."},
]

collection.add(
    documents=[d["text"] for d in destinations],
    ids=[d["id"] for d in destinations]
)

print(f"Added {len(destinations)} destinations. Total in collection: {collection.count()}")