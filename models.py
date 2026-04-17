from database import db

# ================= CLIENTE =================
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    cidade = db.Column(db.String(100))


# ================= MOTORISTA =================
class Motorista(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    cpf = db.Column(db.String(20))


# ================= CAVALO =================
class Cavalo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(10))
    modelo = db.Column(db.String(100))


# ================= CARRETA =================
class Carreta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(10))
    tipo = db.Column(db.String(100))


# ================= MONITORAMENTO =================
class Monitoramento(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    status = db.Column(db.String(50))
    cidade = db.Column(db.String(100))
    observacao = db.Column(db.String(200))

    motorista_id = db.Column(db.Integer, db.ForeignKey('motorista.id'))
    cavalo_id = db.Column(db.Integer, db.ForeignKey('cavalo.id'))

    carreta_id = db.Column(
        db.Integer,
        db.ForeignKey('carreta.id'),
        nullable=True
    )

    motorista = db.relationship('Motorista')
    cavalo = db.relationship('Cavalo')
    carreta = db.relationship('Carreta')


# ================= PROGRAMAÇÃO =================
class Programacao(db.Model):
    __bind_key__ = 'cadastros'

    id = db.Column(db.Integer, primary_key=True)

    # 🔹 GERAL
    cliente = db.Column(db.String(100))
    status = db.Column(db.String(50))

    # 🔹 VÍNCULOS (SEM FK PRA NÃO QUEBRAR O BIND)
    motorista_id = db.Column(db.Integer)
    cavalo_id = db.Column(db.Integer)
    carreta_id = db.Column(db.Integer)

    # 🔹 COLETA
    data_coleta = db.Column(db.String(20))
    hora_coleta = db.Column(db.String(10))
    origem = db.Column(db.String(100))

    # 🔹 ENTREGA
    data_entrega = db.Column(db.String(20))
    hora_entrega = db.Column(db.String(10))
    destino = db.Column(db.String(100))