from django import forms
class PlaylistForm(forms.Form):
    name = forms.Field()

class RecommendationForm(forms.Form):
    name = forms.Field()