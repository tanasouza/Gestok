from django import forms
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()


class UserAddressFormMixin(forms.ModelForm):
    cep = forms.CharField(
        required=False,
        max_length=9,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '00000-000',
            'inputmode': 'numeric',
            'autocomplete': 'postal-code',
        }),
    )
    rua = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome da rua',
            'autocomplete': 'address-line1',
        }),
    )
    setor = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Setor ou bairro',
            'autocomplete': 'address-level3',
        }),
    )
    numero = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número',
            'inputmode': 'numeric',
            'autocomplete': 'address-line2',
        }),
    )
    sem_numero = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    address_prefixes = {
        'CEP': 'cep',
        'Rua': 'rua',
        'Setor': 'setor',
        'Número': 'numero',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound or not getattr(self.instance, 'endereco', None):
            return

        address = self.instance.endereco.strip()
        parsed = {}
        for part in address.split(' | '):
            if ': ' not in part:
                continue
            label, value = part.split(': ', 1)
            field_name = self.address_prefixes.get(label)
            if field_name:
                parsed[field_name] = value

        if parsed:
            self.initial.update(parsed)
            self.initial['sem_numero'] = parsed.get('numero') == 'S/N'
            if self.initial['sem_numero']:
                self.initial['numero'] = ''
        else:
            # Legacy free-text addresses remain editable as the street name.
            self.initial['rua'] = address

    def clean(self):
        cleaned_data = super().clean()
        cep = (cleaned_data.get('cep') or '').strip()
        rua = (cleaned_data.get('rua') or '').strip()
        setor = (cleaned_data.get('setor') or '').strip()
        numero = (cleaned_data.get('numero') or '').strip()
        sem_numero = cleaned_data.get('sem_numero', False)

        if cep:
            digits = ''.join(character for character in cep if character.isdigit())
            if len(digits) != 8:
                self.add_error('cep', 'Informe um CEP com 8 dígitos.')
            else:
                cleaned_data['cep'] = f'{digits[:5]}-{digits[5:]}'

        if sem_numero:
            cleaned_data['numero'] = ''
        elif any((cep, rua, setor)) and not numero:
            self.add_error('numero', 'Informe o número ou marque a opção "Sem número".')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        parts = []
        for label, field_name in self.address_prefixes.items():
            if field_name == 'numero' and self.cleaned_data.get('sem_numero'):
                value = 'S/N'
            else:
                value = (self.cleaned_data.get(field_name) or '').strip()
            if value:
                parts.append(f'{label}: {value}')

        user.endereco = ' | '.join(parts) or None
        if commit:
            user.save()
            self.save_m2m()
        return user


class LoginForm(forms.Form):
    """
    Form for logging in users via matricula.
    """
    matricula = forms.CharField(
        label="Matrícula",
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite sua matrícula',
            'class': 'form-control',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Digite sua senha',
            'class': 'form-control'
        })
    )

class UserCreateForm(UserAddressFormMixin):
    """
    Form for creating new users.
    Only administrator can fill this form.
    It does not contain password or matricula, since they are generated automatically.
    """
    class Meta:
        model = User
        fields = ['nome_completo', 'email', 'telefone', 'cargo']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'cargo': forms.Select(attrs={'class': 'form-select'}),
        }

class UserEditForm(UserAddressFormMixin):
    """
    Form for editing user details.
    """
    class Meta:
        model = User
        fields = ['nome_completo', 'email', 'telefone', 'cargo', 'ativo']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'cargo': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class FirstAccessForm(forms.Form):
    """
    Form for the mandatory password change on the first access.
    """
    new_password = forms.CharField(
        label="Nova Senha",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 6 caracteres',
            'id': 'id_new_password'
        })
    )
    confirm_password = forms.CharField(
        label="Confirmar Senha",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repita a nova senha'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password:
            if new_password != confirm_password:
                self.add_error('confirm_password', "As senhas não coincidem.")
            if len(new_password) < 6:
                self.add_error('new_password', "A senha deve ter no mínimo 6 caracteres.")
        return cleaned_data
