from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


# 🔁 GET all active products
@app.route("/products", methods=["GET"])
def get_products():
    now = datetime.now()
    products_ref = db.collection("products")
    docs = products_ref.stream()

    result = []
    for doc in docs:
        product = doc.to_dict()
        product_id = doc.id

        if "end_time" not in product:
            continue

        try:
            end_time = datetime.fromisoformat(product["end_time"])
        except Exception:
            continue

        if now < end_time:
            time_remaining = end_time - now
            product["product_id"] = product_id
            product["time_remaining"] = str(time_remaining)
            result.append(product)

    return jsonify(result), 200


# 🔍 GET a single product by name (case-insensitive)
@app.route("/product", methods=["GET"])
def get_product():
    product_name = request.args.get("product_name")
    if not product_name:
        return jsonify({"error": "Missing product_name"}), 400

    products_ref = db.collection("products")
    docs = products_ref.stream()

    for doc in docs:
        product = doc.to_dict()
        if product["name"].lower() == product_name.lower():
            return jsonify(product), 200

    return jsonify({"error": "Product not found"}), 404


# 💰 POST a new bid on a product
@app.route("/product/bid", methods=["POST"])
def post_bid():
    req_data = request.get_json()
    product_name = req_data.get("product_name")
    amount = req_data.get("amount")
    user = req_data.get("user", "Anonymous")

    if not product_name:
        return jsonify({"error": "Missing product_name"}), 400
    if amount is None or not isinstance(amount, (int, float)):
        return jsonify({"error": "Invalid bid amount"}), 400

    products_ref = db.collection("products")
    docs = products_ref.stream()

    for doc in docs:
        product = doc.to_dict()
        if product["name"].lower() == product_name.lower():
            doc_ref = db.collection("products").document(doc.id)

            current_highest = product.get("highest_bid", 0)
            if amount > current_highest:
                product["highest_bid"] = amount
                if "bidding_history" not in product:
                    product["bidding_history"] = []
                product["bidding_history"].append({
                    "user": user,
                    "amount": amount
                })

                # Save back to Firestore
                doc_ref.set(product)
                return jsonify({
                    "message": "Bid accepted",
                    "new_highest": amount
                }), 200
            else:
                return jsonify({
                    "error": "Bid must be higher than current highest bid",
                    "current_highest": current_highest
                }), 400

    return jsonify({"error": "Product not found"}), 404


# 📊 GET auction stats
@app.route("/stats", methods=["GET"])
def get_stats():
    stats = {}
    products_ref = db.collection("products")
    docs = products_ref.stream()

    for doc in docs:
        product = doc.to_dict()
        product_id = doc.id
        total_bids = len(product.get("bidding_history", []))
        highest_bid = product.get("highest_bid", 0)
        stats[product_id] = {
            "total_bids": total_bids,
            "highest_bid": highest_bid
        }

    return jsonify(stats), 200


# 🏁 Run app
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
