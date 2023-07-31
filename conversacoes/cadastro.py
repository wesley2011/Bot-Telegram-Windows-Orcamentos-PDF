import json, requests, re, os, telegram
from datetime import datetime
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    ParseMode,
)
from telegram.ext import (
    ConversationHandler,
    CallbackContext,
)

from conversacoes.FunComplementar import (
    ler_informacoes_usuario
)
from conversacoes.gerencia import(
    verificar_creditos, consumir_credito
)
from conversacoes.FunComplementar import (
    ler_informacoes_usuario, formatar_cnpj_cpf_cep, formatar_telefone
)


# Estados para o fluxo de conversa CADASTRO DE CLIENTE E MATRIZ
SELECTING_OPTION, CADASTRO, SELECTING_CADASTRO, EDITING_FIELD, SELECTING_OPTION_EDITING,SELECTING_OPTION_EDITING_S, LISTAR_CADASTROS, AGUARDAR_RESPOSTA = range(8)
# Nomes dos botões
CANCEL = "Cancelar"

# Nome do arquivo JSON para salvar os cadastros
JSON_FILE = "cadastros.json"


# Campos do cadastro
CAMPOS_CADASTRO = [
    "nome",
    "cep",
    "endereco",
    "numero_endereco",
    "bairro",
    "complemento",
    "cidade",
    "estado",
    "telefone_contato",
    "email",
]


# Classe para representar a entidade Cliente/Matriz
class Cadastro:
    def __init__(self, tipo, cnpj_cpf):
        self.tipo = tipo
        self.cnpj_cpf = cnpj_cpf
        self.nome = None
        self.cep = None
        self.endereco = None
        self.numero_endereco = None
        self.bairro = None
        self.complemento = None
        self.cidade = None
        self.estado = None
        self.telefone_contato = None
        self.email = None

    def preencher_cnpj(self, cnpj_data):
        self.nome = cnpj_data["nome"]
        self.cep = cnpj_data["cep"]
        self.endereco = cnpj_data["logradouro"]
        self.numero_endereco = cnpj_data["numero"]
        self.bairro = cnpj_data["bairro"]
        self.complemento = cnpj_data.get("complemento", None)
        self.cidade = cnpj_data["municipio"]
        self.estado = cnpj_data["uf"]
        self.telefone_contato = cnpj_data["telefone"]
        self.email = cnpj_data.get("email", None)

# Classe para gerenciar o fluxo de cadastro
class CadastroHandler:
    def __init__(self):
        self.cadastro_atual = None

    def cadastrar_iniciar(self, tipo, cnpj_cpf=None):
        self.cadastro_atual = Cadastro(tipo, cnpj_cpf)

    def preencher_cnpj_cpf(self, cnpj_cpf):
        if not self.cadastro_atual:
            return "Erro: cadastro não iniciado."

        self.cadastro_atual.cnpj_cpf = cnpj_cpf

        # Verificar se é CNPJ ou CPF
        if len(cnpj_cpf) == 14:
            # CNPJ encontrado, pesquisar na API e preencher os dados
            cnpj_data = pesquisar_cnpj(cnpj_cpf)
            if cnpj_data:
                self.cadastro_atual.preencher_cnpj(cnpj_data)
                return None
            else:
                return (
                    "CNPJ inválido ou não encontrado na base de dados. Por favor, digite um CNPJ válido."
                )

        elif len(cnpj_cpf) == 11:

            return None

        else:
            # CPF ou CNPJ inválido
            return "CPF ou CNPJ inválido. Por favor, digite um CPF ou CNPJ válido."

    def preencher_dado(self, field_name, field_value):
        if not self.cadastro_atual:
            return "Erro: cadastro não iniciado."

        setattr(self.cadastro_atual, field_name, field_value)
        return None

    def is_cadastro_completo(self):
        if not self.cadastro_atual:
            return False

        return all(getattr(self.cadastro_atual, field) for field in CAMPOS_CADASTRO)

    def get_cadastro_atual(self):
        return self.cadastro_atual if self.cadastro_atual else None
    
# Função para pesquisar CNPJ
def pesquisar_cnpj(cnpj):
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("status", None) == "ERROR":
                return None
            return data
    except requests.exceptions.RequestException:
        return None

    return None

# Função para pesquisar CEP
def pesquisar_cep(cep):
    url = f"https://viacep.com.br/ws/{cep}/json/"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("erro"):
                return None
            return data
    except requests.exceptions.RequestException:
        return None

    return None

# Função para limpar CNPJ/CPF
def limpar_cnpj_cpf(cnpj_cpf):
    return re.sub(r"[^0-9]", "", cnpj_cpf)

# Função para exibir menu inicial
def menu(update: Update, _: CallbackContext) -> int:
    user = update.effective_user
    user_id = user.id
    options = [
        [
            InlineKeyboardButton("➕ Cadastrar Cliente", callback_data="cliente"),
            InlineKeyboardButton("🏭 Cadastrar Matriz", callback_data="matriz")
         ],
        [
            InlineKeyboardButton("📄 Listar Cadastros", callback_data="listar"),
            InlineKeyboardButton("🗑 Excluir Cadastros", callback_data="excluir_cadastro")
         ],
        [InlineKeyboardButton("💢 Cancelar", callback_data="cancelar")]
    ]
        # Contar o número de clientes e matrizes
    user_info = ler_informacoes_usuario(user_id)
    clientes = sum(1 for cadastro in user_info.get("cadastros", []) if cadastro["tipo"] == "cliente")
    matrizes = sum(1 for cadastro in user_info.get("cadastros", []) if cadastro["tipo"] == "matriz")

    if clientes > 0:
        cliente__ = f"***Total de clientes:*** [ {clientes} ]"
    else:
        cliente__ = f"***Nenhum cliente cadastrado!*** 📒"

    if matrizes == 0:
        matriz__ = f"***Sua empresa não está cadastrada.*** ❌"
    else:
        matriz__ = f"***Sua empresa está cadastrada!*** ✅"

    reply_markup = InlineKeyboardMarkup(options)
    update.message.reply_text(f"\n━━━━━━━✦✗✦━━━━━━━━\n" \
                              f"{matriz__}\n" \
                              f"{cliente__}\n" \
                              f"━━━━━━━✦✗✦━━━━━━━━\n\n" \
                              f"🤔 Oque deseja fazer 💭? selecione uma opção:\n\nLembrete: a qualquer momento pode apertar /cancelar.", reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
    return SELECTING_OPTION

# Função para iniciar o cadastro
def cadastrar_start(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    tipo = query.data
    if tipo == "cancelar":
        query.edit_message_text("Operação cancelada! todo progresso feito foi apagado.")
        context.user_data["cadastro_handler"] = CadastroHandler()
        return ConversationHandler.END

        # Ler as informações do usuário a partir do arquivo JSON
    user_id = update.effective_user.id
    user_folder_path = f"user_data/{user_id}"
    user_info_file_path = f"{user_folder_path}/user_info.json"
    with open(user_info_file_path, "r") as user_info_file:
        user_info = json.load(user_info_file)


    cadastro_handler = context.user_data.get("cadastro_handler")

    if not cadastro_handler:
        cadastro_handler = CadastroHandler()
        context.user_data["cadastro_handler"] = cadastro_handler

    if tipo == "cliente":
        cadastro_handler.cadastrar_iniciar("cliente")
        nome_tipo = "do Cliente"
    elif tipo == "matriz":
        nome_tipo = "da Matriz (sua empresa)"

        # Verificar se o usuário já possui um cadastro de matriz
        user_cadastros = user_info.get("cadastros", [])
        has_matriz_cadastro = any(cadastro.get("tipo") == "matriz" for cadastro in user_cadastros)
        if has_matriz_cadastro:
            query.edit_message_text("Você já possui um cadastro de Matriz.")
            return ConversationHandler.END

        cadastro_handler.cadastrar_iniciar("matriz")

    query.edit_message_text(
        f"Vamos lá, Digite o CPF ou CNPJ {nome_tipo}:"
    )
    return CADASTRO

def verificar_cnpj_cpf(update: Update, context: CallbackContext) -> int:
    if "tentativas" not in context.user_data:
        context.user_data["tentativas"] = 0

    cnpj_cpf = limpar_cnpj_cpf(update.message.text)

    user = update.effective_user
    user_id = user.id
 
    situação_usuario = verificar_creditos(user_id)
    if situação_usuario:
        if situação_usuario["tipo"] == "mensal":
            update.message.reply_text(situação_usuario["mensagem"])
            return ConversationHandler.END
        elif situação_usuario["tipo"] == "credito":
            update.message.reply_text(situação_usuario["mensagem"])
            return ConversationHandler.END

    # Verificar se o número (CPF/CNPJ) já está cadastrado no cadastro temporário
    cadastro_handler = context.user_data.get("cadastro_handler")
    cadastro_temporario = cadastro_handler.get_cadastro_atual()  

    # Verificar se o número (CPF/CNPJ) já está cadastrado no arquivo JSON do usuário atual
    user_id = update.message.chat_id
    user_folder_path = f"user_data/{user_id}"
    user_info_file_path = f"{user_folder_path}/user_info.json"
    if os.path.exists(user_info_file_path):
        with open(user_info_file_path, "r") as user_info_file:
            user_info = json.load(user_info_file)
            cadastros = user_info.get("cadastros", [])

            for cadastro in cadastros:
                if cadastro.get("cnpj_cpf") == cnpj_cpf:
                    update.message.reply_text(
                        f"❌ ***- Cadastro Negado!***\nEsse número (CPF/CNPJ) já está cadastrado no seu perfil. Por favor, verifique e tente novamente. ou se quiser cancelar aperte aqui /cancelar", parse_mode=telegram.ParseMode.MARKDOWN
                    )
                    update.message.reply_text(
                        f"***Digite outro CPF ou CNPJ:***", parse_mode=telegram.ParseMode.MARKDOWN
                    )
                    return CADASTRO

    # Verificar se o usuário está tentando cadastrar como matriz
    tipo = cadastro_temporario.tipo

    if tipo == "matriz":
        # Verificar se o número (CPF/CNPJ) está cadastrado em alguma matriz de outros usuários
        user_data_folder = "user_data/"
        for user_folder in os.listdir(user_data_folder):
            other_user_id = int(user_folder)
            if other_user_id != user_id:  # Ignorar o arquivo JSON do usuário atual
                other_user_info_file_path = f"{user_data_folder}/{user_folder}/user_info.json"
                with open(other_user_info_file_path, "r") as other_user_info_file:
                    other_user_info = json.load(other_user_info_file)
                    other_user_cadastros = other_user_info.get("cadastros", [])
                    for other_user_cadastro in other_user_cadastros:
                        tipo_cadastro = other_user_cadastro.get("tipo", "")
                        if tipo_cadastro == "matriz" and other_user_cadastro.get("cnpj_cpf") == cnpj_cpf:
                            update.message.reply_text(
                                f"❌ ***- Cadastro Negado!***\nEsse número (CPF/CNPJ) já está cadastrado em outra matriz de outro usuario. Por favor, verifique e tente novamente. caso o usuario cadastrou errado, entre em contato com suporte. @suporteorcamentobot, ou se quiser cancelar aperte aqui /cancelar", parse_mode=telegram.ParseMode.MARKDOWN
                            )
                            update.message.reply_text(
                                f"***Digite outro CPF ou CNPJ da Matriz***", parse_mode=telegram.ParseMode.MARKDOWN
                            )
                            return CADASTRO
 
    # Verificar se é CNPJ ou CPF
    if len(cnpj_cpf) == 14:
        error_message = context.user_data["cadastro_handler"].preencher_cnpj_cpf(cnpj_cpf)
        if error_message:
            context.user_data["tentativas"] += 1
            if context.user_data["tentativas"] >= 3:
                update.message.reply_text("❌ Você excedeu o número máximo de tentativas. Por favor, tente novamente mais tarde.")
                return ConversationHandler.END
            update.message.reply_text(f"Tentativa {context.user_data['tentativas']} de 3. Digite novamente o CPF ou CNPJ válido:")
            return CADASTRO

    elif len(cnpj_cpf) == 11:
        return select_cadastro(update, context)
        
    else:
        # CPF ou CNPJ inválido
        context.user_data["tentativas"] += 1
        if context.user_data["tentativas"] >= 3:
            update.message.reply_text("❌ Você excedeu o número máximo de tentativas. Por favor, tente novamente mais tarde.")
            return ConversationHandler.END
        update.message.reply_text(f"Tentativa {context.user_data['tentativas']} de 3. Digite novamente o CPF ou CNPJ válido:")
        return CADASTRO

    context.user_data.pop("tentativas", None)
    return listar_editar_cadastro(update, context)

# Função para iniciar o cadastro de cliente ou matriz
def select_cadastro(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text.lower()
    cadastro_handler = context.user_data["cadastro_handler"]
    cont = cadastro_handler.get_cadastro_atual()
    context.user_data["tipo_cadastro"] = cont.tipo

    # Definir o cnpj_cpf no context.user_data
    context.user_data["cnpj_cpf"] = user_input

    # Iniciar o cadastro
    cadastro_handler.cadastrar_iniciar(cont.tipo, user_input)

    # Chama a função preencher_campos_loop para continuar preenchendo os campos enquanto houver campos faltantes
    return preencher_campos_loop(update, context)

# Função para lidar com a edição do campo selecionado
def editing_field(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text.lower()

    campos_editaveis = context.user_data.get("campos_editaveis")
    try:
        opcao = int(user_input.split('.')[0].strip())
    except ValueError:
        # If the input is not numeric, handle the error
        num_attempts = context.user_data.get("num_attempts", 0) + 1
        max_attempts = 3
        if num_attempts >= max_attempts:
            update.message.reply_text("Número de tentativas excedido. Operação cancelada.")
            return cancel(update, context)
        context.user_data["num_attempts"] = num_attempts
        update.message.reply_text(f"Opção inválida. Escolha um campo válido. Tentativa {num_attempts} de {max_attempts}.")
        return EDITING_FIELD

    if opcao in range(1, len(campos_editaveis) + 1):
        num_opcao = opcao
        if not 1 <= num_opcao <= len(campos_editaveis):
            update.message.reply_text(
                "Opção inválida. Escolha um campo válido."
            )
            return EDITING_FIELD

        # Definir o próximo campo a ser editado
        field_name = campos_editaveis[num_opcao - 1]
        context.user_data["field_name"] = field_name

        update.message.reply_text(
            f"Digite o novo valor para {field_name.replace('_', ' ').capitalize()}:"
        )
        return SELECTING_OPTION_EDITING
    
   # Se não for um dígito, pode ser uma tentativa de editar sem ter selecionado o campo anteriormente
    update.message.reply_text("Por favor, selecione um campo para editar primeiro.")
    return CADASTRO

# Função para cadastrar os demais campos
def cadastrar_field(update: Update, context: CallbackContext) -> int:
    cadastro_handler = context.user_data["cadastro_handler"]
    cadastro_atual = cadastro_handler.get_cadastro_atual()

    # Verificar se já foi selecionado um campo para edição
    if "field_name" not in context.user_data:
        update.message.reply_text("Por favor, selecione um campo para editar primeiro.")
        return EDITING_FIELD

    field_name = context.user_data["field_name"]
    field_value = update.message.text

    # Preencher o dado do campo recebido
    error_message = cadastro_handler.preencher_dado(field_name, field_value)
    if error_message:
        update.message.reply_text(error_message)
        return CADASTRO

    campos_faltantes_list = campos_faltando(cadastro_atual)

    # Se ainda faltam campos para preencher, solicitar o próximo
    if campos_faltantes_list:
        next_field = campos_faltantes_list[0]
        context.user_data["field_name"] = next_field
        update.message.reply_text(f"Digite {next_field.replace('_', ' ').capitalize()}:")
        return CADASTRO

    # Se todos os campos foram preenchidos, listar os dados cadastrados e perguntar se quer editar ou finalizar
    return listar_editar_cadastro(update, context)

def preencher_campo(update: Update, context: CallbackContext) -> int:
    cadastro_handler = context.user_data["cadastro_handler"]
    cadastro_atual = cadastro_handler.get_cadastro_atual()

    # Verificar se todos os campos já foram preenchidos
    if cadastro_handler.is_cadastro_completo():
        return listar_editar_cadastro(update, context)  # Cadastro concluído

    # Obter o nome do campo atual a ser preenchido
    field_name = context.user_data.get("field_name")

    if field_name == "cep" and not cadastro_atual.endereco:
        # O campo "cep" está vazio, vamos preencher os outros campos usando a API de CEP
        cnpj_data = pesquisar_cep(update.message.text)
        if cnpj_data:
            # Preencher os campos do cadastro com os dados da API
            cadastro_atual.cep = cnpj_data.get("cep", None)
            cadastro_atual.endereco = cnpj_data.get("logradouro", None)
            cadastro_atual.numero_endereco = cnpj_data.get("numero", None)
            cadastro_atual.bairro = cnpj_data.get("bairro", None)
            cadastro_atual.complemento = cnpj_data.get("complemento", None)
            cadastro_atual.cidade = cnpj_data.get("localidade", None)
            cadastro_atual.estado = cnpj_data.get("uf", None)
            cadastro_atual.telefone_contato = cnpj_data.get("telefone", None)
            cadastro_atual.email = cnpj_data.get("email", None)
            return preencher_campos_loop(update, context)
        
    if field_name:
        # Preencher o dado do campo recebido
        field_value = update.message.text
        error_message = cadastro_handler.preencher_dado(field_name, field_value)
        if error_message:
            update.message.reply_text(error_message)
        else:
            # Remover o campo da lista de campos faltantes (se estiver presente)
            campos_faltantes_list = campos_faltando(cadastro_atual)
            if field_name in campos_faltantes_list:
                campos_faltantes_list.remove(field_name)
            context.user_data["field_name"] = None

    # Chamar novamente a função preencher_campos_loop para continuar preenchendo os campos
    return preencher_campos_loop(update, context)


def preencher_campos_loop(update: Update, context: CallbackContext) -> int:
    cadastro_handler = context.user_data["cadastro_handler"]
    cadastro_atual = cadastro_handler.get_cadastro_atual()

    # Obter a lista de campos faltantes
    campos_faltantes_list = campos_faltando(cadastro_atual)


    if campos_faltantes_list:
        # Ainda há campos para preencher, vamos solicitar o próximo
        next_field = campos_faltantes_list[0]
        context.user_data["field_name"] = next_field
        update.message.reply_text(f"Digite {next_field.replace('_', ' ').capitalize()}:")
        
        return SELECTING_OPTION_EDITING_S



    # Cadastro concluído, listar os dados cadastrados e perguntar se quer editar ou finalizar
    return listar_editar_cadastro(update, context)

def resposta_listar_cadastro(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    response = query.data.lower()
    
    # Definir uma lista com as opções válidas para a pergunta
    opcoes_validas = ["clientes", "matrizs"]

    if response in opcoes_validas:
        # Opção válida selecionada, listar os cadastros correspondentes
        if response == "clientes":
            response = "cliente"
        else:
            response = "matriz"
        user_id = query.from_user.id
        cadastros = listar_cadastros_por_tipo(user_id, response)

        if not cadastros:
            query.edit_message_text(f"Nenhum cadastro {response} encontrado.")
        else:
            message = f"Lista de Clientes:\n\n"
            for idx, cadastro in enumerate(cadastros, start=1):
                message += f"˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙\nCadastro Nº ***{idx}:***\n{formatar_cadastro(cadastro)}\n"
            query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    
    else:
        # Opção inválida, informar a quantidade de tentativas restantes
        query.edit_message_text("Opção inválida. Tente novamente.")
    
    return AGUARDAR_RESPOSTA

def listar_cadastros(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()

    options = [
        [InlineKeyboardButton("📒 Cliente", callback_data="clientes")],
        [InlineKeyboardButton("🏭 Matriz", callback_data="matrizs")],
    ]
    reply_markup = InlineKeyboardMarkup(options)
    query.edit_message_text(
        "Ver cadastro da matriz ou cliente?", reply_markup=reply_markup
    )
    return AGUARDAR_RESPOSTA
    
# Função para lidar com os botões inline
def inline_button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    button_pressed = query.data
    query.answer()
    if button_pressed == 'finalizar':
        return cadastrar_finalizar(query, context)  # Certifique-se de chamar a função correta aqui.
    elif button_pressed == 'cancelar':
        query.edit_message_text("Operação cancelada!.")
        context.user_data["cadastro_handler"] = CadastroHandler()
        return ConversationHandler.END

    else:
        # Outras opções para o caso de você ter mais botões inline
        pass

# Função para cancelar a operação
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Operação cancelada!")
    context.user_data["cadastro_handler"] = CadastroHandler()
    return ConversationHandler.END


# Função para listar e editar o cadastro antes de finalizar
def listar_editar_cadastro(update: Update, context: CallbackContext) -> int:
    cadastro_handler = context.user_data["cadastro_handler"]
    cadastro_atual = cadastro_handler.get_cadastro_atual()

    if cadastro_atual:
        message = "Dados cadastrados:\n"
        campos_editaveis = []
        for idx, (field_name, field_value) in enumerate(cadastro_atual.__dict__.items(), start=0):
            if field_value is not None and field_name in CAMPOS_CADASTRO:
                message += f"**{idx - 1}**. *{field_name.capitalize()}:* `{field_value}`\n"
                campos_editaveis.append(field_name)

        # Save the list of editable fields in the user_data for later use in processar_listar_editar_cadastro function
        context.user_data["campos_editaveis"] = campos_editaveis

        message = f"\n___Escolha uma das opções abaixo:___\n" 
        message += f"┌━━━━━━━━━━━━━━\n"
        message += f"├ • ***'Finalizar'***, salvar e terminar o cadastro.\n" 
        message += f"├ • ***'Cancelar'***, Excluir todo o cadastro e cancela.\n" 
        message += f"└ • Para editar digite um numero ou selecione abaixo. \n\n"  
        
        reply_markup_keyboard, reply_markup_inline = custom_keyboard(campos_editaveis)
        update.message.reply_text(
            message, reply_markup=reply_markup_keyboard, parse_mode=telegram.ParseMode.MARKDOWN
        )

        # Enviar também os botões "Finalizar" e "Cancelar" em formato inline
        update.message.reply_text(
            "Escolha uma das opções abaixo:",
            reply_markup=reply_markup_inline
        )

        return EDITING_FIELD

    else:
        # Caso não haja cadastro atual, voltamos para o início da conversa
        update.message.reply_text("Nenhum cadastro em andamento.")
        return menu(update, context)  # Voltar para o menu inicial

# Função para criar o teclado customizado com os números dos campos editáveis
def custom_keyboard(campos_editaveis):

    # Criar os botões do teclado a partir da lista de campos editáveis
    keyboard = [
        [KeyboardButton(f"{idx}. {campo.capitalize()}")]
        for idx, campo in enumerate(campos_editaveis, start=1)
    ]

    # Criar os botões "Finalizar" e "Cancelar" em formato inline
    inline_keyboard = [
        [InlineKeyboardButton("Finalizar ✅", callback_data="finalizar"), InlineKeyboardButton("Cancelar ❌", callback_data="cancelar")]
    ]

    # Criar o ReplyKeyboardMarkup e InlineKeyboardMarkup com one_time_keyboard=True
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True), InlineKeyboardMarkup(inline_keyboard)

# Função para finalizar o cadastro
def cadastrar_finalizar(update: Update, context: CallbackContext) -> int:

    cadastro_handler = context.user_data["cadastro_handler"]
    cadastro_atual = cadastro_handler.get_cadastro_atual()
    
    if cadastro_atual:

        # Ler as informações do usuário a partir do arquivo JSON
        user_id = update.message.chat_id
        consumir_credito(user_id)
        
        user_folder_path = f"user_data/{user_id}"
        user_info_file_path = f"{user_folder_path}/user_info.json"

        with open(user_info_file_path, "r") as user_info_file:
            user_info = json.load(user_info_file)

        # Salvar o cadastro no arquivo JSON
        user_info["cadastros"].append(cadastro_atual.__dict__)
        with open(user_info_file_path, "w", encoding="utf-8") as user_info_file:
            json.dump(user_info, user_info_file, ensure_ascii=False, indent=4)

        # Reiniciar o cadastro_handler para uma próxima vez
        context.user_data["cadastro_handler"] = CadastroHandler()
        update.message.reply_text("Cadastro finalizado e salvo com sucesso! ✅ - Aperte: /menu", reply_markup=ReplyKeyboardRemove(), parse_mode=telegram.ParseMode.MARKDOWN)
    return ConversationHandler.END

# Função para retornar a lista de campos faltantes no cadastro
def campos_faltando(cadastro_atual):
    return [campo for campo in CAMPOS_CADASTRO if not getattr(cadastro_atual, campo)]

def formatar_cadastro(cadastro):
    tipo = cadastro.get("tipo")
    cnpj_cpf = formatar_cnpj_cpf_cep(cadastro.get("cnpj_cpf"))
    nome = cadastro.get("nome")
    cep = formatar_cnpj_cpf_cep(cadastro.get("cep"))
    endereco = cadastro.get("endereco")
    numero_endereco = cadastro.get("numero_endereco")
    bairro = cadastro.get("bairro")
    complemento = cadastro.get("complemento")
    cidade = cadastro.get("cidade")
    estado = cadastro.get("estado")
    telefone_contato = formatar_telefone(cadastro.get("telefone_contato"))
    email = cadastro.get("email")

    # Formatar o cadastro como uma string formatada
    formatted_cadastro =  f"┌────────────────\n" 
    formatted_cadastro += f"├─ • ***Tipo:*** `{tipo}`\n" 
    formatted_cadastro += f"├────────────────\n"
    formatted_cadastro += f"├─ ***CNPJ/CPF:*** `{cnpj_cpf}`\n" 
    formatted_cadastro += f"├─ ***Nome:*** `{nome}`\n" 
    formatted_cadastro += f"├─ ***CEP:*** `{cep}`\n" 
    formatted_cadastro += f"├─ ***Endereço:*** `{endereco}, {numero_endereco}`\n" 
    formatted_cadastro += f"├─ ***Bairro:*** `{bairro}`\n"
    formatted_cadastro += f"├─ ***Complemento:*** `{complemento}`\n"
    formatted_cadastro += f"├─ ***Cidade:*** `{cidade}`\n" 
    formatted_cadastro += f"├─ ***Estado:*** `{estado}`\n" 
    formatted_cadastro += f"├─ ***Telefone:*** `{telefone_contato}`\n"
    formatted_cadastro += f"├─ ***E-mail:*** `{email}`\n"
    formatted_cadastro += f"└────────────────\n"
    return formatted_cadastro


def listar_cadastros_por_tipo(user_id: int, tipo: str):
    cadastros = []

    # Verificar se a pasta do usuário existe
    user_folder_path = f"user_data/{user_id}"
    if not os.path.exists(user_folder_path):
        return cadastros

    # Verificar se o arquivo user_info.json existe
    user_info_file_path = f"{user_folder_path}/user_info.json"
    if not os.path.exists(user_info_file_path):
        return cadastros

    # Carregar os cadastros do arquivo user_info.json
    with open(user_info_file_path, "r") as user_info_file:
        user_info = json.load(user_info_file)
        user_cadastros = user_info.get("cadastros", [])
        for cadastro in user_cadastros:
            if cadastro.get("tipo") == tipo:
                cadastros.append(cadastro)

    return cadastros

def funcao_auxiliar_logo(update: Update, context: CallbackContext) -> int:
    
    query = update.callback_query
    message = f"˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙˙\n"
    query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)

    # Redireciona o usuário para o comando /iniciar_orcamento
    context.bot.send_message(chat_id=query.message.chat_id, text=f"Aperte aqui 👉 /logo")

    # Retorna o estado atual para evitar problemas com o ConversationHandler
    return ConversationHandler.END