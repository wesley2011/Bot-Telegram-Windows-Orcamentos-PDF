import json, re, os


def ler_informacoes_usuario(user_id):
    user_folder_path = f"user_data/{user_id}"
    user_info_file_path = f"{user_folder_path}/user_info.json"
    if os.path.exists(user_info_file_path):
        with open(user_info_file_path, "r") as user_info_file:
            user_info = json.load(user_info_file)
            return user_info
    return None

def formatar_cnpj_cpf(nome: str, cnpj_cpf: str) -> str:
    if len(cnpj_cpf) == 14:  # CNPJ
        cnpj_formatado = f"/{cnpj_cpf[-6:-2]}-{cnpj_cpf[-2:]}"
        return f"{cnpj_formatado} - {nome.split()[0]}"
    elif len(cnpj_cpf) == 11:  # CPF
        cpf_formatado = f"{cnpj_cpf[:3]}.{cnpj_cpf[3:6]}"
        return f"{cpf_formatado} - {nome.split()[0]}"
    return f"\"{cnpj_cpf}\" - {nome.split()[0]}"

def formatar_cnpj_cpf_cep(numero):
    numero = numero.strip().replace(".", "").replace("/", "").replace("-", "")

    if len(numero) == 14:
        return f"{numero[:2]}.{numero[2:5]}.{numero[5:8]}/{numero[8:12]}-{numero[12:]}"
    elif len(numero) == 11:
        return f"{numero[:3]}.{numero[3:6]}.{numero[6:9]}-{numero[9:]}"
    elif len(numero) == 8 or "." in numero or "-" in numero:
        return f"{numero[:2]}.{numero[2:5]}-{numero[5:]}"
    else:
        return numero
    
def formatar_telefone(numero):
    numero2 = numero
    numero = re.sub(r"\D", "", numero)  # Remover todos os caracteres não numéricos
    if len(numero) > 11: return numero2
    
    if len(numero) == 8:
        return f"{numero[:4]}-{numero[4:]}"
    elif len(numero) == 9:
        return f"{numero[0]}.{numero[1:5]}-{numero[5:]}"
    elif len(numero) == 11:
        return f"({numero[:2]}) {numero[2]}.{numero[3:7]}-{numero[7:]}"
    else:
        return numero
    
