from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from decimal import Decimal # Importation utile pour la précision si besoin plus tard

# =========================================================================
# 1. Structures Académiques (Option, Semestre, UE, Matiere)
# =========================================================================
class SemestreChoix(models.TextChoices):
    semestre1='S1',_('S1')
    semestre2='s2',_('s2')
    semestre3='s3',_('s3')
    semestre4='S4',_('S4')
    semestre5='s5',_('s5')
    semestre6='s6',_('s6')
class Option(models.Model):
    """Représente une filière/option/classe (ex: OIGL L1, Génie Électrique M1)."""
    code_classe = models.CharField(max_length=20, unique=True, verbose_name=_("Code de la Classe")) 
    nom = models.CharField(max_length=40, verbose_name=_("Nom de la Classe"))

    class Meta:
        verbose_name = _("Classe/Option")
        verbose_name_plural = _("Classes/Options")
        
    def __str__(self):
        return self.nom
# noter bien c'est class au lieu de semestre
class Option(models.Model):
    code_option= models.CharField(max_length=10, primary_key=True, verbose_name=_("Code option"))
    nom_option= models.CharField(max_length=20, verbose_name=_("Nom option"))

    class Meta:
        verbose_name = _("Option")
        verbose_name_plural = _("Option")

    def __str__(self):
        return self.nom_option

class UE(models.Model):
    """Représente une Unité d'Enseignement (UE)."""
    code_ue = models.CharField(max_length=20, unique=True, verbose_name=_("Code UE"))
    nom_ue = models.CharField(max_length=50, verbose_name=_("Nom de l'UE"))
    
    # Correction : related_name est explicite
    semestre =models.CharField(max_length=20,choices=SemestreChoix.choices,verbose_name=_('semestre'))

    class Meta:
        verbose_name = _("Unité d'Enseignement")
        verbose_name_plural = _("Unités d'Enseignement")

    def __str__(self):
        return f"{self.code_ue} - {self.nom_ue}"

class Matiere(models.Model):
   
    code_matiere = models.CharField(primary_key=True, max_length=100, verbose_name=_("Code Matière"))
    nom_matiere = models.CharField(max_length=50, verbose_name=_("Nom de la Matière"))
    
    semestre = models.CharField(max_length=20,choices=SemestreChoix.choices ,verbose_name=_('semestre'))
    coef = models.DecimalField(max_digits=4, decimal_places=2, verbose_name=_("Coefficient"))
    
    ue = models.ForeignKey(
        UE, 
        on_delete=models.CASCADE, 
        related_name="matieres_ue", # Changé le related_name pour plus de clarté
        verbose_name=_("Unité d'Enseignement")
    )

    class Meta:
        verbose_name = _("Matières")
        verbose_name_plural = _("Matières")
        
    def __str__(self):
        return f"{self.code_matiere} - {self.nom_matiere}"

# =========================================================================
# 2. Utilisateurs et Profils (Professeur, Etudiant)
# =========================================================================

class DepartChoice(models.TextChoices):
    INFO = 'info', _('Informatique Génie Logiciel')
    ELEC = 'elec', _('Génie Électrique')
    MECA = 'meca', _('Génie Mécanique')

class Professeur(models.Model):
    """Profil étendu de l'utilisateur pour les professeurs."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="professeur", verbose_name=_("Compte Utilisateur"))
    code_prof = models.CharField(max_length=20, unique=True, verbose_name=_("Code du Professeur"))
    
    # Correction : related_name pour éviter les conflits et clarifier
    matiere_principale = models.ForeignKey(
        Matiere, 
        on_delete=models.SET_NULL, # Mieux de mettre NULL si la matière est supprimée
        null=True, 
        blank=True, 
        related_name='professeurs_principaux',
        verbose_name=_("Matière d'enseignement principale")
    )
    
    class Meta:
        verbose_name = _("Professeur")
        verbose_name_plural = _("Professeurs")
        
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.code_prof})"

    def get_absolute_url(self):
        return reverse('professeur_list')

class Etudiant(models.Model):
    """Profil étendu de l'utilisateur pour les étudiants."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="etudiant", verbose_name=_("Compte Utilisateur"))
    matricule = models.CharField(max_length=20, unique=True, verbose_name=_("Matricule"))
    
    # Correction: 'classe' est un terme plus courant, mais j'utilise 'option_classe' pour éviter les conflits.
    option_classe = models.ForeignKey(
        Option, 
        on_delete=models.CASCADE, 
        related_name="etudiants",
        verbose_name=_("Option/Classe de l'étudiant")
    )
    departement = models.CharField(
        max_length=50, 
        choices=DepartChoice.choices,
        default=DepartChoice.INFO,
        verbose_name=_("Département")
    )

    class Meta:
        verbose_name = _("Étudiant")
        verbose_name_plural = _("Étudiants")

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.matricule})"

    def get_absolute_url(self):
        return reverse('etudiant_list')

# =========================================================================
# 3. Emploi du Temps
# =========================================================================

class JourChoices(models.TextChoices):
    LUNDI = 'Lundi', _('Lundi')
    MARDI = 'Mardi', _('Mardi')
    MERCREDI = 'Mercredi', _('Mercredi')
    JEUDI = 'Jeudi', _('Jeudi')
    VENDREDI = 'Vendredi', _('Vendredi')
    SAMEDI = 'Samedi', _('Samedi')
    DIMANCHE = 'Dimanche', _('Dimanche')

class Emploi(models.Model):
    """Représente une séance de cours dans l'emploi du temps."""
    id_seance = models.CharField(unique=True, max_length=10, verbose_name=_("ID Séance"))
    heure_debut = models.TimeField(verbose_name=_("Heure Début"))
    heure_fin = models.TimeField(verbose_name=_("Heure Fin"))
    date_seance = models.DateField(verbose_name=_("Date de la Séance")) 
    jour_nom = models.CharField(max_length=10, choices=JourChoices.choices, verbose_name=_("Jour"))

    # Correction 1 : Utilisation cohérente des noms
    option_classe = models.ForeignKey(
        Option, 
        on_delete=models.CASCADE, 
        related_name="seances_classe", # Related name plus clair
        verbose_name=_("Option")
    )
    
    # Correction 2 : Renommé 'user' en 'professeur' pour la clarté de la FK
    professeur = models.ForeignKey(
        Professeur, 
        on_delete=models.CASCADE, 
        related_name="seances_professeur", # Related name plus clair
        verbose_name=_("Professeur")
    )
    
    # Correction 3 : Renommé 'nom_matiere' en 'matiere' (l'objet FK)
    matiere = models.ForeignKey(
        Matiere, 
        on_delete=models.CASCADE, 
        related_name="seances_matiere", # Related name plus clair
        verbose_name=_("Matière Enseignée")
    )

    class Meta:
        verbose_name = _("Emploi du Temps")
        verbose_name_plural = _("Emplois du Temps")

    def __str__(self):
        return f"Séance {self.id_seance}: {self.matiere} ({self.classe}) - {self.jour_nom}"

# =========================================================================
# 4. Notes et Résultats
# =========================================================================

class Note(models.Model):
    """Enregistre les notes d'un étudiant pour une matière, avec les coefficients de pondération."""
    etudiant = models.ForeignKey(
        Etudiant, 
        on_delete=models.CASCADE, 
        related_name="notes",
        verbose_name=_("Étudiant")
    )
    matiere = models.ForeignKey(
        Matiere, 
        on_delete=models.CASCADE, 
        related_name='notes',
        verbose_name=_("Matière")
    )
    
    # Correction: Ajout de note_td et coef_td que j'ai vu utilisés dans la vue
    note_cm = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name=_("Note CM"))
    coef_cm = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('1.0'), verbose_name=_("Coef CM"))
    
    note_td = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name=_("Note TD"))
    coef_td = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('1.0'), verbose_name=_("Coef TD")) # Supposé exister
    
    note_tp = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name=_("Note TP"))
    coef_tp = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('1.0'), verbose_name=_("Coef TP"))
    
    class Meta:
        # Assure qu'un étudiant n'a qu'une seule entrée de note par matière
        unique_together = ('etudiant', 'matiere') 
        verbose_name = _("Note")
        verbose_name_plural = _("Notes")
        
    def __str__(self):
        return f"Notes de {self.etudiant.user.last_name} en {self.matiere.nom_matiere}"
    
    def get_absolute_url(self):
        # Pourrait renvoyer vers le bulletin de l'étudiant
        return reverse('bulletin_de_notes', kwargs={'etudiant_pk': self.etudiant.pk})