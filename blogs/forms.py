from django import forms
from .models import Blog, Category, Tag


class BlogForm(forms.ModelForm):
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter tags separated by commas',
            'id': 'tags-input'
        }),
        help_text='Separate tags with commas'
    )

    allow_comments = forms.BooleanField(
        required=False, 
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Blog
        fields = [
            'title', 'category', 'content', 'excerpt',
            'featured_image', 'allow_comments',
            'meta_title', 'meta_description'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter a compelling blog title...'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Brief description of your blog (shown in listings)...'
            }),
            'content': forms.Textarea(attrs={'class': 'form-control', 'id': 'blog-content'}),
            'featured_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'id': 'imageInput'}),
            'allow_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO Title (max 70 chars)', 'maxlength': '70'}),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'SEO Description (max 160 chars)', 'maxlength': '160'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].empty_label = 'Select Category'
        if self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(
                self.instance.tags.values_list('name', flat=True)
            )

    def save(self, commit=True):
        blog = super().save(commit=False)
        original_save_m2m = self.save_m2m if hasattr(self, 'save_m2m') else lambda: None

        def save_m2m_with_tags():
            original_save_m2m()
            tags_raw = self.cleaned_data.get('tags_input', '')
            tag_names = [t.strip().lower() for t in tags_raw.split(',') if t.strip()]
            tag_objs = []
            for name in tag_names:
                if name:
                    tag, _ = Tag.objects.get_or_create(name=name)
                    tag_objs.append(tag)
            blog.tags.set(tag_objs)

        if commit:
            blog.save()
            save_m2m_with_tags()
        else:
            self.save_m2m = save_m2m_with_tags

        return blog
