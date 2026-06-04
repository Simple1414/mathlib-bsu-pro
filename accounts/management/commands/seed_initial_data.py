from django.core.management.base import BaseCommand
from accounts.models import Faculty, Specialty, University
from library.models import Category, Author


class Command(BaseCommand):
    help = 'Маълумоти аввалияро барои MathLib BSU месозад.'

    def handle(self, *args, **options):
        university, _ = University.objects.get_or_create(
            name='Донишгоҳи давлатии Бохтар ба номи Носири Хусрав'
        )
        faculty, _ = Faculty.objects.get_or_create(
            university=university,
            name='Факултети математика'
        )
        specialties = [
            ('Математика-информатика', '1-31 03 01-02'),
            ('Математика', '1-31 03 01'),
            ('Информатика', '1-40 01 01'),
        ]
        for name, code in specialties:
            Specialty.objects.get_or_create(faculty=faculty, name=name, defaults={'code': code})

        for category in ['Математика', 'Информатика', 'Барномасозӣ', 'Зеҳни сунъӣ', 'Таҳлили математикӣ', 'Алгебра', 'Геометрия', 'Методикаи таълим']:
            Category.objects.get_or_create(name=category)

        for author in ['Носири Хусрав', 'Леонард Эйлер', 'Исаак Нютон', 'Алан Тюринг']:
            Author.objects.get_or_create(full_name=author)

        self.stdout.write(self.style.SUCCESS('Маълумоти аввалия бомуваффақият сохта шуд.'))
