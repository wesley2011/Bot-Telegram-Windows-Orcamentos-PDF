import json, os, telegram, locale
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
)
from telegram.ext import (
    ConversationHandler,
    CallbackContext,
)

from conversacoes.geraPdf_1 import (
    preencher_dados_excel, 
)
from conversacoes.gerencia import (
    verificar_creditos
)

from conversacoes.FunComplementar import (
    ler_informacoes_usuario, formatar_cnpj_cpf
)

from conversacoes.gerencia import(
    verificar_creditos, consumir_credito
)

from conversacoes.geraPdf_2 import (
    caminho_foto_usuario, caminho_layout, caminho_salvar_pdf, inserir_imagem_excel
    # caminho_salvar_pdf(user_id, "orçamento - nº") e retorna o caminho da dele
    # caminho_foto_usuario(user_id) e retorna o caminho da foto
    # caminho_layout("nome do layout") e retorna o caminho dele
)
from conversacoes.receber_foto import load_image_log

# Estado de conversação GERAÇÃO DE ORÇAMENTO
SELECIONAR_CLIENTE, RECEBER_MENSAGEM, RECEBER_VALOR_TOTAL, RECEBER_OBSERVACAO, REVISAO_ORCAMENTO, CONFIRMAR_EDICAO, ADICIONAR_LINHA, RECEBER_OBSERVACAO_TEXTO = range(8)



def funcao_auxiliar_orçamento(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
   
    message = f"˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙\n"
    query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)

    # Redireciona o usuário para o comando /iniciar_orcamento
    context.bot.send_message(chat_id=query.message.chat_id, text='Aperte aqui 👉 /orcamento')

    # Retorna o estado atual para evitar problemas com o ConversationHandler
    return ConversationHandler.END


def iniciar_orcamento(update: Update = None, context: CallbackContext = None) -> int:

    if update:
        user_id = update.effective_user.id


    user_id = update.message.chat_id

    situação_usuario = verificar_creditos(user_id)
    if situação_usuario:
        if situação_usuario["tipo"] == "mensal":
            update.message.reply_text(situação_usuario["mensagem"])
            return ConversationHandler.END
        elif situação_usuario["tipo"] == "credito":
            update.message.reply_text(situação_usuario["mensagem"])
            return ConversationHandler.END


    user_info = ler_informacoes_usuario(user_id)

    cadastros = user_info.get("cadastros", [])
    context.user_data["clientes"] = cadastros
    clientes_list = [cadastro for cadastro in cadastros if cadastro.get("tipo") == "cliente"]

    matriz = user_info.get("cadastros", [])
    for cadastro in matriz:
        if cadastro.get("tipo") == "matriz":
            matriz = cadastro
            break
    else:
        update.message.reply_text(f"Você não possui uma matriz cadastrada.\nComando cancelado.")
        return ConversationHandler.END
    
    if not clientes_list:
        update.message.reply_text(f"Você não possui clientes cadastrados.\nComando cancelado.")
        return ConversationHandler.END

    keyboard = [
        [
            
            InlineKeyboardButton(
                
                f"{i + 1} - {formatar_cnpj_cpf(cliente['nome'], cliente['cnpj_cpf'])}",
                callback_data=f"cliente_{i + 1}"
            )
        ] for i, cliente in enumerate(clientes_list)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    client = f"___Geração de orçamento em PDF, eu irei fazer algumas perguntas simples para você.___\n" \
            f"___As perguntas serão proprias para orçamento.___\n" \
            f"___nao pedirei os dados nem nada, pois se voce chegou aqui é porque já cadastrou sua empresa (matriz) e seu cliente.___\n\n" 
    client += f"***Selecione o cliente:***\n"
    for i, cliente in enumerate(clientes_list):
        client += f"***{i + 1}*** - `{formatar_cnpj_cpf(cliente['nome'], cliente['cnpj_cpf'])}`\n"

    update.message.reply_text(
        client,
        reply_markup=reply_markup,  parse_mode=telegram.ParseMode.MARKDOWN
    )

    return SELECIONAR_CLIENTE

def receber_cliente(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    cliente_index = (int(query.data.split("_")[1]) -1)
    context.user_data["cliente_index"] = cliente_index

    query.edit_message_text(f"Cliente selecionado: {context.user_data['clientes'][cliente_index]['nome']}")
    query.message.reply_text("✍ ***Envie uma mensagem para o orçamento***\nOu digite /cancelar para cancelar.", parse_mode=telegram.ParseMode.MARKDOWN)

    return RECEBER_MENSAGEM

def receber_mensagem(update: Update, context: CallbackContext) -> int:
    mensagem = update.message.text

    # Verificar se a chave "orcamento_mensagem" já existe no user_data
    # Se não existir, criar a chave e inicializar a lista de mensagens
    if "orcamento_mensagem" not in context.user_data:
        context.user_data["orcamento_mensagem"] = []
    
    # Verificar se a chave "contador_mensagem" já existe no user_data
    # Se não existir, criar a chave e inicializar o contador com 0
    if "contador_mensagem" not in context.user_data:
        context.user_data["contador_mensagem"] = 0

    # Incrementar o contador de mensagens
    context.user_data["contador_mensagem"] += 1

    # Adicionar a mensagem atual à lista de mensagens
    context.user_data["orcamento_mensagem"].append({"messa_id": context.user_data["contador_mensagem"], "texto": mensagem.strip()})


    # Teclado para escolher as opções
    keyboard = [
        [InlineKeyboardButton("Inserir nova mensagem", callback_data="inserir_linha")],
        [InlineKeyboardButton("Proximo", callback_data="concluir")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        f"Inserir mais uma mensagem ou ir para proxima?\nO que deseja fazer?",
        reply_markup=reply_markup,
    )

    return ADICIONAR_LINHA

def adicionar_linha(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    data = query.data
    if data == "concluir":
        query.edit_message_text("💰 ***Envie o valor total do orçamento:*** 💰\n (ex: 1250,50)", parse_mode=telegram.ParseMode.MARKDOWN)
        return RECEBER_VALOR_TOTAL
    elif data == "inserir_linha":
        query.edit_message_text("✍ ***Envie a próxima linha do orçamento:***", parse_mode=telegram.ParseMode.MARKDOWN)
        return RECEBER_MENSAGEM

def converter_valor_total(valor_texto):
    # Defina a localização para o Brasil (ou qualquer outra localização que desejar)
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    
    # Remova todos os caracteres que não sejam dígitos, vírgula e ponto
    valor_formatado = ''.join(c for c in valor_texto if c.isdigit() or c in [',', '.'])
    
    # Verifique se o separador decimal é uma vírgula e substitua por ponto, se necessário
    if ',' in valor_formatado and '.' not in valor_formatado:
        valor_formatado = valor_formatado.replace(',', '.')
    
    # Converta o valor para um número usando a localização definida
    valor_numerico = locale.atof(valor_formatado)
    
    # Arredonde o valor para duas casas decimais
    valor_arredondado = round(valor_numerico, 2)
    
    return valor_arredondado

def receber_valor_total(update: Update, context: CallbackContext) -> int:
    valor_total = update.message.text
    context.user_data["valor_total"] = converter_valor_total(valor_total)

    # Teclado para escolher as opções
    keyboard = [
        [InlineKeyboardButton("Sim", callback_data="sim"), InlineKeyboardButton("Não", callback_data="nao")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        "Deseja colocar observação: (Sim/Não)",
        reply_markup=reply_markup,
    )
    return RECEBER_OBSERVACAO_TEXTO

def adicionar_observacao(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    data = query.data
    try:
        keyboard = [
            [InlineKeyboardButton("Sim", callback_data="sim"), InlineKeyboardButton("Não", callback_data="nao")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if data == "sim":
            query.edit_message_text("Envie a observação:")
            return RECEBER_OBSERVACAO
        elif data == "nao":
            query.edit_message_text("OK, colocaremos padrao (Obrigado pela preferencia.)")
            context.user_data["observacao"] = "Obrigado pela preferencia!"
            receber_observacao(query, context)
        
    except (ValueError, IndexError):
        query.edit_message_text("Opção inválida. Por favor, selecione uma opção válida. (Sim/Não)",
        reply_markup=reply_markup)
        return RECEBER_OBSERVACAO_TEXTO

def receber_observacao(update: Update, context: CallbackContext) -> int:
    observacao = update.message.text
    orcamento_data = context.user_data
    if orcamento_data.get("observacao") != "Obrigado pela preferencia!":
        context.user_data["observacao"] = observacao

    # Agora você tem todas as informações do orçamento no context.user_data
    # Pode processar e gerar o orçamento conforme necessário.

    # Adicionar a data e hora atual aos dados do orçamento
    context.user_data.pop("clientes", None) # remove o item clientes que é inserido no inicio para informações.
    data_hora_atual = datetime.now().strftime("%d/%m/%Y")
    context.user_data["data_emissao"] = data_hora_atual
    # Defina a data de vencimento aqui, estou usando 10 dias após a data de emissão como exemplo
    data_vencimento = (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y")
    context.user_data["data_vencimento"] = data_vencimento

    # Salvar os dados do orçamento em um arquivo JSON
    user_id = update.message.chat_id
    orcamento_number = context.user_data.get("numero_orcamento", obter_ultimo_numero_orcamento(user_id))
    orcamento_json_path = salvar_orcamento_json(user_id, context.user_data)
    
    update.message.reply_text("Orçamento salvo com sucesso!")
    message = update.message.reply_text("Gerando o arquivo PDF, Aguarde....")
    # Obter o diretório atual do script Python


    user_folder_path = f"user_data/{user_id}/orçamentos"

    tem_foto = load_image_log()[str(user_id)].get("image") # SE TIVER FOTO RETORNA TRUE
    if tem_foto:
        #    layout tem que ter o nome -> planilha_foto.xlsx na pasta layout_excel/
        user_id = str(user_id)
        nome_pdf = f"Orçamento - {orcamento_number}.pdf"
        data = context.user_data
        current_directorywa = inserir_imagem_excel(user_id, nome_pdf, data)
        if not os.path.exists(user_folder_path):
            try:
                # Criar a pasta "orçamentos"
                os.makedirs(user_folder_path)
            except Exception as e:
                print("Erro ao criar a pasta 'orçamentos':", e)
        
        
    else:
        # LAYOUT SEM FOTO
        current_directorywa = caminho_salvar_pdf(user_id, f"Orçamento - {orcamento_number}.pdf")
        
        # Verificar se a pasta "orçamentos" já existe
        if not os.path.exists(user_folder_path):
            try:
                # Criar a pasta "orçamentos"
                os.makedirs(user_folder_path)
            except Exception as e:
                print("Erro ao criar a pasta 'orçamentos':", e)
        preencher_dados_excel(context.user_data, current_directorywa)

        # Verificar se o arquivo PDF foi gerado corretamente
    pdf_file_path = current_directorywa  # Caminho completo para o arquivo PDF gerado
    if os.path.exists(pdf_file_path):
        context.bot.delete_message(chat_id=user_id, message_id=message.message_id)
        update.message.reply_text("Gerando com sucesso!. ✅")
        context.bot.send_document(chat_id=user_id, document=open(pdf_file_path, 'rb'))
        os.remove(pdf_file_path)
    else:
        context.bot.delete_message(chat_id=user_id, message_id=message.message_id)
        update.message.reply_text("Houve um problema na geração do PDF. Por favor, tente novamente mais tarde.")

    return ConversationHandler.END


def salvar_orcamento_json(user_id, orcamento_data):
    orcamento_number = orcamento_data.get("numero_orcamento", obter_ultimo_numero_orcamento(user_id))
    orcamento_data["numero_orcamento"] = orcamento_number

    # Obter os dados da matriz e do cliente selecionado
    user_info = ler_informacoes_usuario(user_id)
    cliente_index = orcamento_data.get("cliente_index", 0)
    matriz = user_info.get("cadastros", [])
    cliente_selecionado = user_info.get("cadastros", [])[cliente_index]

    for cadastro in matriz:
        if cadastro.get("tipo") == "matriz":
            matriz = cadastro
            break
    else:
        matriz = {}  # Caso não encontre a matriz, retorna um dicionário vazio

    orcamento_data["matriz"] = matriz
    orcamento_data["cliente"] = cliente_selecionado

    orcamento_json_path = f"user_data/{user_id}/orçamentos/orcamento_{orcamento_number}.json"
    with open(orcamento_json_path, "w", encoding="utf-8") as orcamento_json_file:
        json.dump(orcamento_data, orcamento_json_file, indent=4, ensure_ascii=False)
    
    
    consumir_credito(user_id)
    return orcamento_json_path



def obter_ultimo_numero_orcamento(user_id):
    user_folder_path = f"user_data/{user_id}/orçamentos/"
    if not os.path.exists(user_folder_path):
        os.makedirs(user_folder_path)

    orcamento_numbers = [int(f.split("_")[1].split(".")[0]) for f in os.listdir(user_folder_path) if f.startswith("orcamento_")]
    return max(orcamento_numbers, default=0) + 1


def cancelar_orcamento(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("O orçamento foi cancelado.")
    return ConversationHandler.END