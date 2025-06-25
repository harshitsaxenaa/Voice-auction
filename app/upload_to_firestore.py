import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase app
cred = credentials.Certificate("firebase_key.json") 
firebase_admin.initialize_app(cred)
db = firestore.client()

with open("data.json", "r") as f:
    data = json.load(f)
for product_id, product in data.items():
    # Convert end_time string to Firestore timestamp
    try:
        product["end_time"] = datetime.fromisoformat(product["end_time"]).isoformat()
    except Exception:
        print(f"Skipping {product_id}, invalid end_time")
        continue

    db.collection("products").document(product_id).set(product)
    print(f"Uploaded {product['name']} ({product_id})")

print("Upload complete!")
