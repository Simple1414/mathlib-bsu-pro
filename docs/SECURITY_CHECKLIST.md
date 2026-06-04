# Security Checklist — MathLib BSU Pro

## Пеш аз production

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` иваз шуд
- [ ] `ALLOWED_HOSTS` дуруст аст
- [ ] HTTPS фаъол аст
- [ ] `SECURE_SSL_REDIRECT=True`
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] `CSRF_COOKIE_SECURE=True`
- [ ] PostgreSQL user танҳо permission-и лозимаро дорад
- [ ] Backup-и database фаъол аст
- [ ] Upload танҳо PDF/DOC/DOCX иҷозат медиҳад
- [ ] Ҳаҷми файл маҳдуд аст
- [ ] Китобҳои пешниҳодшуда тасдиқро талаб мекунанд
- [ ] Нақшҳоро танҳо админ тағйир медиҳад
- [ ] Admin URL дар production ҳифз мешавад
- [ ] `python manage.py check --deploy` иҷро шуд

## Хатарҳои асосӣ

1. Боркунии файлҳои зараровар
2. Додани нақши баланд ба корбари нодуруст
3. Фош шудани `.env`
4. Набудани backup
5. DEBUG=True дар сервер
6. Permission-и нодурусти media files

## Қоидаи сахт

Система бе SSL, backup ва `DEBUG=False` набояд ба истифодаи расмии факултет дода шавад.
