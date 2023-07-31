import os
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters

# Constantes para os estados da conversação
CONFIRMANDO_FOTO, SOLICITANDO_FOTO, EXIBINDO_OPCOES, AGUARDANDO_RESPOSTA, SELECTING_OPTIONS = range(5)

# Pasta para armazenar as fotos enviadas pelos usuários
USER_DATA_FOLDER = "user_data"
LOG_IMAGE = "Controle_Notificacoes/image_log.json"


# "Controle_Notificacoes/image_log.json"
#

# Função para carregar o log de imagens
def load_image_log():
    if not os.path.exists(LOG_IMAGE):
        return {}
    with open(LOG_IMAGE, "r") as file:
        return json.load(file)

# Função para salvar o log de imagens
def save_image_log(image_log):
    with open(LOG_IMAGE, "w", encoding="utf-8") as file:
        json.dump(image_log, file, ensure_ascii=False, indent=4)

# Função para solicitar foto
def solicitar_foto(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    attempts = context.user_data.get("attempts", 0)

    if attempts >= 3:
        update.callback_query.answer("Você excedeu o número máximo de tentativas.")
        return cancel_conversa(update, context)

    update.callback_query.answer()
    update.callback_query.edit_message_text("Por favor, envie uma foto para que eu possa armazená-la.")
    context.user_data["attempts"] = attempts + 1
    return CONFIRMANDO_FOTO

# Função para confirmar foto
def confirmar_foto(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    file_id = update.message.photo[-1].file_id
    file = context.bot.get_file(file_id)
    folder_path = os.path.join(USER_DATA_FOLDER, str(user_id))

    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{user_id}.jpg")
    file.download(file_path)

    caminho_image = file_path

    image_log = load_image_log()
    image_log[str(user_id)] = {
        "image": True,
        "path": caminho_image
    }
    save_image_log(image_log)

    update.message.reply_text("Foto armazenada com sucesso!")
    context.user_data["attempts"] = 0
    return ConversationHandler.END

# Função para exibir foto
def exibir_foto(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    folder_path = os.path.join(USER_DATA_FOLDER, str(user_id))
    file_path = os.path.join(folder_path, f"{user_id}.jpg")

    if not os.path.exists(file_path):
        update.callback_query.answer()
        update.callback_query.edit_message_text("Você ainda não enviou nenhuma foto.")
        return ConversationHandler.END

    update.callback_query.answer()
    update.callback_query.message.reply_photo(photo=open(file_path, "rb"))

# Função para excluir foto
def excluir_foto(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    folder_path = os.path.join(USER_DATA_FOLDER, str(user_id))
    file_path = os.path.join(folder_path, f"{user_id}.jpg")

    if not os.path.exists(file_path):
        update.callback_query.answer()
        update.callback_query.edit_message_text("Você ainda não enviou nenhuma foto.")
        return ConversationHandler.END

    os.remove(file_path)

    image_log = load_image_log()
    image_log[str(user_id)] = {
        "image": False,
        "path": None
    }
    save_image_log(image_log)

    update.callback_query.answer()
    update.callback_query.edit_message_text("Foto excluída com sucesso!")

# Função para exibir o menu
def menu_image(update: Update, context: CallbackContext) -> int:
    # Limpar os dados do usuário para iniciar uma nova conversa
    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton("Enviar Foto", callback_data=str(SOLICITANDO_FOTO))],
        [InlineKeyboardButton("Ver Foto", callback_data=str(EXIBINDO_OPCOES))],
        [InlineKeyboardButton("Excluir Foto", callback_data=str(AGUARDANDO_RESPOSTA))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Selecione uma opção:", reply_markup=reply_markup)
    return SELECTING_OPTIONS

# Função para lidar com o menu selecionado
def opcao_selecionada(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    option = query.data
    if option == SOLICITANDO_FOTO:
        return solicitar_foto(update, context)
    elif option == EXIBINDO_OPCOES:
        return exibir_foto(update, context)
    elif option == CONFIRMANDO_FOTO:
        return confirmar_foto(update, context)
    elif option == AGUARDANDO_RESPOSTA:
        return excluir_foto(update, context)

# Função para cancelar a conversação
def cancel_conversa(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Operação cancelada.")
    return ConversationHandler.END

