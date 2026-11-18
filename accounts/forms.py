from django import forms

from .models import Rating


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ["shop", "download", "upload"]
        labels = {
            "download": "Download (Mbps)",
            "upload": "Upload (Mbps)",
        }
