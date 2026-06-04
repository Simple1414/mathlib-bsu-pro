from django import forms
from .models import Author, Book, BookRequest, Category


class BookForm(forms.ModelForm):
    new_authors = forms.CharField(
        required=False,
        label='Муаллифони нав',
        help_text='Агар муаллиф дар рӯйхат нест, ин ҷо нависед. Барои чанд муаллиф бо вергул ҷудо кунед.'
    )

    class Meta:
        model = Book
        fields = [
            'title', 'authors', 'new_authors', 'category', 'description', 'publication_year',
            'language', 'subject', 'keywords', 'cover', 'file', 'is_download_allowed'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'authors': forms.SelectMultiple(attrs={'size': 7}),
        }

    def save(self, commit=True, uploaded_by=None, auto_approve=False):
        book = super().save(commit=False)
        if uploaded_by:
            book.uploaded_by = uploaded_by
        if auto_approve:
            book.is_approved = True
        if commit:
            book.save()
            self.save_m2m()
            raw = self.cleaned_data.get('new_authors', '')
            for name in [x.strip() for x in raw.split(',') if x.strip()]:
                author, _ = Author.objects.get_or_create(full_name=name)
                book.authors.add(author)
        return book


class BookRequestForm(forms.ModelForm):
    class Meta:
        model = BookRequest
        fields = ['title', 'author', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 4}),
        }


class BookSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Ҷустуҷӯ')
    category = forms.ModelChoiceField(required=False, queryset=Category.objects.all(), label='Категория')
    language = forms.ChoiceField(required=False, choices=[('', 'Ҳамаи забонҳо')] + list(Book.Language.choices), label='Забон')
