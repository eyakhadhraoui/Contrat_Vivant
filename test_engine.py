# test_db.py
from tools.si_contrats_tool import get_contrat
from tools.si_sinistres_tool import get_sinistres

contrat = get_contrat("C001")
sinistres = get_sinistres("C001")

print("Contrat :", contrat)
print("Sinistres :", sinistres)