import pymongo
from pymongo import MongoClient

try:
    client = pymongo.MongoClient("mongodb+srv://noreplyemotion4u:45kVomOnb38h3VFU@emotion4u-basecluster.5gbds.mongodb.net/admin?retryWrites=true&loadBalanced=false&replicaSet=atlas-xp4kqi-shard-0&readPreference=primary&srvServiceName=mongodb&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-1")
    db = client["Emotion4U_UserDB"]
    collection = db["User"]

    # En son kaydolan kullanıcının email bilgisini bulma
    last_registered_user = collection.find().sort("CreatedAt", -1).limit(1)

    for user in last_registered_user:
        email = user["Email"]
        print(f"Response: En son kaydolan kullanıcının email adresi: {email}")
        break  # Sadece ilk (en son) sonucu alıyoruz
    else:
        print("Response: Kayıtlı kullanıcı bulunamadı.")

    client.close()

except pymongo.errors.PyMongoError as e:
    print("Exception")


except Exception as e:
    print("Exception")