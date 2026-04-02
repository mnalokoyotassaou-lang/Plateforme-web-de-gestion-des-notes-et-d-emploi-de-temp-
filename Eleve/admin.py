from django.contrib import admin
from .models import Etudiant,Professeur,UE,Emploi,Note,Matiere,Option
# Register your models here.
admin.site.register(Etudiant)
admin.site.register(Professeur)
admin.site.register(UE)
admin.site.register(Matiere)
admin.site.register(Emploi)
admin.site.register(Note)
admin.site.register(Option)
