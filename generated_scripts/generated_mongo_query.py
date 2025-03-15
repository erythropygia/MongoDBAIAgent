import pymongo
import pandas as pd

try:
    client = pymongo.MongoClient("mongodb+srv://noreplyemotion4u:45kVomOnb38h3VFU@emotion4u-basecluster.5gbds.mongodb.net/admin?retryWrites=true&loadBalanced=false&replicaSet=atlas-xp4kqi-shard-0&readPreference=primary&srvServiceName=mongodb&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-1")
    db = client["Emotion4U_PaymentDB"]
    collection = db["PaymentData"]

    cursor = collection.find({})
    data = list(cursor)

    if data:
        df = pd.DataFrame(data)
        # ObjectId'leri kaldır
        df = df.drop('_id', axis=1)
        # Quota alanını ayır
        df['EvaluateDataQuota'] = df['Quota'].apply(lambda x: x['EvaluateDataQuota'] if isinstance(x, dict) and 'EvaluateDataQuota' in x else None)
        df['EvaluateCVQuota'] = df['Quota'].apply(lambda x: x['EvaluateCVQuota'] if isinstance(x, dict) and 'EvaluateCVQuota' in x else None)
        df = df.drop('Quota', axis=1) #Quota sütununu kaldır


        df.to_excel("payments.xlsx", index=False)
        response = "Payments exported to payments.xlsx"
    else:
        response = "No data found"

except Exception as e:
    response = "Exception"

finally:
    client.close()
    print(response)