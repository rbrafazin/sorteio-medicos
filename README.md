# Sorteio Médico com Flask

Aplicação web em Flask para cadastro de médicos, geração de QR Code do formulário e sorteio aleatório de participantes em um painel administrativo protegido.

## Recursos

- Formulário responsivo com Bootstrap e validação de campos
- Geração automática do código do sorteio a cada cadastro
- Persistência em PostgreSQL com SQLAlchemy
- QR Code apontando para a URL pública do formulário
- Login administrativo com sessão protegida
- Sorteio aleatório com destaque do vencedor em modal
- Estrutura pronta para deploy com Gunicorn

## Variáveis de Ambiente

Todas as variáveis abaixo são **obrigatórias**. A aplicação **não inicia** sem elas.

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta usada pelo Flask para assinar sessões e tokens CSRF. Gere uma chave forte e única. |
| `ADMIN_USERNAME` | Nome de usuário para acesso ao painel administrativo. |
| `ADMIN_PASSWORD` | Senha em texto plano para o login administrativo. Pode ser omitida se `ADMIN_PASSWORD_HASH` for definida. |
| `ADMIN_PASSWORD_HASH` | Hash Werkzeug da senha administrativa. Alternativa mais segura a `ADMIN_PASSWORD`. |
| `DATABASE_URL` | URL de conexão com o banco PostgreSQL (ex.: `postgresql://user:pass@host:5432/dbname`). |
| `PUBLIC_BASE_URL` | *(Opcional)* URL pública da aplicação, usada na geração do QR Code (ex.: `https://meu-sorteio.onrender.com`). |

> **Nota:** Defina `ADMIN_PASSWORD` **ou** `ADMIN_PASSWORD_HASH`. Se ambas forem fornecidas, `ADMIN_PASSWORD` terá prioridade.

## Como executar

1. Crie e ative um ambiente virtual.

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente:

   ```powershell
   $env:SECRET_KEY = "<gere-uma-chave-forte>"
   $env:ADMIN_USERNAME = "<seu-usuario>"
   $env:ADMIN_PASSWORD = "<sua-senha-forte>"
   $env:DATABASE_URL = "postgresql://user:pass@localhost:5432/sorteio"
   ```

   Ou em Linux/macOS:

   ```bash
   export SECRET_KEY="<gere-uma-chave-forte>"
   export ADMIN_USERNAME="<seu-usuario>"
   export ADMIN_PASSWORD="<sua-senha-forte>"
   export DATABASE_URL="postgresql://user:pass@localhost:5432/sorteio"
   ```

4. Inicie a aplicação:

   ```bash
   python wsgi.py
   ```

5. Acesse o login administrativo em `/admin/login`.

## Deploy com Gunicorn

```bash
gunicorn wsgi:app
```

Para produção, configure todas as variáveis de ambiente obrigatórias na plataforma de hospedagem. O QR Code passará a apontar para a `PUBLIC_BASE_URL` quando definida.
