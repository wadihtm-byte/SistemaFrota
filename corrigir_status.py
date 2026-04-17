from app import app
from database import db
from models import Monitoramento

with app.app_context():
    
    correcoes = {
        'Aguardando Carregamento': 'Ag. Carregamento',
        'Aguardando Descarga': 'Ag. Descarga',
        'Em Transito': 'Em Trânsito'
    }

    registros = Monitoramento.query.all()

    alterados = 0

    for r in registros:
        if r.status in correcoes:
            print(f'Corrigindo: {r.status} -> {correcoes[r.status]}')
            r.status = correcoes[r.status]
            alterados += 1

    db.session.commit()

    print(f'\n✅ Total corrigido: {alterados}')