from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.db import transaction # Pour gérer la transaction User/Profil
from decimal import Decimal

# Importation de tous les modèles
from .models import (
    Etudiant, Matiere, Note,UE, 
    Professeur, Emploi, Option, DepartChoice, JourChoices
)

User = get_user_model()

# =========================================================================
# 1. FORMULAIRES ACADÉMIQUES SIMPLES (Gérés par View AJAX)
# Ces formulaires n'ont pas besoin de save() ou init() surchargé
# =========================================================================


class SemestreForm(forms.ModelForm):
    """Formulaire pour le modèle Semestre."""
    class Meta:
        model = Option
        fields = ['code_option', 'nom_option']

class UEForm(forms.ModelForm):
    """Formulaire pour le modèle UE."""
    class Meta:
        model = UE
        fields = ['code_ue', 'nom_ue', 'semestre']

class MatiereForm(forms.ModelForm):
    """Formulaire pour le modèle Matiere."""
    class Meta:
        model = Matiere
        fields = ['code_matiere', 'nom_matiere', 'semestre', 'coef', 'ue']
        
class EmploiForm(forms.ModelForm):
    """Formulaire pour le modèle Emploi du Temps."""
    # Utilisation du nom de champ 'classe' si vous avez appliqué la correction du models.py
   # classe = forms.ModelChoiceField(queryset=Option.objects.all(), label="Classe concernée")
    jour_nom = forms.ChoiceField(choices=JourChoices.choices, label="Jour de la semaine")
    
    class Meta:
        model = Emploi
        # Champs corrigés
        fields = ['id_seance', 'date_seance', 'heure_debut', 'heure_fin', 
                  'jour_nom', 'option_classe', 'professeur', 'matiere']
        widgets = {
            'date_seance': forms.DateInput(attrs={'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'type': 'time'}),
        }

# =========================================================================
# 2. FORMULAIRES COMPLEXES (Etudiant, Professeur) - Nécessitent save() surchargé
# =========================================================================

class EtudiantForm(forms.ModelForm):
    """Gère la création/modification de l'Etudiant et de l'objet User lié."""
    
    # 1. Champs pour l'objet User
    first_name = forms.CharField(label="Prénom", max_length=100)
    last_name = forms.CharField(label="Nom", max_length=100)
    email = forms.EmailField(label="Email")
    password = forms.CharField(
        label='Mot de passe ', 
        widget=forms.PasswordInput(render_value=False), 
        required=False
    )

    class Meta:
        model = Etudiant
        # J'utilise 'option_classe' comme dans ma dernière correction de models.py
        fields = ['matricule', 'option_classe', 'departement']
        
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Pré-remplir les champs User en modification
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            # Masquer le champ password en modification
            del self.fields['password'] 

    @transaction.atomic # Assure que les deux objets (User et Etudiant) sont sauvegardés ou rien ne l'est
    def save(self, commit=True):
        etudiant = super().save(commit=False)
        
        # 1. Récupération ou Création de l'objet User
        if etudiant.pk:
            user = etudiant.user
        else:
            username = self.cleaned_data['matricule']
            user, created = User.objects.get_or_create(username=username)

        # 2. Mise à jour des champs de l'utilisateur
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        # 3. Gestion du mot de passe
        password = self.cleaned_data.get('password')
        if password:
             user.set_password(password)
        elif not user.pk: # Si c'est une création sans mot de passe
             user.set_unusable_password() 

        # 4. Sauvegarde finale
        if commit:
            user.save()
            etudiant.user = user  
            etudiant.save()
            
        return etudiant

class ProfesseurForm(forms.ModelForm):
    """Gère la création/modification du Professeur et de l'objet User lié."""
    
    # 1. Champs pour l'objet User
    first_name = forms.CharField(label="Prénom", max_length=100)
    last_name = forms.CharField(label="Nom", max_length=100)
    email = forms.EmailField(label="Email") 
    password = forms.CharField(
        label='Mot de passe (Laisser vide pour modification)', 
        widget=forms.PasswordInput(render_value=False), 
        required=False
    )
    
    class Meta:
        model = Professeur
        fields = ['code_prof', 'matiere_principale']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Pré-remplir les champs User en modification
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            # Masquer le champ password en modification
            del self.fields['password']
            
    @transaction.atomic
    def save(self, commit=True):
        professeur = super().save(commit=False)
        
        # 1. Récupération ou Création de l'objet User
        if professeur.pk:
            user = professeur.user
        else:
            username = self.cleaned_data['code_prof']
            user, created = User.objects.get_or_create(username=username)

        # 2. Mise à jour des champs de l'utilisateur
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        # 3. Gestion du mot de passe
        password = self.cleaned_data.get('password')
        if password:
             user.set_password(password)
        elif not user.pk:
             user.set_unusable_password()

        # 4. Sauvegarde finale
        if commit:
            user.save()
            professeur.user = user  
            professeur.save()
            
        return professeur

# =========================================================================
# 3. AUTRES FORMULAIRES
# =========================================================================

class NoteForm(forms.ModelForm):
    """Formulaire pour les Notes (avec tous les champs nécessaires pour le calcul)."""
    
    # Ajout des champs coefficients (note/coef TD) qui ne sont pas dans les ModelForm par défaut
    note_td = forms.DecimalField(label="Note TD", max_digits=4, decimal_places=2, required=False)
    coef_cm = forms.DecimalField(label="Coef CM", max_digits=4, decimal_places=2, initial=Decimal('1.0'), required=False)
    coef_td = forms.DecimalField(label="Coef TD", max_digits=4, decimal_places=2, initial=Decimal('1.0'), required=False)
    coef_tp = forms.DecimalField(label="Coef TP", max_digits=4, decimal_places=2, initial=Decimal('1.0'), required=False)
    
    class Meta:
        model = Note
        fields = [
            'etudiant', 'matiere', 
            'note_cm', 'coef_cm', 
            'note_td', 'coef_td', 
            'note_tp', 'coef_tp'
        ] 
        widgets = {
             'etudiant': forms.Select(attrs={'class': 'form-control'}),
             'matiere': forms.Select(attrs={'class': 'form-control'}),
             'note_cm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
             'note_td': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
             'note_tp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
             'coef_cm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
             'coef_td': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
             'coef_tp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class CustomUserCreationForm(UserCreationForm):
    # Ajoutez un champ email pour être professionnel
    email = forms.EmailField(
        label="Adresse e-mail", 
        max_length=254, 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemple@universite.com'})
    )
    
    # Correction : Utiliser __init__ pour ajouter la classe aux autres champs (username, password, etc.)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Parcourir et ajouter la classe 'form-control' aux champs restants
        for field_name, field in self.fields.items():
            # Nous stylisons déjà l'email ci-dessus, mais c'est une sécurité
            if field_name not in ['email']: 
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': field.label 
                })

    class Meta(UserCreationForm.Meta):
        # Si vous utilisez le modèle User par défaut, cela reste inchangé
        # Si vous avez un champ 'matricule' ou autre, ajoutez-le ici
        fields = ('username', 'email') + UserCreationForm.Meta.fields[2:] # Afficher email en plus du username
        # Si vous voulez l'email et le username:
        # fields = UserCreationForm.Meta.fields + ('email',)