from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from database import db
from models import Motorista, Cavalo, Carreta, Monitoramento, Programacao
import os
import json
import hashlib

app = Flask(__name__)
app.secret_key = 'chave_super_segura_123'  # 🔥 ajuste aqui

# ================= CONFIG BANCO =================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')

if not os.path.exists(INSTANCE_DIR):
    os.makedirs(INSTANCE_DIR)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(INSTANCE_DIR, 'frota.db')

app.config['SQLALCHEMY_BINDS'] = {
    'cadastros': 'sqlite:///' + os.path.join(INSTANCE_DIR, 'cadastros.db')
}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ================= LOGIN =================
USUARIO = 'admin'
SENHA = '1234'

@app.before_request
def proteger_rotas():
    rotas_livres = ['login', 'static']

    if not request.endpoint:
        return

    if request.endpoint not in rotas_livres:
        if not session.get('logado'):
            return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('usuario') == USUARIO and request.form.get('senha') == SENHA:
            session['logado'] = True
            return redirect(url_for('index'))

        return render_template('login.html', erro="Usuário ou senha inválidos")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect(url_for('login'))

# ================= STATUS =================
STATUS_VALIDOS = [
    'Programado',
    'Ag. Carregamento',
    'Em Carregamento',
    'Carregado',
    'Em Trânsito',
    'Ocorrência',
    'Ag. Descarga',
    'Em Descarga',
    'Finalizado',
    'Ag. Programação'
]

# ================= RESUMO =================
def gerar_resumo():
    dados = Monitoramento.query.all()

    resumo = {
        'Em Trânsito': 0,
        'Carregado': 0,
        'Em Carga/Descarga': 0,
        'Ocorrência': 0,
        'Disponíveis': 0
    }

    for d in dados:
        if d.status == 'Em Trânsito':
            resumo['Em Trânsito'] += 1
        elif d.status == 'Carregado':
            resumo['Carregado'] += 1
        elif d.status in ['Ag. Carregamento', 'Em Carregamento', 'Ag. Descarga', 'Em Descarga']:
            resumo['Em Carga/Descarga'] += 1
        elif d.status == 'Ocorrência':
            resumo['Ocorrência'] += 1
        elif d.status in ['Finalizado', 'Ag. Programação']:
            resumo['Disponíveis'] += 1

    return resumo, len(dados)

# ================= DASHBOARD =================
@app.route('/')
def index():
    resumo, total = gerar_resumo()
    return render_template('index.html', resumo=resumo, total=total)

@app.route('/dados_dashboard')
def dados_dashboard():
    resumo, total = gerar_resumo()

    dados_str = json.dumps(resumo, sort_keys=True) + str(total)
    hash_dados = hashlib.md5(dados_str.encode()).hexdigest()

    return jsonify({
        "resumo": resumo,
        "total": total,
        "hash": hash_dados
    })

# ================= CADASTROS =================
@app.route('/motoristas', methods=['GET', 'POST'])
def motoristas():
    if request.method == 'POST':
        db.session.add(Motorista(
            nome=request.form.get('nome'),
            cpf=request.form.get('cpf')
        ))
        db.session.commit()
        flash("Motorista cadastrado ✅")
        return redirect(url_for('motoristas'))

    return render_template(
        'motoristas.html',
        motoristas=Motorista.query.order_by(Motorista.nome.asc()).all()
    )

@app.route('/cavalos', methods=['GET', 'POST'])
def cavalos():
    if request.method == 'POST':
        db.session.add(Cavalo(
            placa=request.form.get('placa'),
            modelo=request.form.get('modelo')
        ))
        db.session.commit()
        flash("Cavalo cadastrado ✅")
        return redirect(url_for('cavalos'))

    return render_template(
        'cavalos.html',
        cavalos=Cavalo.query.order_by(Cavalo.placa.asc()).all()
    )

@app.route('/carretas', methods=['GET', 'POST'])
def carretas():
    if request.method == 'POST':
        db.session.add(Carreta(
            placa=request.form.get('placa'),
            tipo=request.form.get('tipo')
        ))
        db.session.commit()
        flash("Carreta cadastrada ✅")
        return redirect(url_for('carretas'))

    return render_template(
        'carretas.html',
        carretas=Carreta.query.order_by(Carreta.placa.asc()).all()
    )

# ================= MONITORAMENTO =================
@app.route('/monitoramento', methods=['GET', 'POST'])
def monitoramento():
    if request.method == 'POST':

        status = request.form.get('status')

        if not status or status not in STATUS_VALIDOS:
            flash("❌ Status inválido!")
            return redirect(url_for('monitoramento'))

        novo = Monitoramento(
            status=status,
            motorista_id=request.form.get('motorista') or None,
            cavalo_id=request.form.get('cavalo') or None,
            carreta_id=request.form.get('carreta') or None,
            cidade=request.form.get('cidade'),
            observacao=request.form.get('observacao')
        )

        db.session.add(novo)
        db.session.commit()

        flash("Registro criado 📡")
        return redirect(url_for('monitoramento'))

    return render_template(
        'monitoramento.html',
        monitoramentos=Monitoramento.query.all(),
        motoristas=Motorista.query.order_by(Motorista.nome.asc()).all(),
        cavalos=Cavalo.query.order_by(Cavalo.placa.asc()).all(),
        carretas=Carreta.query.order_by(Carreta.placa.asc()).all()
    )

# ================= PROGRAMAÇÃO =================
@app.route('/programacao', methods=['GET', 'POST'])
def programacao():

    if request.method == 'POST':
        nova = Programacao(
            cliente=request.form.get('cliente'),
            status=request.form.get('status'),

            motorista_id=request.form.get('motorista') or None,
            cavalo_id=request.form.get('cavalo') or None,
            carreta_id=request.form.get('carreta') or None,

            data_coleta=request.form.get('data_coleta'),
            hora_coleta=request.form.get('hora_coleta'),
            origem=request.form.get('origem'),

            data_entrega=request.form.get('data_entrega'),
            hora_entrega=request.form.get('hora_entrega'),
            destino=request.form.get('destino')
        )

        db.session.add(nova)
        db.session.commit()

        flash("Programação cadastrada 📅")
        return redirect(url_for('programacao'))

    programacoes = Programacao.query.order_by(Programacao.id.desc()).all()

    for p in programacoes:
        motorista = Motorista.query.get(p.motorista_id)
        cavalo = Cavalo.query.get(p.cavalo_id)
        carreta = Carreta.query.get(p.carreta_id)

        p.motorista_nome = motorista.nome if motorista else ''
        p.cavalo_placa = cavalo.placa if cavalo else ''
        p.carreta_placa = carreta.placa if carreta else ''

    return render_template(
        'programacao.html',
        programacoes=programacoes,
        motoristas=Motorista.query.order_by(Motorista.nome).all(),
        cavalos=Cavalo.query.order_by(Cavalo.placa).all(),
        carretas=Carreta.query.order_by(Carreta.placa).all()
    )

# ================= EXCLUIR =================
@app.route('/excluir_programacao/<int:id>', methods=['POST'])
def excluir_programacao(id):
    p = Programacao.query.get_or_404(id)

    db.session.delete(p)
    db.session.commit()
    flash("Excluído 🗑️")

    return redirect(url_for('programacao'))

# ================= EDITAR =================
@app.route('/editar_programacao/<int:id>', methods=['GET', 'POST'])
def editar_programacao(id):

    p = Programacao.query.get_or_404(id)

    if request.method == 'POST':
        p.cliente = request.form.get('cliente')
        p.status = request.form.get('status')

        p.motorista_id = request.form.get('motorista') or None
        p.cavalo_id = request.form.get('cavalo') or None
        p.carreta_id = request.form.get('carreta') or None

        p.data_coleta = request.form.get('data_coleta')
        p.hora_coleta = request.form.get('hora_coleta')
        p.origem = request.form.get('origem')

        p.data_entrega = request.form.get('data_entrega')
        p.hora_entrega = request.form.get('hora_entrega')
        p.destino = request.form.get('destino')

        db.session.commit()

        flash("Programação atualizada ✏️")
        return redirect(url_for('programacao'))

    return render_template(
        'editar_programacao.html',
        p=p,
        motoristas=Motorista.query.order_by(Motorista.nome).all(),
        cavalos=Cavalo.query.order_by(Cavalo.placa).all(),
        carretas=Carreta.query.order_by(Carreta.placa).all()
    )
# ================= EDITAR MONITORAMENTO =================
@app.route('/editar_monitoramento/<int:id>', methods=['POST'])
def editar_monitoramento(id):

    m = Monitoramento.query.get_or_404(id)

    status = request.form.get('status')

    if not status:
        flash("❌ Status inválido")
        return redirect(url_for('monitoramento'))

    m.status = status
    m.motorista_id = request.form.get('motorista') or None
    m.cavalo_id = request.form.get('cavalo') or None
    m.carreta_id = request.form.get('carreta') or None
    m.cidade = request.form.get('cidade')
    m.observacao = request.form.get('observacao')

    db.session.commit()

    flash("Atualizado com sucesso 💾")
    return redirect(url_for('monitoramento'))


# ================= EXCLUIR MONITORAMENTO =================
@app.route('/excluir_monitoramento/<int:id>', methods=['POST'])
def excluir_monitoramento(id):

    m = Monitoramento.query.get_or_404(id)

    db.session.delete(m)
    db.session.commit()

    flash("Excluído 🗑️")
    return redirect(url_for('monitoramento'))

# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)