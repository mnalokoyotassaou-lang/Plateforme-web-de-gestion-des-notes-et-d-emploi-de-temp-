from django.urls import path
from . import views 
from .views import (
    # Importez explicitement toutes les classes de vues
    EtudiantListView, EtudiantCreateView, EtudiantUpdateView, EtudiantDeleteView,
    ProfesseurListView, ProfesseurCreateView, ProfesseurUpdateView, ProfesseurDeleteView,
    home_view,
    SemestreListView, SemestreCreateView, SemestreUpdateView, SemestreDeleteView,
    UEListView, UECreateView, UEUpdateView, UEDeleteView,
    MatiereListView, MatiereCreateView, MatiereUpdateView, MatiereDeleteView,
    EmploiListView, EmploiCreateView, EmploiUpdateView, EmploiDeleteView,NoteCreateView,NoteListView
    
    
)
from django.contrib.auth import views as auth_views
urlpatterns = [
    # --- URLS PUBLIQUES/HOME ---
    #path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'), # Ajout de la vue tableau de bord
    path('register/', views.register, name='register'), # Ajout de la vue register
    path('', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
     path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
     path('home/', views.home_view, name='home'),
    # --------------------------------------------------------------------------------
    # --- URLS CRUD ETUDIANT (Vues par Classes) ---
    # --------------------------------------------------------------------------------
    path('etudiants/', views.EtudiantListView.as_view(), name='etudiant_list'),
    path('etudiants/ajouter/', views.EtudiantCreateView.as_view(), name='etudiant_create'),
    path('etudiants/<int:pk>/detail/', views.etudiant_detail, name='etudiant_detail'), # Vue par Fonction
    path('etudiants/<int:pk>/modifier/', views.EtudiantUpdateView.as_view(), name='etudiant_update'),
    path('etudiants/<int:pk>/supprimer/', views.EtudiantDeleteView.as_view(), name='etudiant_delete'),
    
    # --------------------------------------------------------------------------------
    # --- URLS CRUD PROFESSEUR (Vues par Classes) ---
    # --------------------------------------------------------------------------------
    path('professeurs/', views.ProfesseurListView.as_view(), name='professeur_list'),
    path('professeurs/ajouter/', views.ProfesseurCreateView.as_view(), name='professeur_create'),
    path('professeurs/<int:pk>/modifier/', views.ProfesseurUpdateView.as_view(), name='professeur_update'),
    path('professeurs/<int:pk>/supprimer/', views.ProfesseurDeleteView.as_view(), name='professeur_delete'),

    
    # --------------------------------------------------------------------------------
    path('semestres/', views.SemestreListView.as_view(), name='semestre_list'),
    path('semestres/ajouter/', views.SemestreCreateView.as_view(), name='semestre_create'),
    path('semestres/<str:pk>/modifier/', views.SemestreUpdateView.as_view(), name='semestre_update'),
    path('semestres/<str:pk>/supprimer/', views.SemestreDeleteView.as_view(), name='semestre_delete'),

    # --------------------------------------------------------------------------------
    # --- URLS CRUD UE (Vues par Classes) ---
    # --------------------------------------------------------------------------------
    path('ues/', views.UEListView.as_view(), name='ue_list'),
    path('ues/ajouter/', views.UECreateView.as_view(), name='ue_create'),
    path('ues/<str:pk>/modifier/', views.UEUpdateView.as_view(), name='ue_update'),
    path('ues/<str:pk>/supprimer/', views.UEDeleteView.as_view(), name='ue_delete'),

    # --------------------------------------------------------------------------------
    # --- URLS CRUD MATIERE (Vues par Classes) ---
    # --------------------------------------------------------------------------------
    path('matieres/', views.MatiereListView.as_view(), name='matiere_list'),
    path('matieres/ajouter/', views.MatiereCreateView.as_view(), name='matiere_create'),
    path('matieres/<str:pk>/modifier/', views.MatiereUpdateView.as_view(), name='matiere_update'),
    path('matieres/<str:pk>/supprimer/', views.MatiereDeleteView.as_view(), name='matiere_delete'),

    # --------------------------------------------------------------------------------
    # --- URLS CRUD EMPLOI DU TEMPS (Vues par Classes) ---
    # --------------------------------------------------------------------------------
    path('emplois/', views.EmploiListView.as_view(), name='emploi_list'),
   
    path('emplois/ajouter/', views.EmploiCreateView.as_view(), name='emploi_create'),
    path('emplois/<int:pk>/modifier/', views.EmploiUpdateView.as_view(), name='emploi_update'),
    path('emplois/<int:pk>/supprimer/', views.EmploiDeleteView.as_view(), name='emploi_delete'),
    
    # --------------------------------------------------------------------------------
    # --- URLS NOTES ET BULLETIN (Vues par Fonctions/Classes) ---
    # --------------------------------------------------------------------------------
    path('notes/saisir', views.NoteCreateView.as_view(), name='note_create'), # Vue par Classe
    path('etudiants/<int:etudiant_pk>/bulletin/',   views.bulletin_de_notes,   name='bulletin_de_notes'),
    
    # Consultation/Liste des notes (avec filtre par matricule)
    path('notes/', views.NoteListView.as_view(), name='notes_list'),
    
    # Création de note (utilisé par le script AJAX)
    #path('notes/ajouter/', views.NoteCreateView, name='NoteCreate'),
    
    # Modification de note (PK = Primary Key/ID de la note)
    path('notes/<int:pk>/modifier/', views.NoteUpdateView.as_view(), name='NoteUpdate'),
    
    # Suppression de note
    path('notes/<int:pk>/supprimer/', views.NoteDeleteView.as_view(), name='NoteDelete'),
]