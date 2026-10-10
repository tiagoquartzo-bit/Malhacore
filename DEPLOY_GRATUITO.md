# GUIA DE HOSPEDAGEM GRATUITA & PUBLICAÇÃO — MALHACORE

Este guia mostra como colocar a central **MalhaCore** no ar gratuitamente, acessível de qualquer lugar (celular, tablet ou computador), já com a sua credencial master cadastrada e protegida.

---

## 1. Suas Credenciais de Acesso (Já Cadastradas e Prontas)

O sistema já provisionou seu usuário administrador com criptografia militar PBKDF2:

- **Link de Entrada:** `/login`
- **E-mail do Operador:** `tiagoaraujoxsl@gmail.com`
- **Chave de Acesso / Senha:** `Neyva@10`

---

## 2. Opção 1: Publicação Gratuita no Render.com (Recomendada)

O [Render.com](https://render.com) é a melhor plataforma gratuita para **FastAPI**:
- Custo: **R$ 0,00 / mês** (plano Free Web Service permanente).
- Certificado SSL/HTTPS automático e gratuito (`https://suacentral.onrender.com`).
- Não exige cartão de crédito.

### Passo a Passo (Leva menos de 3 minutos):

1. **Subir os arquivos para o GitHub:**
   - Crie um repositório no seu GitHub (público ou privado) chamado `MalhaCore`.
   - Você pode descompactar o pacote pronto **`MalhaCore_Deploy.zip`** e arrastar os arquivos diretamente pelo navegador (botão "Add file" -> "Upload files").

2. **Criar o Serviço no Render:**
   - Acesse [https://render.com](https://render.com) e faça login (pode ser com sua conta do GitHub ou Google).
   - Clique no botão azul **"New +"** &rarr; **"Web Service"**.
   - Conecte o repositório `MalhaCore`.

3. **Configuração Simples:**
   - **Name:** `malhacore` (ou o nome que preferir)
   - **Language:** `Python 3`
   - **Region:** `Ohio (US East)` ou `Frankfurt`
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free` (0 USD/mo)

4. **Pronto!**
   - O Render vai compilar e gerar a sua URL pública (ex: `https://malhacore.onrender.com`).
   - Ao acessar, você verá a tela de **AUTENTICAÇÃO CENTRAL**. Basta colocar `tiagoaraujoxsl@gmail.com` e `Neyva@10`!

---

## 3. Opção 2: Publicação no PythonAnywhere (Via ZIP Pronto)

Como você já possui a conta `tiago` rodando o app da clínica em `https://tiago.pythonanywhere.com`, você tem duas alternativas no PythonAnywhere:

### Alternativa A: Criar uma segunda conta gratuita (ex: `malhacore.pythonanywhere.com`)
1. Crie uma conta gratuita em [https://www.pythonanywhere.com](https://www.pythonanywhere.com).
2. Na aba **Files**, envie o arquivo pronto **`MalhaCore_Deploy.zip`** (gerado na raiz da pasta `06.MalhaCore`).
3. Na aba **Consoles**, abra um Bash console e descompacte:
   ```bash
   unzip MalhaCore_Deploy.zip -d ~/06.MalhaCore
   cd ~/06.MalhaCore
   pip install -r requirements.txt
   ```
4. Na aba **Web**, crie uma Web App (Manual Configuration, Python 3.10 ou superior).
5. No link de configuração do arquivo WSGI, substitua o conteúdo pelo que já está no arquivo `wsgi_pythonanywhere.py`:
   ```python
   import sys
   import os

   app_dir = os.path.expanduser('~/06.MalhaCore')
   if app_dir not in sys.path:
       sys.path.insert(0, app_dir)

   from asgiref.wsgi import WsgiToAsgi
   from main import app as asgi_app

   application = WsgiToAsgi(asgi_app)
   ```

---

## 4. Rotina de Uso no Dia a Dia

Com o sistema no ar:
1. **Acessos Diários:** Acesse de qualquer lugar pelo celular ou computador.
2. **Atualização de Valores:**
   * Clique em **`+ NOVO CONTRATO`** para adicionar qualquer novo cliente, valor mensal e plano.
   * Clique em **`BAIXA`** quando o cliente pagar (o sistema registra a data/hora e recalcula o faturamento liquidado).
   * Clique em **`COBRAR`** para abrir o WhatsApp do cliente com o texto pronto de cobrança.
   * Clique em **`EXPORTAR LEDGER CSV`** para baixar a planilha conciliada a qualquer momento.
3. **Rollout de Novos Apps:**
   * O **MalhaX** já está destacado na central para o cliente **Activia**.
   * Conforme você avançar com a **Açaiteria Maranata** ou outros clientes, basta atualizar os cards diretamente na central.

