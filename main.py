# main.py
from fastapi import FastAPI, HTTPException
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import oracledb
import os
from dotenv import load_dotenv
from models import Voluntario, VoluntarioCreate, AgendaItem

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_SID = os.getenv("DB_SID")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

#ROTA1
@app.post("/voluntarios", response_model=Voluntario)
def criar_voluntario(voluntario: VoluntarioCreate):
    try:
        dsn = oracledb.makedsn(DB_HOST, DB_PORT, sid=DB_SID)
        conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM USUARIOS WHERE EMAIL = :1 OR CPF = :2", (voluntario.email, voluntario.cpf))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="CPF ou e-mail já cadastrado.")

        id_usuario = cursor.var(oracledb.NUMBER)

        cursor.execute("""
            INSERT INTO USUARIOS (NOME, EMAIL, TELEFONE, CPF, RG, CEP, ENDERECO)
            VALUES (:1, :2, :3, :4, :5, :6, :7)
            RETURNING ID_USUARIO INTO :8
        """, (
            voluntario.nome, voluntario.email, voluntario.telefone,
            voluntario.cpf, voluntario.rg, voluntario.cep, voluntario.endereco,
            id_usuario
        ))

        novo_id = int(id_usuario.getvalue()[0])

        for item in voluntario.agenda:
            cursor.execute("""
                INSERT INTO AGENDA_VOLUNTARIO (ID_USUARIO, TURNO, DIA_SEMANA)
                VALUES (:1, :2, :3)
            """, (
                novo_id, item.turno, item.dia_semana
            ))

        conn.commit()
        return Voluntario(id=novo_id, **voluntario.dict())

    except Exception as e:
        print("Erro ao cadastrar voluntário:", e)
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar voluntário: {e}")

    finally:
        cursor.close()
        conn.close()

#ROTA2
@app.get("/voluntarios", response_model=List[Voluntario])
def listar_voluntarios():
    dsn = oracledb.makedsn(DB_HOST, DB_PORT, sid=DB_SID)
    conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)
    cursor = conn.cursor()

    cursor.execute("SELECT ID_USUARIO, NOME, EMAIL, TELEFONE, CPF, RG, CEP, ENDERECO FROM USUARIOS")
    usuarios = cursor.fetchall()

    voluntarios = []
    for row in usuarios:
        id_usuario = row[0]
        cursor.execute("SELECT TURNO, DIA_SEMANA FROM AGENDA_VOLUNTARIO WHERE ID_USUARIO = :1", [id_usuario])
        agenda_rows = cursor.fetchall()
        agenda = [{"turno": a[0], "dia_semana": a[1]} for a in agenda_rows]

        voluntario = {
            "id": row[0],
            "nome": row[1],
            "email": row[2],
            "telefone": row[3] or "",
            "cpf": row[4],
            "rg": row[5] or "",
            "cep": row[6] or "",
            "endereco": row[7] or "",
            "agenda": agenda
        }
        voluntarios.append(voluntario)

    cursor.close()
    conn.close()

    return voluntarios

#ROTA3
@app.get("/voluntarios/{voluntario_id}", response_model=Voluntario)
def obter_voluntario(voluntario_id: int):
    dsn = oracledb.makedsn(DB_HOST, DB_PORT, sid=DB_SID)
    conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)
    cursor = conn.cursor()

    cursor.execute("SELECT ID_USUARIO, NOME, EMAIL, TELEFONE, CPF, RG, CEP, ENDERECO FROM USUARIOS WHERE ID_USUARIO = :1", [voluntario_id])
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Voluntário não encontrado")

    cursor.execute("SELECT TURNO, DIA_SEMANA FROM AGENDA_VOLUNTARIO WHERE ID_USUARIO = :1", [voluntario_id])
    agenda_rows = cursor.fetchall()
    agenda = [{"turno": a[0], "dia_semana": a[1]} for a in agenda_rows]

    cursor.close()
    conn.close()

    return Voluntario(
        id=row[0],
        nome=row[1],
        email=row[2],
        telefone=row[3] or "",
        cpf=row[4],
        rg=row[5] or "",
        cep=row[6] or "",
        endereco=row[7] or "",
        agenda=agenda
    )

#ROTA4
@app.put("/voluntarios/{voluntario_id}")
def atualizar_voluntario(voluntario_id: int, voluntario: VoluntarioCreate):
    try:
        dsn = oracledb.makedsn(DB_HOST, DB_PORT, sid=DB_SID)
        conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE USUARIOS SET
                NOME = :1,
                EMAIL = :2,
                TELEFONE = :3,
                CPF = :4,
                RG = :5,
                CEP = :6,
                ENDERECO = :7
            WHERE ID_USUARIO = :8
            """,
            (
                voluntario.nome, voluntario.email, voluntario.telefone,
                voluntario.cpf, voluntario.rg, voluntario.cep,
                voluntario.endereco, voluntario_id
            )
        )

        cursor.execute("DELETE FROM AGENDA_VOLUNTARIO WHERE ID_USUARIO = :1", [voluntario_id])
        for item in voluntario.agenda:
            cursor.execute(
                "INSERT INTO AGENDA_VOLUNTARIO (ID_USUARIO, TURNO, DIA_SEMANA) VALUES (:1, :2, :3)",
                (voluntario_id, item.turno, item.dia_semana)
            )

        conn.commit()
        return {"mensagem": "Voluntário atualizado com sucesso"}

    except Exception as e:
        print("Erro ao atualizar voluntário:", e)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar voluntário: {e}")

    finally:
        cursor.close()
        conn.close()

#ROTA5
@app.delete("/voluntarios/{voluntario_id}")
def deletar_voluntario(voluntario_id: int):
    try:
        dsn = oracledb.makedsn(DB_HOST, DB_PORT, sid=DB_SID)
        conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM USUARIOS WHERE ID_USUARIO = :1", [voluntario_id])
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Voluntário não encontrado.")

        cursor.execute("DELETE FROM AGENDA_VOLUNTARIO WHERE ID_USUARIO = :1", [voluntario_id])
        cursor.execute("DELETE FROM USUARIOS WHERE ID_USUARIO = :1", [voluntario_id])

        conn.commit()
        return {"mensagem": "Voluntário excluído com sucesso"}

    except Exception as e:
        print("Erro ao excluir voluntário:", e)
        raise HTTPException(status_code=500, detail=f"Erro ao excluir voluntário: {e}")

    finally:
        cursor.close()
        conn.close()





#ROTA6
@app.get("/agenda/{id_usuario}", response_model=List[AgendaItem])
def obter_agenda_por_usuario(id_usuario: int):
    dsn = oracledb.makedsn(DB_HOST, DB_PORT, sid=DB_SID)
    conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)
    cursor = conn.cursor()

    cursor.execute("SELECT TURNO, DIA_SEMANA FROM AGENDA_VOLUNTARIO WHERE ID_USUARIO = :1", [id_usuario])
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="Agenda não encontrada para este voluntário.")

    return [{"turno": r[0], "dia_semana": r[1]} for r in rows]


#ROTA7
@app.put("/agenda/{id_usuario}")
def atualizar_agenda(id_usuario: int, agenda: List[AgendaItem]):
    try:
        dsn = oracledb.makedsn(DB_HOST, DB_PORT, sid=DB_SID)
        conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM USUARIOS WHERE ID_USUARIO = :1", [id_usuario])
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Voluntário não encontrado.")

        cursor.execute("DELETE FROM AGENDA_VOLUNTARIO WHERE ID_USUARIO = :1", [id_usuario])

        for item in agenda:
            cursor.execute("""
                INSERT INTO AGENDA_VOLUNTARIO (ID_USUARIO, TURNO, DIA_SEMANA)
                VALUES (:1, :2, :3)
            """, (id_usuario, item.turno, item.dia_semana))

        conn.commit()
        return {"mensagem": "Agenda atualizada com sucesso"}

    except Exception as e:
        print("Erro ao atualizar agenda:", e)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar agenda: {e}")

    finally:
        cursor.close()
        conn.close()




#ROTA8
@app.get("/doacoes")
def listar_doacoes():
    try:
        dsn = oracledb.makedsn(DB_HOST, DB_PORT, sid=DB_SID)
        conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)
        cursor = conn.cursor()

        cursor.execute("SELECT ID_DOACAO, ID_USUARIO, DATA_DOACAO, STATUS FROM DOACOES")
        rows = cursor.fetchall()
        resultado = [
            {"id_doacao": r[0], "id_usuario": r[1], "data_doacao": str(r[2]), "status": r[3]}
            for r in rows
        ]

        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar doações: {e}")
    finally:
        cursor.close()
        conn.close()


#ROTA9
@app.get("/itens_doacao")
def listar_itens_doacao():
    try:
        dsn = oracledb.makedsn(DB_HOST, DB_PORT, sid=DB_SID)
        conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)
        cursor = conn.cursor()

        cursor.execute("SELECT ID_ITEM, ID_DOACAO, CATEGORIA, ITEM_NOME, QUANTIDADE FROM ITENS_DOACAO")
        rows = cursor.fetchall()
        resultado = [
            {"id_item": r[0], "id_doacao": r[1], "categoria": r[2], "item_nome": r[3], "quantidade": r[4]}
            for r in rows
        ]

        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar itens de doação: {e}")
    finally:
        cursor.close()
        conn.close()


#ROTA10
@app.get("/recebimentos")
def listar_recebimentos():
    try:
        dsn = oracledb.makedsn(DB_HOST, DB_PORT, sid=DB_SID)
        conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)
        cursor = conn.cursor()

        cursor.execute("SELECT ID_RECEBIMENTO, ID_DOACAO, DATA_RECEBIDO, CONFIRMADO_POR, OBSERVACAO FROM RECEBIMENTOS")
        rows = cursor.fetchall()
        resultado = [
            {
                "id_recebimento": r[0],
                "id_doacao": r[1],
                "data_recebido": str(r[2]),
                "confirmado_por": r[3],
                "observacao": r[4]
            }
            for r in rows
        ]

        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar recebimentos: {e}")
    finally:
        cursor.close()
        conn.close()
