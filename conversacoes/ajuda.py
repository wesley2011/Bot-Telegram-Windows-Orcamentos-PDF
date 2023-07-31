import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, CallbackContext

# Constants for conversation states
MENU_2, AJUDA_2, CADASTRAMENTO_2, LISTAR_CADASTROS_2, REMOVER_CADASTROS_2, GERAR_ORCAMENTOS_2, IMPORTAR_LOGOTIPO_2, SAIR_2, MENU3 = range(9)

# Helper function to display the main menu
def menu_ajuda(update: Update, _: CallbackContext) -> int:
    
    keyboard = [
        [
            InlineKeyboardButton("Cadastramento", callback_data=str(CADASTRAMENTO_2))
        ],
        [
            InlineKeyboardButton("Listar Cadastros", callback_data=str(LISTAR_CADASTROS_2)),
            InlineKeyboardButton("Remover Cadastros", callback_data=str(REMOVER_CADASTROS_2)),
        ],
        [
            InlineKeyboardButton("Gerar Orçamentos", callback_data=str(GERAR_ORCAMENTOS_2)),
            InlineKeyboardButton("Importar Logotipo", callback_data=str(IMPORTAR_LOGOTIPO_2)),
        ],
        [
            InlineKeyboardButton("Sair", callback_data=str(SAIR_2)),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    global id_mes
    id_mes = update.message.reply_text("Selecione uma opção:", reply_markup=reply_markup)
    return MENU_2


# Helper function to go back to the main menu
def voltar(update: Update, _: CallbackContext) -> int:
    return menu_ajuda(update, _)

# Handler for handling button presses
def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    global id_mes
    # Determine which button was pressed
    option = int(query.data)

    if option == AJUDA_2:
        query.edit_message_text("Mais informações, erros, sujestões abra chamado no @suporteorcamentobot")
        return ConversationHandler.END
    elif option == CADASTRAMENTO_2:
        message = f"""
**Instruções de Uso:**

1. Para iniciar o cadastro, escolha "Cadastrar Cliente" ou "Cadastrar Matriz" no menu inicial.

2. Digite o CPF ou CNPJ para dar início ao cadastro. Caso seja um CNPJ válido, o bot preencherá automaticamente informações adicionais.

3. Preencha os demais campos solicitados pelo bot até que todos os campos obrigatórios estejam preenchidos.

4. Caso deseje editar alguma informação do cadastro, o bot apresentará os campos editáveis numerados. Selecione o número do campo que deseja modificar.

5. Após preencher todos os campos obrigatórios ou quando estiver satisfeito com as edições, selecione "Finalizar" para salvar o cadastro.

6. O cadastro será salvo e concluída com sucesso.

7. A qualquer momento, você pode selecionar "Cancelar" para interromper a operação em andamento e apagar o progresso feito no cadastro.
        """
    elif option == MENU_2:
        id_mes = query.edit_message_text("Voltando..")
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=id_mes.message_id)
        return menu_ajuda(query, context)
    elif option == LISTAR_CADASTROS_2:
        message = f"""
1. Passo a Passo:

 • Digite /listar.
 • O bot apresentará as opções disponíveis para a listagem:
 • 📒 Cliente: Para listar os cadastros de clientes.
 • 🏭 Matriz: Para listar os cadastros de matrizes.
 • Selecione a opção desejada para visualizar os respectivos cadastros.
2. Observações:
Caso não haja cadastros disponíveis para o tipo selecionado (cliente ou matriz), o bot informará que nenhum cadastro foi encontrado.

3. Contato e Suporte:
Se precisar de ajuda ou tiver alguma dúvida, entre em contato conosco: @suportelistagembot.
        """
        
    elif option == REMOVER_CADASTROS_2:
        message = f"""
1. O bot apresenta uma lista de opções para o usuário escolher entre "Cliente" e "Matriz".

2. O usuário escolhe o tipo de cadastro que deseja remover.

3. O bot lista os cadastros do tipo escolhido pelo usuário e apresenta um número ao lado de cada cadastro.

4. O usuário seleciona o número do cadastro que deseja excluir.

5. O bot confirma a exclusão do cadastro e realiza a remoção dos dados do arquivo JSON.

6. O bot exibe uma mensagem indicando que o cadastro foi removido com sucesso.

7. Caso o usuário decida cancelar a operação, ele pode selecionar a opção "Cancelar" a qualquer momento durante o processo.

Se o usuário escolher um tipo de cadastro que não possui registros, o bot informará que não há cadastros do tipo escolhido para serem removidos.

Se o usuário selecionar um número de cadastro inválido, o bot informará que a escolha é inválida e o processo será encerrado.
        """

    elif option == GERAR_ORCAMENTOS_2:
        message = f"""
1. Escolha o cliente para o qual deseja gerar o orçamento.

2. Envie as mensagens que deseja incluir no orçamento.

3. Envie o valor total do orçamento.

4. Opcionalmente, adicione uma observação ao orçamento.

O bot criará o arquivo PDF do orçamento e o enviará a você.
Se tiver alguma dúvida ou precisar de ajuda, contate-nos no suporte: @suporteorcamentobot.
        """

    elif option == IMPORTAR_LOGOTIPO_2:
        message = f"""
1. Opções do Menu:
 • Enviar Foto: Envia uma foto ao bot.
 • Ver Foto: Exibe a foto enviada anteriormente (se houver).
 • Excluir Foto: Remove a foto enviada (se houver).

2. Instruções:
 • Selecione "Enviar Foto" e envie a foto.
 • Para ver a foto enviada, escolha "Ver Foto".
 • Para excluir a foto, selecione "Excluir Foto".

3. Limite de Tentativas:
 • Limite de 3 tentativas para enviar fotos.

Importante:
Fotos são armazenadas de forma segura.
O bot não compartilha suas fotos.
        """
    elif option == SAIR_2:
        query.edit_message_text("Saindo o menu ajuda.")
        return ConversationHandler.END

    # Offer a 'Voltar' button
    

    if id_mes:
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=id_mes.message_id)
    keyboard = [[InlineKeyboardButton("Voltar", callback_data=str(MENU_2)), InlineKeyboardButton("Sair", callback_data=str(SAIR_2))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text(message, parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=reply_markup)

    return MENU_2
