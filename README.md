# MathLib BSU Pro

**Китобхонаи электронии факултети математикаи Донишгоҳи давлатии Бохтар ба номи Носири Хусрав**

Лоиҳа бо **Python + Django + PostgreSQL** сохта шудааст. Нақшҳо: **Админ, Китобдор, Омӯзгор, Донишҷӯ**.

---

## 1. Имкониятҳо

- Бақайдгирии корбар бо донишгоҳ, факултет, ихтисос, курс ва гурӯҳ
- Нақшҳо: Админ, Китобдор, Омӯзгор, Донишҷӯ
- Панели алоҳида барои ҳар нақш
- Иловаи китоб бо муқова ва файли PDF/DOC/DOCX
- Тасдиқи китоб аз тарафи китобдор ё админ
- Ҷустуҷӯ ва филтр аз рӯйи категория, забон, муаллиф
- Дӯстдоштаҳо барои донишҷӯён
- Дархости китоб аз тарафи донишҷӯ
- Сабти зеркашиҳо
- Audit log барои амалҳои муҳим
- PostgreSQL-ready
- Интерфейси академӣ ва мутобиқ ба факултет

---

## 2. Насб дар Windows

```bash
cd mathlib_bsu_pro
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Файли `.env.example`-ро ба `.env` нусха кунед:

```bash
copy .env.example .env
```

---

## 3. Сохтани PostgreSQL database

Дар PostgreSQL ин фармонҳоро иҷро кунед:

```sql
CREATE DATABASE mathlib_bsu;
CREATE USER mathlib_user WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE mathlib_bsu TO mathlib_user;
```

Агар PostgreSQL 15+ бошад ва permission мушкил диҳад, баъд аз пайваст шудан ба database иҷро кунед:

```sql
\c mathlib_bsu
GRANT ALL ON SCHEMA public TO mathlib_user;
ALTER SCHEMA public OWNER TO mathlib_user;
```

---

## 4. Мигратсия ва оғоз

```bash
python manage.py makemigrations accounts library
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_initial_data
python manage.py runserver
```

Сипас кушоед:

```text
http://127.0.0.1:8000/
```

Админпанел:

```text
http://127.0.0.1:8000/admin/
```

---

## 5. Қоидаи нақшҳо

- Корбари нав ҳамеша ҳамчун **Донишҷӯ** сабт мешавад.
- Танҳо админ метавонад нақшро ба **Китобдор** ё **Омӯзгор** иваз кунад.
- Омӯзгор метавонад китоб пешниҳод кунад, вале китоб то тасдиқи китобдор/админ нашр намешавад.
- Китобдор метавонад китобҳоро тасдиқ, таҳрир ва идора кунад.

---

## 6. Барои production

Пеш аз гузоштан дар сервер:

1. `DEBUG=False`
2. `SECRET_KEY`-ро иваз кунед
3. `ALLOWED_HOSTS`-ро бо домени худ пур кунед
4. HTTPS фаъол кунед
5. `SECURE_SSL_REDIRECT=True`
6. `SESSION_COOKIE_SECURE=True`
7. `CSRF_COOKIE_SECURE=True`
8. Backup-и PostgreSQL созед
9. Media-файлҳоро бо permission дуруст нигоҳ доред

---

## 7. Фармонҳои муфид

```bash
python manage.py createsuperuser
python manage.py seed_initial_data
python manage.py collectstatic
python manage.py check --deploy
```

---

## 8. Сохтори лоиҳа

```text
accounts/   — корбарон, донишгоҳ, факултет, ихтисос, бақайдгирӣ
library/    — китобҳо, муаллифон, категорияҳо, файлҳо, дархостҳо
dashboard/  — панелҳои нақшҳо
config/     — settings, urls, wsgi, asgi
templates/  — HTML шаблонҳо
static/     — CSS ва файлҳои интерфейс
media/      — китобҳо ва муқоваҳо
```

---

## 9. Эзоҳи муҳим

Ин версия ядрои қавии лоиҳа аст. Барои истифодаи расмӣ дар факултет бояд баъд аз санҷиши дохилӣ:

- сиёсати ҳуқуқи муаллиф,
- тартиби иҷозати PDF,
- backup,
- SSL,
- hosting,
- ва масъулияти китобдор муайян карда шавад.

