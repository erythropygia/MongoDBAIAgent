import pymongo
from datetime import datetime

def get_payments():
    try:
        # MongoDB bağlantısı
        client = pymongo.MongoClient("mongodb+srv://noreplyemotion4u:45kVomOnb38h3VFU@emotion4u-basecluster.5gbds.mongodb.net/admin?retryWrites=true&loadBalanced=false&replicaSet=atlas-xp4kqi-shard-0&readPreference=primary&srvServiceName=mongodb&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-1")
        
        # Veritabanı seçimi
        db = client['Emotion4U_PaymentDB']
        
        # Koleksiyon seçimi
        collection = db['PaymentData']
        
        # Tüm payment bilgilerini getirme sorgusu
        payments = collection.find()
        
        # Sonuçları listeleme
        for payment in payments:
            print(f"_id: {payment['_id']}")
            print(f"CreatedAt: {payment['CreatedAt']}")
            print(f"PaymentId: {payment['PaymentId']}")
            print(f"Email: {payment['Email']}")
            print(f"Package: {payment['Package']}")
            print(f"Quota: EvaluateDataQuota = {payment['Quota']['EvaluateDataQuota']}, EvaluateCVQuota = {payment['Quota']['EvaluateCVQuota']}")
            print(f"Price: {payment['Price']}")
            print(f"Discount: {payment['Discount']}")
            print(f"AmountPaid: {payment['AmountPaid']}")
            print(f"PaymentStatus: {payment['PaymentStatus']}")
            print("-" * 40)
    
    except Exception as e:
        print(f"Bu işlemi gerçekleştirmeye yetkim yok: {e}")
    
    finally:
        # Bağlantıyı kapatma
        if 'client' in locals() and client:
            client.close()

# Fonksiyonu çağrma
get_payments()