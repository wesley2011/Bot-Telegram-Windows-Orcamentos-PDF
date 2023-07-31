import json, time,os, telegram
from datetime import datetime
from telegram import Bot


token_file = "conversacoes/token_bot/token.txt"



def verificar_cadastros_vencidos():
    user_data_path = "user_data"
    while True:
        # Caminho para o arquivo de log de notificações
        log_file_path = "Controle_Notificacoes/notificacoes_log.json"

        # Verificar cada pasta de usuário (cada pasta é um ID de usuário)
        for user_id in os.listdir(user_data_path):
            user_folder_path = os.path.join(user_data_path, user_id)
            user_info_file_path = os.path.join(user_folder_path, "user_info.json")

            # Verificar se o arquivo "user_info.json" existe para o usuário atual
            if os.path.exists(user_info_file_path):
                with open(user_info_file_path, "r") as user_info_file:
                    user_info = json.load(user_info_file)
                    mensalidades = user_info.get("mensalidade", [])
                    nome_usuario = user_info.get("first_name", "")


                    if user_info.get("mensal"):
                        data_hora_atual_str = datetime.now().strftime("%d/%m/%Y %H:%M")
                        

                        # Atualizar o status das mensalidades com base na data de vencimento
                        for mensalidade in mensalidades:
                            
                            if mensalidade.get("status"):
                                data_final_str = mensalidade["data_final"]
                                # Converter as strings em objetos datetime
                                data_final = datetime.strptime(data_final_str, "%d/%m/%Y %H:%M")
                                data_hora_atual = datetime.strptime(data_hora_atual_str, "%d/%m/%Y %H:%M")

                                # Calcular a diferença entre as datas
                                diferenca_tempo = data_final - data_hora_atual

                                # Acessar os atributos do timedelta para obter a diferença em dias, horas e minutos
                                dias_restantes = diferenca_tempo.days
                                horas_restantes = diferenca_tempo.seconds // 3600  # converter segundos para horas
                                minutos_restantes = (diferenca_tempo.seconds // 60) % 60  # converter segundos para minutos



                                # Verificar se a mensalidade já venceu
                                if data_final < data_hora_atual:
                                    
                                    mensalidade["status"] = False
                                    message = f"╭───── • ◈ • ─────╮\n"
                                    message += f"               ***Aviso 2/2***\n"
                                    message += f"╰───── • ◈ • ─────╯\n\n"
                                    message += f"Olá {nome_usuario}, a sua mensalidade está ***vencida***. Renove agora @suporteorcamentobot"

                                    enviar_notificacao(message, user_id)
                                    if user_id not in log_data:
                                        log_data[user_id] = {
                                        "lembrete": True,
                                        "vencimento": False
                                    }
                                    log_data[user_id]["vencimento"] = True

                                    # Salvar o log de notificações atualizado
                                    with open(log_file_path, "w", encoding="utf-8") as log_file:
                                        json.dump(log_data, log_file, indent=4, ensure_ascii=False)

                        # Salvar as alterações no arquivo "user_info.json"
                        with open(user_info_file_path, "w", encoding="utf-8") as user_info_file:
                            json.dump(user_info, user_info_file, indent=4, ensure_ascii=False)
                        
                                                                # Armazenar no log que o lembrete foi enviado


                        # Verificar se a mensalidade está perto de vencer
                        for mensalidade in mensalidades:
                            if mensalidade.get("status"):
                                data_final_str = mensalidade["data_final"]
                                # Converter as strings em objetos datetime
                                data_final = datetime.strptime(data_final_str, "%d/%m/%Y %H:%M")
                                data_hora_atual = datetime.strptime(data_hora_atual_str, "%d/%m/%Y %H:%M")

                                # Calcular a diferença entre as datas
                                diferenca_tempo = data_final - data_hora_atual

                                # Acessar os atributos do timedelta para obter a diferença em dias, horas e minutos
                                dias_restantes = diferenca_tempo.days
                                horas_restantes = diferenca_tempo.seconds // 3600  # converter segundos para horas
                                minutos_restantes = (diferenca_tempo.seconds // 60) % 60  # converter segundos para minutos

                                # Verificar se faltam menos de 5 dias para vencer a mensalidade
                                if 0 < dias_restantes <= 5:
                                    # Abrir o arquivo de log de notificações (se já existir)
                                    if os.path.exists(log_file_path):
                                        with open(log_file_path, "r") as log_file:
                                            log_data = json.load(log_file)
                                    else:
                                        log_data = {}

                                    if user_id not in log_data or "lembrete" not in log_data[user_id]:
                                        message = f"╭───── • ◈ • ─────╮\n"
                                        message += f"               ***Aviso 1/2***\n"
                                        message += f"╰───── • ◈ • ─────╯\n\n"
                                        message += f"___Olá___ {nome_usuario}___, a sua mensalidade está perto de vencer!___\n────────────────\n"
                                        message += f"***Dias restantes:*** `{dias_restantes}`\n"
                                        message += f"***Horas restantes:*** `{horas_restantes}`\n"
                                        message += f"***Minutos restantes:*** `{minutos_restantes}`\nNão fique sem usar o sistema, renove agora @suporteorcamentobot"
                                        enviar_notificacao(message, user_id)

                                        # Armazenar no log que o lembrete foi enviado
                                        if user_id not in log_data:
                                            log_data[user_id] = {
                                            "lembrete": False,
                                            "vencimento": False
                                        }
                                        log_data[user_id]["lembrete"] = True

                                    # Salvar o log de notificações atualizado
                                    with open(log_file_path, "w", encoding="utf-8") as log_file:
                                        json.dump(log_data, log_file, indent=4, ensure_ascii=False)

        # Intervalo de espera de 1 hora (3600 segundos) antes de verificar novamente
        time.sleep(10)

def enviar_notificacao(mensagem, usuario_id):
        # Leitura do token do bot a partir do arquivo "token.txt"
    with open(token_file, "r") as file:
        token = file.read().strip()
        # Remove o prefixo "token=" do valor lido
        token = token.replace("token=", "")
    bot = Bot(token)
    bot.send_message(chat_id=usuario_id, 
                        text=mensagem, 
                        parse_mode=telegram.ParseMode.MARKDOWN
                        )


def agendar_verificacao_cadastros(scheduler):
    verificar_cadastros_vencidos()  # Executa a função imediatamente no início do programa
    scheduler.enter(10, 0, agendar_verificacao_cadastros, (scheduler,))  # Agendamento para 1 hora (3600 segundos)

