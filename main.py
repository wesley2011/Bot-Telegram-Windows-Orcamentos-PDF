import logging, threading, json, os, telegram
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
)
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    ParseMode,
    Bot,
)


from conversacoes.cadastro import (
    menu, cadastrar_start, listar_cadastros, verificar_cnpj_cpf, select_cadastro, editing_field, cadastrar_field,
    preencher_campo, resposta_listar_cadastro, inline_button_handler, cancel, funcao_auxiliar_logo,
    SELECTING_OPTION, CADASTRO, SELECTING_CADASTRO, EDITING_FIELD, SELECTING_OPTION_EDITING,SELECTING_OPTION_EDITING_S, 
    AGUARDAR_RESPOSTA
)

from conversacoes.gerencia import (
    listar_usuarios, selecionar_usuario, selecionar_opcao, quantidade_creditos,
    quantidade_dias, cancelar_adicao_creditos, funcao_auxiliar_add_credito, 
    SELECIONAR_USUARIO, SELECIONAR_OPCAO, QUANTIDADE_CREDITOS, QUANTIDADE_DIAS
)

from conversacoes.orcamento import (
    iniciar_orcamento, receber_cliente, receber_mensagem, adicionar_linha,
    receber_valor_total, adicionar_observacao, receber_observacao, cancelar_orcamento, funcao_auxiliar_orçamento,
    SELECIONAR_CLIENTE, RECEBER_MENSAGEM, RECEBER_VALOR_TOTAL, RECEBER_OBSERVACAO,
    ADICIONAR_LINHA, RECEBER_OBSERVACAO_TEXTO
)

from conversacoes.apagar import (
    iniciar_remocao, escolher_tipo, excluir_cadastro, funcao_auxiliar_excluir_cadastro,
    ESCOLHER_TIPO, EXCLUIR_CADASTRO
)

from conversacoes.cadastroVencido import (
    verificar_cadastros_vencidos
)

from conversacoes.receber_foto import (
    opcao_selecionada, menu_image, confirmar_foto, excluir_foto,cancel_conversa,
    CONFIRMANDO_FOTO, SOLICITANDO_FOTO, EXIBINDO_OPCOES, AGUARDANDO_RESPOSTA, SELECTING_OPTIONS 
)

from conversacoes.ajuda import menu_ajuda, button

TOKEN_FILE = "conversacoes/token_bot/token.txt"  # Arquivo contendo o token do bot
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def start_bot(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name
    username = user.username
    date = update.message.date.strftime('%d/%m/%Y')
    # Ativa a flag para indicar que existe uma conversa em andamento
 
    # Criar a pasta com o ID do usuário
    user_folder_path = f"user_data/{user_id}"
    user_info_file_path = f"{user_folder_path}/user_info.json"
    # Verificar se o usuário já deu o /start antes
    if os.path.exists(user_folder_path):
        with open(user_info_file_path, "r") as user_info_file:
            user_info = json.load(user_info_file)
            creditos = user_info.get("creditos", 0)  # Obter o número de créditos disponíveis
            nome = user_info.get("first_name")
            mensal = user_info.get("mensal", False)  # Verificar se é usuário mensal
            message = f"Olá {nome}, Bem vindo de volta.🙂\n"
            if mensal:  # Usuário mensal
                # Obter a data inicial da assinatura mensal do usuário (se existir)
                mensalidade_info = user_info.get("mensalidade", [])
                if mensalidade_info[0]["status"]:
                    dias_de_uso = mensalidade_info[0]["dias"]
                    message += f"🫵 Você é um usuário mensal, Resta {dias_de_uso} dia. 😎"
                else:
                    message += "Você é um usuário mensal, mas ainda não tem uma assinatura ativa. 😭"
            else:  # Usuário com créditos
                message += f"Você possue [ {creditos} ] créditos.\n\n"
        
        message += f"Aperte o comando 👉 /listar 👈 para que eu te mande os comandos disponiveis.\n"
    else:
        os.makedirs(user_folder_path, exist_ok=True)

        # Salvar as informações do usuário em um arquivo JSON
        user_info = {
            "id": user_id,
            "first_name": first_name,
            "username": username,
            "date": date,
            "cadastros": [],
            "creditos": 5,
            "mensal": False,  # Definir como False por padrão, indicando que é usuário com créditos
            "mensalidade": []
        }

        with open(user_info_file_path, "w", encoding="utf-8") as user_info_file:
            json.dump(user_info, user_info_file, ensure_ascii=False, indent=4)

        message = f"Olá! Bem-vindo ao 🤖 de orçamentos.\n"
        message += f"\n"
        message += f"Como este é o seu primeiro acesso, darei gratuitamente 5⃣ créditos para você testar.\n"
        message += f"E gostando do meu serviço, tenho dois tipos de planos, vou listar abaixo para você:\n"
        message += f"━━━━━━━ ● ━━━━━━━\n"
        message += f"***Crédito:*** Cada cadastro de cliente, matriz ou geração de orçamento, irá descontar 1 crédito do seu perfil.\n"
        message += f"└ • *Observação:* ___A exclusão de cadastro já finalizado não devolverá o crédito consumido.___\n"
        message += f"\n"
        message += f"***Mensal:*** Ao obter o plano mensal, você pode cadastrar varios clientes, gerar orçamentos até a data de vencimento. " \
                    "Após o vencimento, os recursos de cadastrar cliente e gerar orçamento não serão possíveis.\n"
        message += f"━━━━━━━ ● ━━━━━━━\n"
        message += f"E se estiver no plano mensal e quiser alternar para o plano de crédito ou renovar a mensalidade, é só falar com o suporte. @suporteorcamentobot\n"
        message += f"Nossos layouts de orçamentos têm dois formatos: um para o caso da sua empresa não ter logotipo, e outro para a sua empresa que tem logotipo. " \
                    "Caso tenha logotipo inserido no menu 'logo', quando gerar o orçamento, o sistema identifica qual o seu tipo de layout e gera em PDF.\n"
        message += f"\n\n"
        message += f"Para mais ajuda, vá ao menu /ajuda que explicarei mais sobre como me usar.\n"
        message += f"\n"
        message += f"Aperte o comando 👉 /listar 👈 para que eu te mande os comandos disponiveis.\n"

    update.message.reply_text(message, parse_mode=telegram.ParseMode.MARKDOWN)


def listar_comandos(update: Update, context: CallbackContext):
    message = f"Comandos disponíveis:\n\n"
    message += f"/menu - Cadastro de Cliente, Cadastro de Matriz, Listar Cadastros.\n"
    message += f"\n"
    message += f"/logo - Armazena logo, vê a logo e a exclui.\n"
    message += f"\n"
    message += f"/excluircad - Exclui cadastros já finalizados, cliente ou matriz.\n"
    message += f"\n"
    message += f"/orcamento - Gera orçamento para seu cliente em PDF.\n"
    message += f"\n"
    message += f"/planos - Veja nossos planos.\n"
    message += f"\n"
    message += f"/ajuda - ajuda de como usar os comandos.\n"
    message += f"\n"
    message += f"/admin - Somente o suporte tem acesso.\n"
    message += f"\n"
    update.message.reply_text(message, parse_mode=telegram.ParseMode.MARKDOWN)

def listar_planos(update: Update, context: CallbackContext):
    user = update.effective_user
    first_name = user.first_name
    message = f"""Olá! 👋 {first_name} Seja bem-vindo

*🤖 Conheça nossos Planos 🤖*


*Plano de 10 Créditos - R$ 5,00*
• Cadastre até 10 clientes ou matrizes 📋
• Gere até 10 orçamentos em PDF 📄
• Ideal para quem precisa de uma pequena quantidade de créditos

*Plano de 30 Créditos - R$ 15,00*
• Cadastre até 30 clientes ou matrizes 📋
• Gere até 30 orçamentos em PDF 📄
• Ótima opção para uso moderado dos recursos

*Plano de 80 Créditos - R$ 40,00*
• Cadastre até 80 clientes ou matrizes 📋
• Gere até 80 orçamentos em PDF 📄
• Perfeito para quem precisa de uma grande quantidade de créditos

*Plano Mensal - R$ 30,00*
• Acesso ilimitado durante o mês 📆
• Cadastre quantos clientes e matrizes desejar 📋
• Gere orçamentos em PDF à vontade 📄
• Exclusivo para assinantes mensais

🎁 *Bônus de Boas-vindas:* Ao assinar o Plano Mensal, você ganha 5 créditos gratuitos para testar nossos serviços! 🆓

🚀 *Economize e Simplifique!* Escolha o plano que melhor atende às suas necessidades e tenha mais praticidade na gestão de seus cadastros e orçamentos. Assine agora mesmo e aproveite todas as funcionalidades do nosso 🤖 de orçamentos.

📩 *Contate-nos:* Em caso de dúvidas ou suporte, estamos à disposição para ajudar. Basta enviar uma mensagem para o suporte no menu /ajuda.

📝 *Observações:* O valor por cada crédito é de R$ 0,50. Os créditos são consumidos ao realizar cadastros de cliente ou gerar orçamentos em PDF no plano de créditos. Já no Plano Mensal, você tem acesso ilimitado aos recursos durante o período de vigência da assinatura. Não perca essa oportunidade, assine agora mesmo! 🎉

"""

    update.message.reply_text(message, parse_mode=telegram.ParseMode.MARKDOWN)

    


def main():
    # Leitura do token do bot a partir do arquivo "token.txt"
    with open(TOKEN_FILE, "r") as file:
        token = file.read().strip()
        # Remove o prefixo "token=" do valor lido
        token = token.replace("token=", "")


    bot = Bot(token)

    # Obtenha as informações do bot usando o método getMe()
    bot_info = bot.get_me()

    # Extraia o username do bot do objeto bot_info
    bot_username = bot_info.username

    print("Bote ligado: ", bot_username)

    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    ation_handler = ConversationHandler(
    entry_points=[CommandHandler("ajuda", menu_ajuda)],
    states={},
    fallbacks=[CallbackQueryHandler(button)],
    )
    dp.add_handler(ation_handler)
    #dp.add_handler(CommandHandler("ajuda", menu_ajuda))
    #dp.add_handler(CallbackQueryHandler(button))


    dp.add_handler(CommandHandler("start", start_bot))
    dp.add_handler(CommandHandler("listar", listar_comandos))
    dp.add_handler(CommandHandler("planos",listar_planos))

    # Definindo os estados para o fluxo de conversa
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("menu", menu)],
        states={
            SELECTING_OPTION: [
                CallbackQueryHandler(cadastrar_start, pattern="^(cliente|matriz|cancelar)$"),
                CallbackQueryHandler(listar_cadastros, pattern="^(listar)$"),
                CallbackQueryHandler(funcao_auxiliar_orçamento, pattern="^(orçamento)$"),
                CallbackQueryHandler(funcao_auxiliar_add_credito, pattern="^(adm)$"),
                CallbackQueryHandler(funcao_auxiliar_excluir_cadastro, pattern="^(excluir_cadastro)$"),
                CallbackQueryHandler(funcao_auxiliar_logo, pattern="^(adicionar_logo)$")
            ],
            CADASTRO: [MessageHandler(Filters.text & ~Filters.command, verificar_cnpj_cpf)],
            SELECTING_CADASTRO: [MessageHandler(Filters.text & ~Filters.command, select_cadastro)],
            EDITING_FIELD: [MessageHandler(Filters.text & ~Filters.command, editing_field)],
            SELECTING_OPTION_EDITING: [MessageHandler(Filters.text & ~Filters.command, cadastrar_field)],
            SELECTING_OPTION_EDITING_S: [MessageHandler(Filters.text & ~Filters.command, preencher_campo)], 
            AGUARDAR_RESPOSTA: [CallbackQueryHandler(resposta_listar_cadastro, pattern="^(clientes|matrizs)$")],
        },
        fallbacks=[
            CommandHandler("cancelar", cancel),
            CallbackQueryHandler(inline_button_handler, pattern="^(finalizar)$"),
            CallbackQueryHandler(inline_button_handler, pattern="^(cancelar)$")
        ]
    )

    conversa_credito = ConversationHandler(
        entry_points=[CommandHandler('admin', listar_usuarios)],
        states={
            SELECIONAR_USUARIO: [CallbackQueryHandler(selecionar_usuario)],
            SELECIONAR_OPCAO: [CallbackQueryHandler(selecionar_opcao)],
            QUANTIDADE_CREDITOS: [MessageHandler(Filters.text & ~Filters.command, quantidade_creditos)],
            QUANTIDADE_DIAS: [MessageHandler(Filters.text & ~Filters.command, quantidade_dias)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar_adicao_creditos)]
    )

    # Crie a lista de handlers do ConversationHandler
    conv_handlers = ConversationHandler(
        entry_points=[CommandHandler('orcamento', iniciar_orcamento)],
        states={
            SELECIONAR_CLIENTE: [CallbackQueryHandler(receber_cliente)],
            RECEBER_MENSAGEM: [MessageHandler(Filters.text & ~Filters.command, receber_mensagem)],
            ADICIONAR_LINHA: [CallbackQueryHandler(adicionar_linha)],
            RECEBER_VALOR_TOTAL: [MessageHandler(Filters.text & ~Filters.command, receber_valor_total)],
            RECEBER_OBSERVACAO_TEXTO: [CallbackQueryHandler(adicionar_observacao, pattern='^(sim|nao)$')],
            RECEBER_OBSERVACAO: [MessageHandler(Filters.text & ~Filters.command,receber_observacao)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar_orcamento)],
    )

    # Criando o ConversationHandler
    remover_cadastro_handler = ConversationHandler(
        entry_points=[CommandHandler('excluircad', iniciar_remocao)],
        states={
            ESCOLHER_TIPO: [CallbackQueryHandler(escolher_tipo)],
            EXCLUIR_CADASTRO: [CallbackQueryHandler(excluir_cadastro)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar_orcamento)],
    )


    # Criando o ConversationHandler
    conv_handlerss = ConversationHandler(
        entry_points=[CommandHandler("logo", menu_image)],
        states={
            SELECTING_OPTIONS: [CallbackQueryHandler(opcao_selecionada)],
            CONFIRMANDO_FOTO: [MessageHandler(Filters.photo & ~Filters.command, confirmar_foto)],
            AGUARDANDO_RESPOSTA: [CallbackQueryHandler(excluir_foto)],
        },
        fallbacks=[CommandHandler("cancelar", cancel_conversa)],
    )

    # Adicione o handler do ConversationHandler ao dispatcher
 
    dp.add_handler(conv_handlerss)
    dp.add_handler(remover_cadastro_handler)
    dp.add_handler(conv_handlers)
    dp.add_handler(conversa_credito)
    dp.add_handler(conversation_handler)
    #dp.add_handler(CallbackQueryHandler(inline_button_handler))
    # Handler para listar os cadastros

    # Iniciar o bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    # Iniciar a verificação de cadastros vencidos em uma thread separada
    thread_verificacao = threading.Thread(target=verificar_cadastros_vencidos)
    thread_verificacao.daemon = True
    thread_verificacao.start()

    main()
    while True:
        pass