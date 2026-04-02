from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from decimal import Decimal
import datetime 
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator


from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required

# Importez vos modèles
from .models import Etudiant, Matiere, Note, UE, Professeur, Emploi, Option


from .forms import (
    EtudiantForm, NoteForm, SemestreForm, MatiereForm, UEForm, 
    ProfesseurForm, EmploiForm, CustomUserCreationForm
)



def is_enseignant(user):
    """Vérifie si l'utilisateur est enseignant ou superuser"""
    return user.groups.filter(name='Enseignants').exists() or user.is_superuser

def is_etudiant(user):
  
    return user.groups.filter(name='Etudiants').exists() or user.is_superuser

class EnseignantRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès aux enseignants et superusers"""
    def test_func(self):
        return is_enseignant(self.request.user)

class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès UNIQUEMENT aux superusers (Admin)"""
    def test_func(self):
        return self.request.user.is_superuser # 👈 NOUVEAU MIXIN

class EtudiantRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès aux utilisateurs connectés (avec possibilité de filtrer)"""
    def test_func(self):
        return self.request.user.is_authenticated

# =========================================================================
# Vues Publiques (Accessibles à tous)
# =========================================================================

def home_view(request):
    """Affiche la page d'accueil."""
    return render(request, 'home.html')

@login_required
def dashboard_view(request):
    """Affiche la page du tableau de bord. Protégé par login."""
    return render(request, 'dashboard.html', {
        'is_enseignant': is_enseignant(request.user),
        'is_etudiant': is_etudiant(request.user)
    })

def register(request):
    """Inscription."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login') 
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

# =========================================================================
# LOGIQUE AJAX GÉNÉRIQUE
# =========================================================================

def handle_ajax_form(self, form, success_fields_map, success_message=None):
    is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if form.is_valid():
        self.object = form.save()
        if is_ajax:
            response_data = {'success': True, 'pk': self.object.pk}
            for field, getter in success_fields_map.items():
                try:
                    response_data[field] = getter(self.object) if callable(getter) else getter
                except Exception:
                    response_data[field] = "Erreur de sérialisation"
            
            if success_message:
                response_data['message'] = success_message
            return JsonResponse(response_data)
        else:
            return super(self.__class__, self).form_valid(form)
    else:
        if is_ajax:
            context = self.get_context_data(form=form)
            return render(self.request, self.template_name, context, status=400) 
        else:
            return super(self.__class__, self).form_invalid(form)

# =========================================================================
# 2. VUES CRUD POUR ETUDIANT (Création/Modif/Suppression réservées à l'ADMIN)
# =========================================================================

# Tout le monde connecté peut voir la liste des étudiants
class EtudiantListView(LoginRequiredMixin, ListView):
    model = Etudiant 
    template_name = 'etudiant_list.html'
    context_object_name = 'etudiants'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'option_classe') 
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(user__last_name__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(matricule__icontains=query)
            ).distinct()
        return queryset

# SEUL LE SUPERUSER peut créer/modifier des étudiants
class EtudiantCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView): # 👈 CHANGEMENT
    model = Etudiant
    form_class = EtudiantForm
    template_name = 'etudiant_form.html'
    
    def form_valid(self, form):
        success_fields = {
            'matricule': lambda obj: obj.matricule,
            'last_name': lambda obj: obj.user.last_name,
            'first_name': lambda obj: obj.user.first_name,
            'email': lambda obj: obj.user.email,
            'option_classe': lambda obj: str(obj.option_classe) if obj.option_classe else 'N/A', 
            'departement': lambda obj: obj.get_departement_display()
        }
        return handle_ajax_form(self, form, success_fields, success_message="Étudiant créé avec succès.")

class EtudiantUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView): # 👈 CHANGEMENT
    model = Etudiant
    form_class = EtudiantForm
    template_name = 'etudiant_form.html'
    success_url = reverse_lazy('etudiant_list')

class EtudiantDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView): # 👈 CHANGEMENT
    model = Etudiant
    template_name = 'etudiant_confirm_delete.html'
    success_url = reverse_lazy('etudiant_list')

@login_required
def etudiant_detail(request, pk):
    # Un étudiant peut voir son propre profil, un prof peut voir tout le monde
    etudiant = get_object_or_404(Etudiant.objects.select_related('user', 'option_classe'), pk=pk)
    
    # Sécurité : Si je suis étudiant et que ce n'est pas MOI, je rejette
    if is_etudiant(request.user) and not is_enseignant(request.user):
        if hasattr(request.user, 'etudiant') and request.user.etudiant.pk != pk:
             return HttpResponseForbidden("Vous ne pouvez pas voir le profil d'un autre étudiant.")

    return render(request, 'etudiant_detail.html', {'etudiant': etudiant})


# =========================================================================
# 3. VUES CRUD POUR PROFESSEUR (Création/Modif/Suppression réservées à l'ADMIN)
# =========================================================================

# Tout le monde connecté peut voir les profs
class ProfesseurListView(LoginRequiredMixin, ListView):
    model = Professeur
    template_name = 'professeur_list.html'
    context_object_name = 'professeurs'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'matiere_principale')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(user__last_name__icontains=query) | 
                Q(user__first_name__icontains=query) | 
                Q(user__email__icontains=query)
            ).distinct()
        return queryset

# SEUL UN SUPERUSER peut ajouter/supprimer des profs
class ProfesseurCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView): # 👈 CHANGEMENT
    model = Professeur
    form_class = ProfesseurForm
    template_name = 'professeur_form.html'
    
    def form_valid(self, form):
        success_fields = {
            'code_prof': lambda obj: obj.code_prof,
            'last_name': lambda obj: obj.user.last_name,
            'first_name': lambda obj: obj.user.first_name,
            'email': lambda obj: obj.user.email,
            'matiere_principale': lambda obj: str(obj.matiere_principale) if obj.matiere_principale else 'N/A',
        }
        return handle_ajax_form(self, form, success_fields, success_message="Professeur créé avec succès.")

class ProfesseurUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView): # 👈 CHANGEMENT
    model = Professeur
    form_class = ProfesseurForm
    template_name = 'professeur_form.html'
    success_url = reverse_lazy('professeur_list')

class ProfesseurDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView): # 👈 CHANGEMENT
    model = Professeur
    template_name = 'professeur_confirm_delete.html'
    success_url = reverse_lazy('professeur_list')


# =========================================================================
# 4. VUES CRUD POUR EMPLOI DU TEMPS (Création/Modif/Suppression réservées à l'ADMIN)
# =========================================================================

# Tout le monde peut voir l'emploi du temps
class EmploiListView(LoginRequiredMixin, ListView):
    model = Emploi
    template_name = 'emploi_list.html'
    context_object_name = 'emplois'
    
    def get_queryset(self):
        queryset = super().get_queryset() 
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter( 
                Q(option_classe__nom_option__icontains=query) | 
                Q(date_seance__icontains=query)
            ).distinct()
        return queryset

# SEUL ADMIN peut modifier l'emploi du temps
class EmploiCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView): # 👈 CHANGEMENT
    model = Emploi
    form_class = EmploiForm
    template_name = 'emploi_form.html'
    
    def form_valid(self, form):
        success_fields = {
            'id_seance': lambda obj: obj.id_seance,
            'heure_debut': lambda obj: obj.heure_debut.strftime('%H:%M'),
            'heure_fin': lambda obj: obj.heure_fin.strftime('%H:%M'),
            'date_seance': lambda obj: obj.date_seance.strftime('%Y-%m-%d'),
            'jour_nom': lambda obj: obj.jour_nom,
            'option_classe': lambda obj: str(obj.option_classe),
            'professeur': lambda obj: str(obj.professeur),
            'matiere': lambda obj: str(obj.matiere),
            'professeur_nom': lambda obj: f"{obj.professeur.user.first_name} {obj.professeur.user.last_name}",
            'nom_matiere': lambda obj: obj.matiere.nom_matiere,
            'update_url': lambda obj: reverse('emploi_update', kwargs={'pk': obj.pk}),
            'delete_url': lambda obj: reverse('emploi_delete', kwargs={'pk': obj.pk}),
        }
        return handle_ajax_form(self, form, success_fields, success_message="Séance créée avec succès.")

class EmploiUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView): # 👈 CHANGEMENT
    model = Emploi
    form_class = EmploiForm
    template_name = 'emploi_form.html'
    success_url = reverse_lazy('emploi_list')

class EmploiDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView): # 👈 CHANGEMENT
    model = Emploi
    template_name = 'emploi_confirm_delete.html'
    success_url = reverse_lazy('emploi_list')


# =========================================================================
# 5. VUES CRUD GÉNÉRIQUES (Option, UE, Matiere) - Création/Modif/Suppression réservées à l'ADMIN
# =========================================================================

# --- Option (Semestre) ---

class SemestreListView(LoginRequiredMixin, ListView):
    model = Option
    template_name = 'semestre_list.html'
    context_object_name = 'semestres'

class SemestreCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView): # 👈 CHANGEMENT
    model = Option
    form_class = SemestreForm
    template_name = 'semestre_form.html'
    
    def form_valid(self, form):
        success_fields = {
            'code_option': lambda obj: obj.code_option,
            'nom_option': lambda obj: obj.nom_option,
        }
        return handle_ajax_form(self, form, success_fields, success_message="Option créé avec succès.")

class SemestreUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView): # 👈 CHANGEMENT
    model = Option
    form_class = SemestreForm
    template_name = 'semestre_form.html'
    success_url = reverse_lazy('semestre_list')

class SemestreDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView): # 👈 CHANGEMENT
    model = Option
    template_name = 'semestre_confirm_delete.html'
    success_url = reverse_lazy('semestre_list')

# --- MATIERE ---

class MatiereListView(LoginRequiredMixin, ListView):
    model = Matiere
    template_name = 'matiere_list.html'
    context_object_name = 'matieres'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(code_matiere__icontains=query) | Q(nom_matiere__icontains=query)
            ).distinct()
        return queryset

class MatiereCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView): # 👈 CHANGEMENT
    model = Matiere
    form_class = MatiereForm
    template_name = 'matiere_form.html'
    
    def form_valid(self, form):
        success_fields = {
            'code_matiere': lambda obj: obj.code_matiere,
            'nom_matiere': lambda obj: obj.nom_matiere,
            'semestre': lambda obj: str(obj.semestre),
            'coef': lambda obj: str(obj.coef),
            'ue': lambda obj: str(obj.ue),
        }
        return handle_ajax_form(self, form, success_fields, success_message="Matière créée avec succès.")

class MatiereUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView): # 👈 CHANGEMENT
    model = Matiere
    form_class = MatiereForm
    template_name = 'matiere_form.html'
    success_url = reverse_lazy('matiere_list')

class MatiereDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView): # 👈 CHANGEMENT
    model = Matiere
    template_name = 'matiere_confirm_delete.html'
    success_url = reverse_lazy('matiere_list')

# --- UE ---

class UEListView(LoginRequiredMixin, ListView):
    model = UE
    template_name = 'ue_list.html'
    context_object_name = 'ues'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(code_ue__icontains=query) | Q(nom_ue__icontains=query)
            ).distinct()
        return queryset
    
class UECreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView): # 👈 CHANGEMENT
    model = UE
    form_class = UEForm
    template_name = 'ue_form.html'
    
    def form_valid(self, form):
        success_fields = {
            'code_ue': lambda obj: obj.code_ue,
            'nom_ue': lambda obj: obj.nom_ue,
            'semestre': lambda obj: str(obj.semestre),
        }
        return handle_ajax_form(self, form, success_fields, success_message="UE créée avec succès.")

class UEUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView): # 👈 CHANGEMENT
    model = UE
    form_class = UEForm
    template_name = 'ue_form.html'
    success_url = reverse_lazy('ue_list')

class UEDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView): # 👈 CHANGEMENT
    model = UE
    template_name = 'ue_confirm_delete.html'
    success_url = reverse_lazy('ue_list')


# =========================================================================
# 6. LOGIQUE DES NOTES ET BULLETIN (Reste réservé aux ENSEIGNANTS)
# =========================================================================

# SEUL ENSEIGNANT peut saisir une note
class NoteCreateView(LoginRequiredMixin, EnseignantRequiredMixin, CreateView):
    model = Note
    form_class = NoteForm
    template_name = 'note_form.html'
    
    def form_valid(self, form):
        obj = form.instance
        type_saisi = 'N/A'
        valeur_saisie = 'N/A'
        coef_saisi = 'N/A'
        
        if obj.note_cm is not None:
            type_saisi = 'Cours Magistral (CM)'
            valeur_saisie = str(obj.note_cm)
            coef_saisi = str(obj.coef_cm)
        elif obj.note_td is not None:
            type_saisi = 'Travaux Dirigés (TD)'
            valeur_saisie = str(obj.note_td)
            coef_saisi = str(obj.coef_td)
        elif obj.note_tp is not None:
            type_saisi = 'Travaux Pratiques (TP)'
            valeur_saisie = str(obj.note_tp)
            coef_saisi = str(obj.coef_tp)

        success_fields = {
            'pk': obj.pk,
            'id_note': obj.pk, 
            'etudiant_nom_complet': lambda obj: str(obj.etudiant),
            'nom_matiere': lambda obj: str(obj.matiere),
            'type_note_display': type_saisi,
            'valeur_note': valeur_saisie,
            'coef': coef_saisi,
            'update_url': lambda obj: reverse('note_update', kwargs={'pk': obj.pk}),
            'delete_url': lambda obj: reverse('note_delete', kwargs={'pk': obj.pk}),
            }
        return handle_ajax_form(self, form, success_fields, success_message="Note enregistrée avec succès.")


class NoteListView(LoginRequiredMixin, ListView):
    """
    Vue INTELLIGENTE :
    - Si l'utilisateur est un étudiant : il voit directement SES notes.
    - Si l'utilisateur est enseignant/admin : il voit le formulaire de recherche par matricule.
    """
    model = Note
    template_name = 'notes_list.html'
    context_object_name = 'note'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # CAS 1 : C'est un étudiant (mais pas un prof/admin) -> IL VOIT SES NOTES
        if is_etudiant(user) and not is_enseignant(user):
            if hasattr(user, 'etudiant'):
                self.etudiant_concerne = user.etudiant
                self.error_message = None
                return queryset.filter(etudiant=user.etudiant).order_by('matiere__nom_matiere', '-date_creation')
            else:
                return queryset.none()

        # CAS 2 : C'est un prof ou admin -> LOGIQUE DE RECHERCHE
        matricule = self.request.GET.get('matricule')
        matricule_confirm = self.request.GET.get('matricule_confirm')
        
        self.etudiant_concerne = None
        self.error_message = None

        if matricule and matricule_confirm:
            if matricule != matricule_confirm:
                self.error_message = "Les deux matricules saisis ne correspondent pas."
                return queryset.none()
            
            try:
                etudiant = Etudiant.objects.get(matricule=matricule)
                self.etudiant_concerne = etudiant
                return queryset.filter(etudiant=etudiant).order_by('matiere__nom_matiere', '-date_creation')
            except Etudiant.DoesNotExist:
                self.error_message = f"Le matricule '{matricule}' est introuvable."
                return queryset.none()
        
        return queryset.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajout des variables pour la template
        context['etudiant_concerne'] = getattr(self, 'etudiant_concerne', None)
        context['error_message'] = getattr(self, 'error_message', None)
        context['is_enseignant'] = is_enseignant(self.request.user)
        return context

# Reste réservé aux ENSEIGNANTS
class NoteUpdateView(LoginRequiredMixin, EnseignantRequiredMixin, UpdateView):
    model = Note
    form_class = NoteForm 
    template_name = 'note_form.html'
    success_url = reverse_lazy('notes_list')
    
    def form_valid(self, form):
        if self.request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
             pass
        return super().form_valid(form)

class NoteDeleteView(LoginRequiredMixin, EnseignantRequiredMixin, DeleteView):
    model = Note
    template_name = 'note_confirm_delete.html' 
    success_url = reverse_lazy('notes_list')

    def post(self, request, *args, **kwargs):
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            response = super().post(request, *args, **kwargs)
            return response 
        return super().post(request, *args, **kwargs)

@login_required
def bulletin_de_notes(request, etudiant_pk):
    """
    Calcule le bulletin.
    Sécurité : Un étudiant ne peut voir QUE son propre bulletin.
    Un prof peut voir le bulletin de n'importe qui.
    """
    etudiant = get_object_or_404(Etudiant.objects.select_related('user', 'option_classe'), pk=etudiant_pk)
    
    # --- SECURITE ---
    user = request.user
    # Si je suis étudiant et que le PK demandé n'est pas le mien, JE BLOQUE.
    if is_etudiant(user) and not is_enseignant(user):
        if hasattr(user, 'etudiant') and user.etudiant.pk != int(etudiant_pk):
            return HttpResponseForbidden("Vous n'avez pas le droit de consulter ce bulletin.")
    # ----------------
    
    notes_etudiant = Note.objects.filter(etudiant=etudiant)
    if not notes_etudiant:
        return render(request, 'bulletin_notes.html', {'etudiant': etudiant, 'message': "Aucune note trouvée."})
        
    data_ue = {}
    total_general_produit_coef = Decimal('0.0')
    somme_total_coef = Decimal('0.0')
    
    for note in notes_etudiant:
        matiere = note.matiere 
        semestre = matiere.semestre
        ue = matiere.ue
        
        if not semestre or not ue:
             continue
        
        cod_ue = ue.code_ue
        nom_ue = ue.nom_ue

        try:
            total_produit = Decimal('0.0')
            total_coef = Decimal('0.0')
            
            if note.note_cm is not None and note.coef_cm is not None:
                total_produit += note.note_cm * note.coef_cm
                total_coef += note.coef_cm
                
            if note.note_td is not None and note.coef_td is not None:
                total_produit += note.note_td * note.coef_td
                total_coef += note.coef_td
                
            if note.note_tp is not None and note.coef_tp is not None:
                total_produit += note.note_tp * note.coef_tp
                total_coef += note.coef_tp
                
            if total_coef > 0:
                note_finale_matiere = (total_produit / total_coef).quantize(Decimal('0.01'))
            else:
                note_finale_matiere = Decimal('0.0')

        except Exception:
            note_finale_matiere = Decimal('0.0')
        
        coef_matiere = matiere.coef
        produit_note_coef = note_finale_matiere * coef_matiere
        
        if semestre not in data_ue:
            data_ue[semestre] = {'nom': semestre, 'ues': {}}
            
        if cod_ue not in data_ue[semestre]['ues']:
            data_ue[semestre]['ues'][cod_ue] = {
                'nom': nom_ue, 
                'matieres': [], 
                'somme_produit_note_coef': Decimal('0.0'), 
                'somme_coef': Decimal('0.0'),
                'note_ue': None 
            }
        
        data_ue[semestre]['ues'][cod_ue]['matieres'].append({
            'nom': matiere.nom_matiere,
            'note_finale': note_finale_matiere,
            'coef': coef_matiere
        })
        
        data_ue[semestre]['ues'][cod_ue]['somme_produit_note_coef'] += produit_note_coef
        data_ue[semestre]['ues'][cod_ue]['somme_coef'] += coef_matiere
    
    for semestre, semestre_data in data_ue.items():
        for cod_ue, ue_data in semestre_data['ues'].items():
            if ue_data['somme_coef'] > 0:
                note_ue = ue_data['somme_produit_note_coef'] / ue_data['somme_coef']
                ue_data['note_ue'] = note_ue.quantize(Decimal('0.01'))
                
                total_general_produit_coef += ue_data['note_ue'] * ue_data['somme_coef']
                somme_total_coef += ue_data['somme_coef'] 

    
    moyenne_generale = Decimal('0.0')
    if somme_total_coef > 0:
        moyenne_generale = (total_general_produit_coef / somme_total_coef).quantize(Decimal('0.01'))
        
    context = {
        'etudiant': etudiant,
        'data_ue': data_ue,
        'moyenne_generale': moyenne_generale,
        'total_general_produit_coef': total_general_produit_coef,
        'somme_total_coef': somme_total_coef
    }
    return render(request, 'bulletin_notes.html', context)
