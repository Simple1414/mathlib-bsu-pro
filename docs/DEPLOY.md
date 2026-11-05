# Дастури гузоштани MathLib BSU Pro дар интернет

Ин дастур барои сервери **Ubuntu 22.04/24.04** (VPS) бо домени худатон аст.
Сохтор: **nginx (HTTPS) → gunicorn → Django → PostgreSQL**.

> Ҳамаи фармонҳоро бо корбари дорои `sudo` иҷро кунед. Ба ҷои `your-domain.tj` домени худро нависед.

---

## 0. Чӣ лозим аст

- Сервер (VPS) бо IP-и доимӣ, ҳадди ақал 1 vCPU, 2 GB RAM, 20 GB диск.
- Домен (масалан `mathlib.bsu.tj`), ки сабти **A** ба IP-и сервер ишора мекунад.
- Портҳои **80** ва **443** дар firewall кушода бошанд.

## 1. Насби бастаҳо

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-dev build-essential \
    postgresql nginx certbot git
sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable
```

## 2. PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE mathlib_bsu;
CREATE USER mathlib_user WITH PASSWORD 'ПАРОЛИ_ҚАВӢ';
ALTER DATABASE mathlib_bsu OWNER TO mathlib_user;
\q
```

## 3. Рамз ва муҳит

```bash
sudo mkdir -p /var/www && cd /var/www
sudo git clone https://github.com/Simple1414/mathlib-bsu-pro.git mathlib_bsu_pro
cd mathlib_bsu_pro
sudo python3 -m venv .venv
sudo .venv/bin/pip install -r requirements.txt

sudo cp .env.example .env
sudo nano .env        # қиматҳоро пур кунед (поёнро бинед)
```

Дар `.env` ҳатман иваз кунед:

| Тағйирёбанда | Қимат |
|---|---|
| `SECRET_KEY` | натиҷаи `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `ALLOWED_HOSTS` | `your-domain.tj,www.your-domain.tj,127.0.0.1,localhost` |
| `CSRF_TRUSTED_ORIGINS` | `https://your-domain.tj,https://www.your-domain.tj` |
| `DB_PASSWORD` | пароли қадами 2 |

> Агар `SECRET_KEY` холӣ ё кӯтоҳ бошад, барнома бо `DEBUG=False` **оғоз намешавад** — ин барои амният аст.

## 4. Омода кардани барнома

```bash
sudo mkdir -p media
sudo chown -R www-data:www-data /var/www/mathlib_bsu_pro
sudo chmod 600 .env

sudo -u www-data .venv/bin/python manage.py migrate
sudo -u www-data .venv/bin/python manage.py seed_initial_data
sudo -u www-data .venv/bin/python manage.py collectstatic --noinput
sudo -u www-data .venv/bin/python manage.py createsuperuser
sudo -u www-data .venv/bin/python manage.py check --deploy
```

`check --deploy` бояд танҳо огоҳиҳои `W005` ва `W021` (HSTS subdomains/preload) нишон диҳад — онҳо қасдан хомӯшанд.

## 5. Gunicorn (systemd)

```bash
sudo cp deploy/gunicorn.service.example /etc/systemd/system/mathlib.service
sudo systemctl daemon-reload
sudo systemctl enable --now mathlib
curl http://127.0.0.1:8001/healthz/      # бояд {"status": "ok"} диҳад
```

## 6. Nginx ва HTTPS

Аввал сертификат гиред (nginx-и стандартӣ бояд дар порти 80 кор кунад):

```bash
sudo certbot certonly --webroot -w /var/www/html -d your-domain.tj -d www.your-domain.tj
```

Сипас конфигуратсияро гузоред:

```bash
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/mathlib
sudo sed -i 's/your-domain.tj/ДОМЕНИ_ШУМО/g' /etc/nginx/sites-available/mathlib
sudo ln -s /etc/nginx/sites-available/mathlib /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Сайт акнун дар `https://your-domain.tj` кушода мешавад.

## 7. Санҷиш пас аз гузоштан

- [ ] `https://your-domain.tj/` кушода мешавад, `http://` ба `https://` мегузарад
- [ ] `https://your-domain.tj/healthz/` → `{"status": "ok"}`
- [ ] Воридшавӣ ва бақайдгирӣ кор мекунад
- [ ] Китобдор китоб илова мекунад, муқова намоён аст
- [ ] Донишҷӯ китобро зеркашӣ мекунад
- [ ] `https://your-domain.tj/media/books/...` → **404** (файлҳо ҳифз шудаанд)

## 8. Навсозӣ (update)

```bash
cd /var/www/mathlib_bsu_pro
sudo -u postgres pg_dump -Fc mathlib_bsu > ~/backup-$(date +%F).dump   # аввал backup!
sudo -u www-data git pull
sudo -u www-data .venv/bin/pip install -r requirements.txt
sudo -u www-data .venv/bin/python manage.py migrate
sudo -u www-data .venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart mathlib
curl -s http://127.0.0.1:8001/healthz/
```

## 9. Backup (ҳар шаб)

```bash
sudo crontab -e
# Ҳар шаб соати 02:30: database ва media
30 2 * * * sudo -u postgres pg_dump -Fc mathlib_bsu > /var/backups/mathlib-$(date +\%F).dump && tar -czf /var/backups/media-$(date +\%F).tar.gz -C /var/www/mathlib_bsu_pro media
```

Backup-ҳоро ба сервери дигар нусха кунед ва ҳар моҳ барқарорсозиро санҷед.

## 10. Мушкилот

| Аломат | Сабаб / ҳал |
|---|---|
| `502 Bad Gateway` | gunicorn кор намекунад: `sudo journalctl -u mathlib -n 50` |
| Редиректи беохир | дар `.env` `BEHIND_PROXY=True` нест |
| `400 Bad Request` | домен дар `ALLOWED_HOSTS` нест |
| `403 CSRF` ҳангоми ворид | домен бо `https://` дар `CSRF_TRUSTED_ORIGINS` нест |
| CSS кор намекунад | `collectstatic` иҷро нашудааст |
| `413` ҳангоми боркунӣ | `client_max_body_size` дар nginx |
| Барнома оғоз намешавад: `ImproperlyConfigured` | `SECRET_KEY` дар `.env` нест ё кӯтоҳ аст |

Ҳамаи хатогиҳо дар `sudo journalctl -u mathlib -f` навишта мешаванд.
