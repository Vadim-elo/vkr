from django import forms

GEEKS_CHOICES =(
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
)

class UserForm(forms.Form):
    id = forms.CharField(label="peoplemain_id")
    levels = forms.ChoiceField(choices = GEEKS_CHOICES)
    check_phone = forms.BooleanField(label = "phone", initial='on',required=False)
    check_card = forms.BooleanField(label="card", initial='on',required=False)
    check_ip = forms.BooleanField(label="ip", initial='on',required=False)
    check_email = forms.BooleanField(label="email", initial='on', required=False)