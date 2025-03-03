import pymongo

try:
    client = pymongo.MongoClient("mongodb+srv://noreplyemotion4u:45kVomOnb38h3VFU@emotion4u-basecluster.5gbds.mongodb.net/admin?retryWrites=true&loadBalanced=false&replicaSet=atlas-xp4kqi-shard-0&readPreference=primary&srvServiceName=mongodb&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-1")
    db = client["Emotion4U_UserDB"]
    collection = db["User"]

    # Sadece okuma işlemi yapıldığı için güvenlik kontrolü gerekmiyor.

    query = {"IsEmailConfirmed": 1}  # IsEmailConfirmed = 1 means email is confirmed.
    projection = {"_id": 0, "FullName": 1, "Email": 1} # Sadece gerekli alanları getir.

    confirmed_users = list(collection.find(query, projection))

    if confirmed_users:
        print(confirmed_users)
        client.close()
    else:
        print("Email'i onaylanmış kullanıcı bulunamadı.")
        client.close()

except pymongo.errors.PyMongoError as e:
    print("Exception")
except Exception as e:
    print("Exception")