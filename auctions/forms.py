from django import forms
from .models import Listing, Comment

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'description', 'starting_bid', 'image_url', 'category']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

class BidForm(forms.Form):
    bid_amount = forms.DecimalField(
        label="Bid Amount",
        min_value=0.01,  # Adjust the minimum value as needed
        required=True,
        widget=forms.NumberInput(attrs={'step': 0.01}),  # This allows decimal values
    )