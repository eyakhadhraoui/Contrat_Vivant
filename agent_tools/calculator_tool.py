def calculer_ecart(garantie_max: float, montant_declare: float) -> str:
    '''Calcule l ecart en pourcentage entre garantie et montant declare.'''
    ecart = (montant_declare - garantie_max) / garantie_max * 100
    return f'Ecart de {round(ecart, 1)}%'
