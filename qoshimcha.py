# Ma'lumotlarni saqlash uchun vaqtinchalik ro'yxatlar (bazasiz)
books = []    # Kitoblar ro'yxati
members = []  # A'zolar ro'yxati
loans = []    # Berilgan kitoblar ro'yxati

while True:
    print("\n=== KUTUBXONA MENYUSI ===")
    print("1. Kitob qo'shish")
    print("2. Barcha kitoblar")
    print("3. Kitob qidirish")
    print("4. A'zo qo'shish")
    print("5. Kitob berish")
    print("6. Kitobni qaytarish")
    print("7. Kimda qaysi kitob bor")
    print("0. Chiqish")
    
    choice = input("Bo'limni tanlang: ").strip()

    if choice == "1":
        title = input("Kitob nomi: ").strip()
        author = input("Muallifi: ").strip()
        year = input("Chop etilgan yili: ").strip()
        
        if not year.isdigit():
            print("❌ Xato: Yil faqat raqamlardan iborat bo'lishi kerak!")
        elif not title or not author:
            print("❌ Kitob nomi va muallifi bo'sh bo'lishi mumkin emas!")
        else:
            book_id = len(books) + 1
            books.append({"id": book_id, "title": title, "author": author, "year": year, "status": "bor"})
            print(f"✅ Kitob muvaffaqiyatli qo'shildi! (ID: {book_id})")

    elif choice == "2":
        if not books:
            print("ℹ️ Kutubxonada hali kitoblar yo'q.")
        else:
            print("\n📚 BARCHA KITOBLAR RO'YXATI:")
            print(f"{'ID':<5} | {'Nomi':<25} | {'Muallifi':<20} | {'Yili':<6} | {'Holati':<10}")
            print("-" * 75)
            for b in books:
                print(f"{b['id']:<5} | {b['title']:<25} | {b['author']:<20} | {b['year']:<6} | {b['status']:<10}")

    elif choice == "3":
        search_text = input("Qidirish uchun so'z kiriting (nomi yoki muallifi): ").strip().lower()
        if not search_text:
            print("❌ Qidiruv matni bo'sh bo'lishi mumkin emas!")
            continue
            
        found_books = [b for b in books if search_text in b['title'].lower() or search_text in b['author'].lower()]
        
        if not found_books:
            print("🔍 Hech qanday kitob topilmadi.")
        else:
            print(f"\n🔍 TOPILGAN KITOBLAR ({len(found_books)} ta):")
            for b in found_books:
                print(f"ID: {b['id']} | [{b['title']}] - {b['author']} ({b['year']}-yil) | Holati: {b['status']}")

    elif choice == "4":
        name = input("A'zoning ismi va familiyasi: ").strip()
        phone = input("Telefon raqami: ").strip()
        
        if not name or not phone:
            print("❌ Ism va telefon raqami bo'sh bo'lishi mumkin emas!")
        else:
            member_id = len(members) + 1
            members.append({"id": member_id, "name": name, "phone": phone})
            print(f"✅ Yangi a'zo muvaffaqiyatli qo'shildi! (ID: {member_id})")

    elif choice == "5":
        m_id_in = input("A'zo ID sini kiriting: ").strip()
        b_id_in = input("Kitob ID sini kiriting: ").strip()
        
        if not m_id_in.isdigit() or not b_id_in.isdigit():
            print("❌ Xato: ID faqat raqam bo'lishi kerak!")
            continue
            
        m_id = int(m_id_in)
        b_id = int(b_id_in)
        
        # A'zo bormi?
        member_found = next((m for m in members if m['id'] == m_id), None)
        # Kitob bormi?
        book_found = next((b for b in books if b['id'] == b_id), None)
        
        if not member_found:
            print("❌ Xato: Bunday ID dagi a'zo mavjud emas!")
        elif not book_found:
            print("❌ Xato: Bunday ID dagi kitob mavjud emas!")
        elif book_found['status'] == "berilgan":
            print("❌ Bu kitob allaqachon kimdir tomonidan ijaraga olingan (berilgan)!")
        else:
            book_found['status'] = "berilgan"
            loans.append({"book_id": b_id, "book_title": book_found['title'], "book_author": book_found['author'], "member_name": member_found['name']})
            print("✅ Kitob a'zoga muvaffaqiyatli berildi!")

    elif choice == "6":
        b_id_in = input("Qaytariladigan kitob ID sini kiriting: ").strip()
        
        if not b_id_in.isdigit():
            print("❌ Xato: ID faqat raqam bo'lishi kerak!")
            continue
            
        b_id = int(b_id_in)
        book_found = next((b for b in books if b['id'] == b_id), None)
        
        if not book_found:
            print("❌ Xato: Bunday ID dagi kitob mavjud emas!")
        elif book_found['status'] == "bor":
            print("ℹ️ Bu kitob javonda turibdi (ijaraga berilmagan).")
        else:
            book_found['status'] = "bor"
            # loans ro'yxatidan o'chirish
            loans = [ln for ln in loans if ln['book_id'] != b_id]
            print("✅ Kitob muvaffaqiyatli qaytarib olindi va holati 'bor' deb o'zgartirildi!")

    elif choice == "7":
        if not loans:
            print("ℹ️ Hozircha ijaraga berilgan kitoblar yo'q.")
        else:
            print("\n📋 IJARAGA BERILGAN KITOBLAR VA ULARNING EGALARI:")
            print(f"{'Kitob ID':<10} | {'Kitob Nomi':<25} | {'Muallifi':<20} | {'Azo Ismi':<20}")
            print("-" * 80)
            for ln in loans:
                print(f"{ln['book_id']:<10} | {ln['book_title']:<25} | {ln['book_author']:<20} | {ln['member_name']:<20}")

    elif choice == "0":
        print("👋 Dastur yakunlandi. Salomat bo'ling!")
        break
    else:
        print("❌ Noto'g'ri buyruq! Ro'yxatdagi raqamlardan birini tanlang.")