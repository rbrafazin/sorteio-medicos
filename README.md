# Sorteio Medico com Flask

Aplicacao web em Flask para cadastro de medicos, geracao de QR Code do formulario e sorteio aleatorio de participantes em um painel administrativo protegido.

## Recursos

- Formulario responsivo com Bootstrap e validacao de campos
- Geracao automatica do codigo do sorteio a cada cadastro
- Persistencia em SQLite com SQLAlchemy
- QR Code apontando para a URL publica do formulario
- Login administrativo com sessao protegida
- Sorteio aleatorio com destaque do vencedor em modal
- Estrutura pronta para deploy com Gunicorn

## Como executar

1. Crie e ative um ambiente virtual.
2. Instale as dependencias:

```bash
pip install -r requirements.txt
```

3. Defina a chave secreta e as credenciais administrativas:

```powershell
$env:SECRET_KEY="sua-chave-segura"
$env:ADMIN_USERNAME="admin"
$env:ADMIN_PASSWORD="senha-forte"
```

4. Inicie a aplicacao:

```bash
python wsgi.py
```

5. Acesse o login administrativo em `/admin/login`.

## Deploy

Para producao, configure estas variaveis de ambiente na plataforma:

- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `PUBLIC_BASE_URL`

Exemplo de `PUBLIC_BASE_URL`:

```text
https://meu-sorteio.onrender.com
```

O QR Code passara a apontar para essa URL publica.

## Deploy com Gunicorn

```bash
gunicorn wsgi:app
```

O banco SQLite sera criado automaticamente em `instance/sorteio.db`.
