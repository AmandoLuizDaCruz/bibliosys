# BiblioSys - Sistema de Gerenciamento de Biblioteca

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Django](https://img.shields.io/badge/Django-3.2+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📚 Descrição

**BiblioSys** é um sistema completo de gerenciamento de biblioteca implementado com **Django**, permitindo controle eficiente de:

- 📖 **Acervo**: Cadastro e gerenciamento de obras e exemplares
- 👥 **Leitores**: Gestão de usuários com diferentes tipos de vinculação
- 📤 **Empréstimos**: Controle completo de empréstimos e devoluções
- 📋 **Reservas**: Sistema de fila para obras emprestadas
- 💰 **Multas**: Cálculo automático de multas por atraso
- 📊 **Relatórios**: Dashboard com estatísticas para funcionários
- 🔐 **Segurança**: Autenticação, autorização e recuperação de senha

## 🛠️ Tecnologias

- **Backend**: Django 3.2+
- **Banco de Dados**: SQLite (desenvolvimento)
- **Autenticação**: Django Auth
- **Testes**: Django TestCase (53 testes automatizados)
- **Python**: 3.8+

## 📋 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- virtualenv (recomendado)

## 🚀 Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/AmandoLuizDaCruz/bibliosys.git
cd bibliosys/bibliosys
```

### 2. Criar ambiente virtual

```bash
python -m venv .venv
```

### 3. Ativar ambiente virtual

**Linux/Mac:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

### 4. Instalar dependências

```bash
pip install -r requirements.txt
```

### 5. Aplicar migrações

```bash
python manage.py migrate
```

### 6. Criar superusuário (admin)

```bash
python manage.py createsuperuser
```

### 7. Rodar servidor de desenvolvimento

```bash
python manage.py runserver
```

Acesse em: **http://localhost:8000**

## 📖 Como Usar

### Tipos de Usuário

1. **Admin/Administrador**
   - Gerenciamento completo do sistema
   - Acesso ao painel administrativo
   - Gestão de usuários e solicitações de funcionário

2. **Funcionário**
   - Gestão de acervo (obras e exemplares)
   - Processamento de empréstimos e devoluções
   - Acesso a relatórios
   - Visualização de notificações

3. **Leitor (Aluno/Professor/Público Externo)**
   - Visualização de obras disponíveis
   - Solicitação de empréstimos
   - Criação de reservas
   - Visualização de histórico pessoal

## 🧪 Executar Testes

### Rodar todos os testes (53 testes)

```bash
python manage.py test biblioteca
```

### Rodar testes específicos

```bash
# Testes de modelos
python manage.py test biblioteca.tests.ObraModelTests

# Testes de views
python manage.py test biblioteca.tests.RottasListagemTests

# Testes de formulários
python manage.py test biblioteca.tests.FormulariosCRUDTests
```

### Rodar testes com cobertura (verbose)

```bash
python manage.py test biblioteca --verbosity=2
```

## 📊 Estrutura do Projeto

```
bibliosys/
├── biblioteca/
│   ├── models.py              # Modelos de dados
│   ├── views.py               # Views principais
│   ├── views_*.py             # Views especializadas
│   ├── forms.py               # Formulários Django
│   ├── urls.py                # URLs e rotas
│   ├── tests.py               # Testes unitários (53 testes)
│   ├── templates/             # Templates HTML
│   └── static/                # Arquivos estáticos
├── config/
│   ├── settings.py            # Configurações Django
│   ├── urls.py                # URLs globais
│   └── wsgi.py                # WSGI config
├── templates/                 # Templates globais
├── manage.py                  # Comando Django
├── requirements.txt           # Dependências
└── README.md                  # Este arquivo
```

## 🗂️ Modelos Principais

### Obra
Representa um livro no acervo
- Título, autor, ISBN, editora
- Ano de publicação, categoria
- Quantidade de exemplares
- Soft delete via campo `ativo`

### Exemplar
Cópia física de uma obra
- Número sequencial
- Status (Disponível, Reservado, Emprestado, etc)
- Exemplar 1 é exclusivo para consulta local

### Leitor
Usuário do sistema
- Dados pessoais (nome, CPF, email, telefone)
- Tipo de vinculação (Aluno, Professor, Funcionário, Público Externo)
- Limite de empréstimos baseado no tipo

### Empréstimo
Registro de empréstimos
- Controle de datas (empréstimo, devolução, prazo)
- Renovações (máximo 1 renovação)
- Status (Ativo, Devolvido, Cancelado)

### Reserva
Sistema de fila para obras emprestadas
- Status (Fila, Aguardando Retirada, Retirada, Expirada, Cancelada)
- Posição na fila automática
- Notificação para funcionários

### Multa
Penalidades por atraso
- Cálculo automático por dias de atraso
- Valor configurável
- Status (Pendente, Paga, Cancelada)

## 🔐 Recuperação de Senha

Usuários podem recuperar sua senha através do fluxo completo:

1. Clicar em "Esqueci minha senha"
2. Informar o email cadastrado
3. Receber email com link de recuperação
4. Redefinir senha através do link
5. Fazer login com nova senha

## 📊 Relatórios

Funcionários aprovados têm acesso a relatórios com:
- Total de empréstimos
- Devoluções
- Multas pendentes e valores
- Reservas ativas
- Gráficos por status

## 🔍 Histórico com Filtros

Acesse o histórico de empréstimos com filtros por:
- **Status**: Ativo, Devolvido, Cancelado
- **Data**: Intervalo de datas
- **Leitor**: Nome ou username
- **Obra**: Título do livro

## 🤝 Contribuindo

Para contribuir com melhorias:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/melhoria`)
3. Commit suas mudanças (`git commit -am 'Adiciona melhoria'`)
4. Push para a branch (`git push origin feature/melhoria`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 👨‍💻 Autor

**Nattan Montel** - [GitHub](https://github.com/n4ttan)

## 📞 Suporte

Para relatar bugs ou solicitar features, abra uma [issue no GitHub](https://github.com/AmandoLuizDaCruz/bibliosys/issues).

## 📚 Documentação Adicional

- [Diagrama de Classes](./RELATORIO_BIBLIOSYS.md)
- [Diagrama de Casos de Uso](./Diagrama_de_Casos_de_Uso.pdf)
- [Testes Automatizados](./biblioteca/tests.py) - 53 testes cobrindo modelos, views e formulários

---

**Última atualização:** 2026-06-28  
**Status:** ✅ Em produção com 53 testes passando
