import pymongo
from datetime import datetime
import pandas as pd

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
        
        # Verileri bir liste olarak toplama
        data = []
        for payment in payments:
            data.append({
                '_id': str(payment['_id']),
                'CreatedAt': payment['CreatedAt'],
                'PaymentId': payment['PaymentId'],
                'Email': payment['Email'],
                'Package': payment['Package'],
                'EvaluateDataQuota': payment['Quota']['EvaluateDataQuota'],
                'EvaluateCVQuota': payment['Quota']['EvaluateCVQuota'],
                'Price': payment['Price'],
                'Discount': payment['Discount'],
                'AmountPaid': payment['AmountPaid'],
                'PaymentStatus': payment['PaymentStatus']
            })
        
        # Verileri bir DataFrame'e dönüştürme
        df = pd.DataFrame(data)
        
        # Excel dosyasına yazdırma
        excel_filename = "payments.xlsx"
        df.to_excel(excel_filename, index=False)
        print(f"Payment bilgileri başarıyla {excel_filename} dosyasına yazıldı.")
    
    except Exception as e:
        print(f"Bu işlemi gerçekleştirmeye yetkim yok: {e}")
    
    finally:
        # Bağlantıyı kapatma
        if 'client' in locals() and client:
            client.close()

# Fonksiyonu çağrma
get_payments()