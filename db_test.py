import psycopg2

try:
    # PostgreSQL bağlantı bilgileri (şifreni kendi şifrenle değiştirmelisin)
    connection = psycopg2.connect(
        dbname="bist_db",
        user="postgres",
        password="esma3762",  # PostgreSQL kurarken girdiğin şifre
        host="localhost",
        port="5432"
    )
    print("Tebrikler! PostgreSQL veritabanına başarıyla bağlandık.")
    connection.close()
except Exception as e:
    print("Bağlantı hatası:", e)