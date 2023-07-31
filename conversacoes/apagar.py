import json, telegram
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

from conversacoes.FunComplementar import (
    ler_informacoes_usuario
)



# Definindo estados de conversação EXCLUIR CLIENTE OU MATRIX
ESCOLHER_TIPO, LISTAR_CADASTROS, EXCLUIR_CADASTRO = range(3)


def funcao_auxiliar_excluir_cadastro(update: Update, context: CallbackContext) -> int:
    
    query = update.callback_query
    message = f"˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙\n"
    query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)

    # Redireciona o usuário para o comando /iniciar_orcamento
    context.bot.send_message(chat_id=query.message.chat_id, text=f"Aperte aqui 👉 /excluircad")

    # Retorna o estado atual para evitar problemas com o ConversationHandler
    return ConversationHandler.END

def iniciar_remocao(update: Update, context: CallbackContext) -> int:
    # Limpar qualquer conversação anterior
    context.user_data.pop("cadastros", None)
    context.user_data.pop("tipo_cadastro", None)
    
    # Contar o número de clientes e matrizes
    user_info = ler_informacoes_usuario(update.effective_user.id)
    clientes = sum(1 for cadastro in user_info.get("cadastros", []) if cadastro["tipo"] == "cliente")
    matrizes = sum(1 for cadastro in user_info.get("cadastros", []) if cadastro["tipo"] == "matriz")
    
    # Criar o teclado inline para escolher o tipo de cadastro a remover
    keyboard = [
        [InlineKeyboardButton(f"Cliente ({clientes})", callback_data="cliente")],
        [InlineKeyboardButton(f"Matriz ({matrizes})", callback_data="matriz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text("Escolha o tipo de cadastro que deseja remover:", reply_markup=reply_markup)
    return ESCOLHER_TIPO

def escolher_tipo(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    tipo_cadastro = query.data.lower()
    
    # Salvar o tipo de cadastro escolhido no contexto
    context.user_data["tipo_cadastro"] = tipo_cadastro
        # Verificar o conteúdo da lista cadastros_do_tipo

    # Listar os cadastros do tipo escolhido
    user_info = ler_informacoes_usuario(query.from_user.id)
    cadastros = user_info["cadastros"]
    cadastros_do_tipo = [cadastro for cadastro in cadastros if cadastro["tipo"] == tipo_cadastro]
    
    
    
    if not cadastros_do_tipo:
        query.message.edit_text(f"Não há {tipo_cadastro}s cadastrados para remover.")
        return ConversationHandler.END
    
    context.user_data["cadastros"] = cadastros_do_tipo
    
    # Criar o teclado inline para escolher o cadastro a remover
    keyboard = [
        [InlineKeyboardButton(f"{i+1} - {cadastro['cnpj_cpf']} - {cadastro['nome']}", callback_data=str(i))]
        for i, cadastro in enumerate(cadastros_do_tipo)
    ]
    keyboard.append([InlineKeyboardButton("Cancelar", callback_data="cancelar")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.message.edit_text(f"Selecione o {tipo_cadastro} que deseja remover:", reply_markup=reply_markup)
    return EXCLUIR_CADASTRO

def excluir_cadastro(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    if query.data == "cancelar":
        query.message.edit_text("A remoção de cadastro foi cancelada.")
        return ConversationHandler.END
    
    
    escolha = int(query.data)
    cadastros_do_tipo = context.user_data.get("cadastros")
    num_cadastros = len(cadastros_do_tipo)

    # Verificar se a escolha é um índice válido
    if num_cadastros == 1 and escolha == 0:
        # Caso matriz, remover o único cadastro
        cadastro_removido = cadastros_do_tipo.pop(0)
    elif 0 <= escolha < num_cadastros:
        # Caso cliente, remover o cadastro selecionado da lista
        cadastro_removido = cadastros_do_tipo.pop(escolha)
    else:
        # Tratar a escolha inválida, se necessário
        query.message.edit_text("Escolha inválida. Por favor, tente novamente.")
        return ConversationHandler.END

    # Atualizar a lista de cadastros no arquivo JSON
    user_id = query.from_user.id
    user_folder_path = f"user_data/{user_id}"
    user_info_file_path = f"{user_folder_path}/user_info.json"

    # Carregar as informações do usuário a partir do arquivo JSON
    with open(user_info_file_path, "r", encoding="utf-8") as user_info_file:
        user_info = json.load(user_info_file)

    # Remover o cadastro do arquivo JSON
    user_info["cadastros"] = [cadastro for cadastro in user_info["cadastros"] if cadastro != cadastro_removido]

    # Salvar as informações atualizadas no arquivo JSON
    with open(user_info_file_path, "w", encoding="utf-8") as user_info_file:
        json.dump(user_info, user_info_file, indent=4, ensure_ascii=False)

    # Mostrar o CNPJ/CPF e nome do cadastro excluído
    query.message.edit_text(f"***O cadastro abaixo foi removido.*** 🗑\n`{cadastro_removido['cnpj_cpf']}` - `{cadastro_removido['nome']}`", parse_mode=telegram.ParseMode.MARKDOWN)


    return ConversationHandler.END