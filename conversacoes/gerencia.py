import json, os, telegram
from datetime import timedelta
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


# Estado de conversação GERENCIA MAIS CREDITO E MENSALIDADE.
SELECIONAR_USUARIO, SELECIONAR_OPCAO, QUANTIDADE_CREDITOS, QUANTIDADE_DIAS = range(4)


def funcao_auxiliar_add_credito(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    message = f"˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙\n"
    query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)

    # Redireciona o usuário para o comando /iniciar_orcamento
    context.bot.send_message(chat_id=query.message.chat_id, text=f"Aperte aqui 👉 /admin")

    # Retorna o estado atual para evitar problemas com o ConversationHandler
    return ConversationHandler.END

# Comando para listar os usuários disponíveis
def listar_usuarios(update: Update, context: CallbackContext):
    # Verificar se o usuário tem permissão para usar esta função
    if update.message.from_user.id != 381043536:
        update.message.reply_text("Desculpe, você não tem permissão para usar esta função. 🙈")
        return ConversationHandler.END

    # Carregar todos os IDs de usuário e seus nomes da pasta "user_data"
    usuarios = []
    user_folder = "user_data"
    for user_id in os.listdir(user_folder):
        user_id = int(user_id)
        user_info_file_path = os.path.join(user_folder, str(user_id), "user_info.json")
        if os.path.exists(user_info_file_path):
            with open(user_info_file_path, "r") as user_info_file:
                user_info = json.load(user_info_file)
                user_name = user_info.get("first_name")
                if user_name:
                    usuarios.append({"ID": user_id, "Nome": user_name})

    if not usuarios:
        update.message.reply_text("Nenhum usuário encontrado.")
        return ConversationHandler.END

    # Criar uma lista de botões inline para selecionar o usuário
    keyboard = [
        [
            InlineKeyboardButton(f"{x + 1}", callback_data=str(usuario['ID']))
            for x, usuario in enumerate(usuarios)
        ],
        [InlineKeyboardButton("Cancelar", callback_data="cancelar")],
    ]

    # Criar uma lista de usuários formatada com ID e nome para enviar na mensagem
    usuarios_list = "\n".join(
        [
            f"***{x + 1} - ID:*** `{usuario['ID']}` ***- Nome:*** `{usuario['Nome']}`"
            for x, usuario in enumerate(usuarios)
        ]
    )
    update.message.reply_text(
        f"Usuários disponíveis:\n{usuarios_list}\n\nSelecione o usuário para adicionar créditos ou escolha 'Cancelar' para encerrar a operação.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=telegram.ParseMode.MARKDOWN,
    )

    # Avançar para o estado de seleção de usuário
    return SELECIONAR_USUARIO

# Função para tratar a seleção do usuário pelos botões inline
def selecionar_usuario(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.data

    # Verificar se o usuário selecionou a opção "Cancelar"
    if user_id == "cancelar":
        query.message.reply_text("Você cancelou a operação.")
        return ConversationHandler.END

    # Salvar o ID do usuário selecionado para ser usado posteriormente
    context.user_data["user_id"] = int(user_id)

    query.message.reply_text(
        f"Você selecionou o usuário com ID: {user_id}.\n\nDeseja adicionar créditos ou assinar um plano mensal?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Adicionar Créditos", callback_data="creditos")],
            [InlineKeyboardButton("Assinar Plano Mensal", callback_data="mensal")],
            [InlineKeyboardButton("Cancelar", callback_data="cancelar")]
        ])
    )

    # Avançar para o estado de seleção de opção
    return SELECIONAR_OPCAO

# Função para tratar a seleção da opção (Adicionar Créditos ou Assinar Plano Mensal)
def selecionar_opcao(update: Update, context: CallbackContext):
    query = update.callback_query
    option = query.data

    # Salvar a opção selecionada para ser usada posteriormente
    context.user_data["option"] = option

    # Verificar se o usuário selecionou a opção "Cancelar"
    if option == "cancelar":
        query.message.reply_text("Você cancelou a operação.")
        return ConversationHandler.END

    if option == "creditos":
        query.message.reply_text("Digite a quantidade de créditos que deseja adicionar:")
        return QUANTIDADE_CREDITOS
    elif option == "mensal":
        query.message.reply_text("Digite a quantidade de dias para a assinatura mensal:")
        return QUANTIDADE_DIAS

# Função para tratar a quantidade de créditos a ser adicionada
def quantidade_creditos(update: Update, context: CallbackContext):
    try:
        quantidade_creditos = int(update.message.text)
        if quantidade_creditos <= 0:
            raise ValueError
    except ValueError:
        update.message.reply_text(
            "Quantidade de créditos inválida. Por favor, digite um número inteiro positivo."
        )
        return QUANTIDADE_CREDITOS

    user_id = context.user_data["user_id"]
    user_folder = "user_data"
    user_folder_path = os.path.join(user_folder, str(user_id))
    user_info_file_path = os.path.join(user_folder_path, "user_info.json")

    # Verificar se o usuário já existe no arquivo JSON
    if os.path.exists(user_info_file_path):
        with open(user_info_file_path, "r") as user_info_file:
            user_info = json.load(user_info_file)

            # Verificar se o usuário possui o plano mensal ativo
            is_mensal = user_info.get("mensal", False)
            if is_mensal:
                # Cancelar o plano mensal, pois o usuário está adicionando créditos
                user_info["mensal"] = False
                user_info["mensalidade"] = []

    # Adicionar créditos ao usuário
    user_info["creditos"] += quantidade_creditos

    # Atualizar o arquivo JSON do usuário
    with open(user_info_file_path, "w") as user_info_file:
        json.dump(user_info, user_info_file, ensure_ascii=False, indent=4)

    mensagem = (
        f"Olá ***{user_info['first_name']}***.\n"
        f"Foram adicionados ***{quantidade_creditos}*** créditos. Agora você tem um total de ***{user_info['creditos']}*** créditos.\n\n"
        f"Agora você pode voltar a usar."
    )

    # Enviar mensagem de notificação ao usuário
    update.message.reply_text(
        f"Foram adicionados {quantidade_creditos} créditos ao usuário com ID: {user_id}."
    )
    context.bot.send_message(user_id, mensagem, parse_mode=telegram.ParseMode.MARKDOWN)

    # Voltar ao estado inicial do ConversationHandler
    return ConversationHandler.END

# Função para tratar a quantidade de dias para a assinatura mensal
def quantidade_dias(update: Update, context: CallbackContext):
    try:
        quantidade_dias = int(update.message.text)
        if quantidade_dias <= 0:
            raise ValueError
    except ValueError:
        update.message.reply_text(
            "Quantidade de dias inválida. Por favor, digite um número inteiro positivo."
        )
        return QUANTIDADE_DIAS

    user_id = context.user_data["user_id"]
    user_folder = "user_data"
    user_folder_path = os.path.join(user_folder, str(user_id))
    user_info_file_path = os.path.join(user_folder_path, "user_info.json")

    # Verificar se o usuário já existe no arquivo JSON
    if os.path.exists(user_info_file_path):
        with open(user_info_file_path, "r") as user_info_file:
            user_info = json.load(user_info_file)

    # Ativar a assinatura mensal para o usuário
    dataini = update.message.date.strftime("%d/%m/%Y %H:%M")
    datafim = (update.message.date + timedelta(days=quantidade_dias)).strftime("%d/%m/%Y %H:%M")
    user_info["mensal"] = True
    user_info["mensalidade"] = [
        {
            "dias": quantidade_dias,
            "data_inicial": dataini,
            "data_final": datafim,
            "status": True,
        }
    ]

    log_file_path = "Controle_Notificacoes/notificacoes_log.json"
    if os.path.exists(log_file_path):
        with open(log_file_path, "r") as log_file:
            log_data = json.load(log_file)
        if str(user_id) in log_data:
            log_data[str(user_id)]["lembrete"] = False
            log_data[str(user_id)]["vencimento"] = False
            print("novo logdata", log_data)
            # Salvar o log de notificações atualizado
            with open(log_file_path, "w", encoding="utf-8") as log_file:
                json.dump(log_data, log_file, indent=4, ensure_ascii=False)

    # Atualizar o arquivo JSON do usuário
    with open(user_info_file_path, "w") as user_info_file:
        json.dump(user_info, user_info_file, ensure_ascii=False, indent=4)


    update.message.reply_text(
        f"Assinatura mensal ativada para o usuário com ID: {user_id}."
    )
    mensagem = f"Olá ***{user_info['first_name']}***.\n"
    mensagem += f"Sua Assinatura mensal foi ativada. ***{quantidade_dias}*** dias.\n" 
    mensagem += f"Data de inicio: `{dataini}`\nData de Vencimento: `{datafim}`\n\n" 
    mensagem += f"Agora você pode voltar a usar."

    context.bot.send_message(user_id, mensagem, parse_mode=telegram.ParseMode.MARKDOWN)

    return ConversationHandler.END

# Função para lidar com o comando de cancelar a adição de créditos
def cancelar_adicao_creditos(update: Update, context: CallbackContext):
    update.message.reply_text("A adição de créditos foi cancelada.")
    return ConversationHandler.END


# Função para verificar se o usuário possui créditos suficientes ou assinatura mensal ativa
def verificar_creditos(user_id):
    user_folder_path = f"user_data/{user_id}"
    user_folder_path = f"user_data/{user_id}"
    user_info_file_path = f"{user_folder_path}/user_info.json"

    with open(user_info_file_path, "r") as user_info_file:
        user_info = json.load(user_info_file)
        is_mensal = user_info.get("mensal", False)

    if is_mensal:
        mensalidade = user_info.get("mensalidade", [])
        if not mensalidade or not mensalidade[0].get("status", False):
            mensagem = f"Seu plano mensal está inativo. 🫣😭\nPor favor, entre em contato com o suporte. @suporteorcamentobot"
            return {"tipo": "mensal","mensagem": mensagem}
    else:
        creditos = user_info.get("creditos", 0)  # Obter o número de créditos disponíveis
        nome = user_info.get("first_name")
        if creditos == 0:
            mensagem = f"\n❌ - Sem crédito [ {creditos}]\n"
            mensagem += f"\n{nome}, Compre mais créditos com @suporteorcamentobot e volte a usar o bot. 🫣😭\n"
            return {"tipo": "credito","mensagem": mensagem}
    
    return None 
def consumir_credito(user_id):
    user_folder_path = f"user_data/{user_id}"
    user_info_file_path = f"{user_folder_path}/user_info.json"

    with open(user_info_file_path, "r") as user_info_file:
        user_info = json.load(user_info_file)
        is_mensal = user_info.get("mensal", False)

    # Verificar se o cadastro é feito por crédito
    if not is_mensal:
        # Consumir crédito apenas se não for mensal
        user_info["creditos"] -= 1
        with open(user_info_file_path, "w", encoding="utf-8") as user_info_file:
            json.dump(user_info, user_info_file, ensure_ascii=False, indent=4)

    return None
