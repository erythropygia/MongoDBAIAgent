import pymongo

try:
    client = pymongo.MongoClient("mongodb+srv://noreplyemotion4u:45kVomOnb38h3VFU@emotion4u-basecluster.5gbds.mongodb.net/admin?retryWrites=true&loadBalanced=false&replicaSet=atlas-xp4kqi-shard-0&readPreference=primary&srvServiceName=mongodb&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-1")
    db = client["Emotion4U_PaymentDB"]
    collection = db["PaymentPackages"]

    pipeline = [
        {
            "$project": {
                "_id": 0,
                "Package": 1,
                "Price": 1
            }
        }
    ]

    results = list(collection.aggregate(pipeline))
    if results:
        for result in results:
            print(f"Paket Adı: {result['Package']}, Fiyat: {result['Price']}")
    else:
        print("Hiç paket bulunamadı.")

    client.close()
    print("İşlem başarılı.")

except pymongo.errors.PyMongoError as e:
    print("Exception")

except Exception as e:
    print("Exception")