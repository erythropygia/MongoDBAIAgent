import pymongo

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
            print(payment)
    
    except Exception as e:
        print(f"Bu işlemi gerçekleştirmeye yetkim yok: {e}")
    
    finally:
        # Bağlantıyı kapatma
        if 'client' in locals() and client:
            client.close()

# Fonksiyonu çağrma
get_payments()