# Ilova uchun litsenziya kalitlari

Admin saytning bosh sahifasida kalit yaratadi, muddat belgilaydi va kalitni bekor qiladi. To‘liq kalit yaratilganda bir marta ko‘rsatiladi. Bazada uning SHA-256 xeshi saqlanadi. Eski demo brauzeridagi kalitlar yangi serverga ko‘chirilmaydi. Bu versiyada kalit amal qilish muddati va bekor qilinganligi bo‘yicha tekshiriladi. Kalit qurilmaga bog‘lanmaydi.

## Windows’da ishga tushirish

Python 3.11 yoki yangiroq versiyasini ishlating. ZIP faylini ochib, app.py turgan papkada PowerShell orqali ishga tushiring.

~~~powershell
py -m pip install -r requirements.txt
py app.py
~~~

Brauzerda http://127.0.0.1:8080 ni oching. Login khakimovv1. ZIP ichidagi admin.password faylida siz belgilagan parol bor. Ushbu fayl shaxsiy va Git tomonidan e’tiborga olinmaydi.

## Hosting

Python web service uchun build buyrug‘i pip install -r requirements.txt va start buyrug‘i python app.py. Hostingda ADMIN_PASSWORD ga belgilagan parolingizni kiriting. Standart login khakimovv1, uni ADMIN_USERNAME orqali o‘zgartirish mumkin. HOST qiymatini 0.0.0.0 qiling. Server hosting bergan PORT ni o‘qiydi. HTTPS ishlating. Bitta server jarayoni va doimiy disk talab qilinadi. Masalan, doimiy disk /var/data manziliga ulangan bo‘lsa, LICENSE_DB=/var/data/licenses.sqlite3 belgilang. Lokal standart joy data/licenses.sqlite3.

## Ilovadan tekshirish

Ilovaga o‘z serveringizning HTTPS manzilini kiriting. Ilova ishga tushganda foydalanuvchi kalitini yuborsin.

~~~http
POST /api/licenses/verify
Content-Type: application/json

{"key":"FOYDALANUVCHI_KALITI"}
~~~

HTTP 200 va valid qiymati aynan true bo‘lsa, kirishga ruxsat bering. Noma’lum, bekor qilingan va muddati tugagan kalitlarga HTTP 200 hamda {"valid":false} qaytadi. Aloqa yoki javob formati xatosida kirishni yopiq saqlang. Ishlayotgan ilovada bekor qilish kuchga kirishi uchun sessiya davomida ham qayta tekshiring. Admin paroli faqat admin panelida ishlatiladi.

VNHAX_PUBG_iOS_report.md asl arxivdagi hisobot. Server mustaqil ishlaydi.
