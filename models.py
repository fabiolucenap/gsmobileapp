from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class AgendaItem(BaseModel):
    turno: str  # 'manhã', 'tarde' ou 'noite'
    dia_semana: str  # exemplo: 'segunda', 'terça', etc

class VoluntarioCreate(BaseModel):
    nome: str
    email: str
    telefone: Optional[str] = None
    cpf: str
    rg: Optional[str] = None
    cep: Optional[str] = None
    endereco: Optional[str] = None
    agenda: List[AgendaItem]


class Voluntario(VoluntarioCreate):
    id: int



# class ItemDoacao(BaseModel):
#     categoria: str
#     item_nome: str
#     quantidade: int

# class DoacaoCreate(BaseModel):
#     id_usuario: int
#     itens: List[ItemDoacao]

# class ItemDoacaoResponse(BaseModel):
#     id_item: int
#     categoria: str
#     item_nome: str
#     quantidade: int

# class DoacaoResponse(BaseModel):
#     id_doacao: int
#     id_usuario: int
#     data_doacao: date
#     status: str
#     itens: List[ItemDoacaoResponse]