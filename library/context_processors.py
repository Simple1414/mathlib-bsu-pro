
SITE_TEXTS = {
    'tg': {
        'home': 'Асосӣ', 'books': 'Китобҳо', 'articles': 'Мақолаҳо',
        'about': 'Дар бораи сомона', 'contact': 'Тамос', 'login': 'Воридшавӣ',
        'register': 'Бақайдгирӣ', 'dashboard': 'Панел', 'profile': 'Профил', 'logout': 'Баромад',
        'library_title': 'Китобхонаи электронии факултет',
    },
    'ru': {
        'home': 'Главная', 'books': 'Книги', 'articles': 'Статьи',
        'about': 'О сайте', 'contact': 'Контакты', 'login': 'Войти',
        'register': 'Регистрация', 'dashboard': 'Панель', 'profile': 'Профиль', 'logout': 'Выйти',
        'library_title': 'Электронная библиотека факультета',
    },
    'en': {
        'home': 'Home', 'books': 'Books', 'articles': 'Articles',
        'about': 'About', 'contact': 'Contact', 'login': 'Login',
        'register': 'Register', 'dashboard': 'Dashboard', 'profile': 'Profile', 'logout': 'Logout',
        'library_title': 'Faculty Electronic Library',
    },
}


def site_context(request):
    code = request.session.get('site_language', 'tg')
    if code not in SITE_TEXTS:
        code = 'tg'
    return {
        'site_language': code,
        'ui': SITE_TEXTS[code],
        'available_languages': [('tg', 'Тоҷикӣ'), ('ru', 'Русский'), ('en', 'English')],
    }
