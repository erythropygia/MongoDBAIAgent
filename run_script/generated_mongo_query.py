import pymongo

try:
    client = pymongo.MongoClient("mongodb+srv://noreplyemotion4u:45kVomOnb38h3VFU@emotion4u-basecluster.5gbds.mongodb.net/admin?retryWrites=true&loadBalanced=false&replicaSet=atlas-xp4kqi-shard-0&readPreference=primary&srvServiceName=mongodb&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-1")
    db = client["Emotion4U_PaymentDB"]
    collection = db["PaymentData"]
    
    user_data = collection.find({})
    
    for data in user_data:
        print(data)

    client.close()
    print("Success")

except Exception as e:
    print("Exception")