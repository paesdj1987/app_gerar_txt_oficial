#callbacks.py

import base64
import io
import pandas as pd
from dash import Output, Input, State, html, dcc
from decimal import Decimal
from layout import create_stepper
import re
import zipfile

def init_callbacks(app):

    # -------------------------------------------------------------------------
    # Mensagens após upload (R01 / R03)
    # -------------------------------------------------------------------------
    @app.callback(
        Output("msg-tipo-r01", "children"),
        Input("upload-tipo-r01", "contents"),
        State("upload-tipo-r01", "filename"),
        prevent_initial_call=True
    )
    def mostrar_msg_r01(r01_contents, r01_filename):
        if r01_contents and r01_filename:
            return f"Arquivo R01 '{r01_filename}' carregado com sucesso!"
        return ""

    @app.callback(
        Output("msg-tipo-r03", "children"),
        Input("upload-tipo-r03", "contents"),
        State("upload-tipo-r03", "filename"),
        prevent_initial_call=True
    )
    def mostrar_msg_r03(r03_contents, r03_filename):
        if r03_contents and r03_filename:
            return f"Arquivo R03 '{r03_filename}' carregado com sucesso!"
        return ""
    
    @app.callback(
        Output("msg-gerar-txt", "children"),
        Input("botao-gerar-txt", "n_clicks"),
        prevent_initial_call=True
    )
    def mostrar_msg_gerado(n_clicks):
        if n_clicks:
            return "TXT gerado com sucesso!"
        return ""

    # Callback client-side 
    app.clientside_callback(
        """
        function(n_clicks) {
        if (!n_clicks) { return ""; }
        const pre = document.getElementById('output-gerar-txt');
        const text = pre ? (pre.innerText || pre.textContent) : "";
        navigator.clipboard.writeText(text)
            .catch(err => console.error('Erro ao copiar:', err));
        return "";
        }
        """,
        Output('clipboard-output', 'children'),
        Input('btn-copy-preview', 'n_clicks'),
        prevent_initial_call=True
    )


    # -------------------------------------------------------------------------
    # Geração do TXT
    # -------------------------------------------------------------------------
    @app.callback(
        Output("output-gerar-txt", "children"),
        Output("store-txt-data", "data"),
        Input("botao-gerar-txt", "n_clicks"),
        State("upload-tipo-r01", "contents"),
        State("upload-tipo-r01", "filename"),
        State("upload-tipo-r03", "contents"),
        State("upload-tipo-r03", "filename"),
        prevent_initial_call=True
    )
    def gerar_txt_callback(n_clicks, r01_contents, r01_filename, r03_contents, r03_filename):
        if n_clicks is None:
            return "", ""

        if not r01_contents or not r03_contents:
            mensagem = html.Div("Por favor, envie os dois arquivos Excel antes de gerar o TXT.", style={'color': 'red'})
            return mensagem, ""

        try:
            df_r01 = parse_excel(r01_contents, r01_filename)
            df_r03 = parse_excel(r03_contents, r03_filename)
        except Exception as e:
            return html.Div(f"Erro ao ler arquivos Excel: {e}", style={'color': 'red'}), ""

        # Processa R01 e R03
        try:
            txt_final = gerar_txt_r01_e_r03(df_r01, df_r03)
        except ValueError as e:
            return html.Div(f"Erro ao gerar TXT: {e}", style={'color': 'red'}), ""

        return html.Pre(txt_final), txt_final

    # -------------------------------------------------------------------------
    # Habilitar o botão de download
    # -------------------------------------------------------------------------

    # 1) Habilita o botão de download assim que gerar o TXT
    @app.callback(
        Output("botao-download-txt", "disabled"),
        Input("botao-gerar-txt", "n_clicks"),
        prevent_initial_call=True
    )
    def habilitar_download(n_clicks):
        return False  # libera o botão

    # 2) Atualiza o stepper conforme uploads e geração
    @app.callback(
    Output("stepper", "children"),
        [
            Input("msg-tipo-r01", "children"),
            Input("msg-tipo-r03", "children"),
            Input("botao-gerar-txt", "n_clicks"),
            Input("botao-download-txt", "n_clicks"),
        ],
        prevent_initial_call=False
    )
    def atualizar_stepper(msg1, msg3, gerar_clicks, download_clicks):
        # Etapa 4 – após download
        if download_clicks:
            return create_stepper(4)
        
        # Etapa 3 – após gerar
        if gerar_clicks:
            return create_stepper(3)
        
        # Etapa 2 – R01 e R03 carregados com sucesso
        if (
            isinstance(msg1, str) and "R01" in msg1 and "sucesso" in msg1
            and isinstance(msg3, str) and "R03" in msg3 and "sucesso" in msg3
        ):
            return create_stepper(2)

        # Etapa 1 – somente R01 carregado com sucesso
        if isinstance(msg1, str) and "R01" in msg1 and "sucesso" in msg1:
            return create_stepper(1)

        # Nenhum passo válido
        return create_stepper(0)



    # -------------------------------------------------------------------------
    # Download do TXT em ANSI (Windows-1252)
    # -------------------------------------------------------------------------
    @app.callback(
        Output("download-text-file", "data"),
        Input("botao-download-txt", "n_clicks"),
        State("store-txt-data", "data"),
        prevent_initial_call=True
    )
    def download_txt_callback(n_clicks, txt_data):
        if not n_clicks or not txt_data:
            return None

        # Converte o texto para bytes usando codificação Windows-1252 (ANSI)
        txt_bytes = txt_data.encode("windows-1252", errors="replace")

        # Converte os bytes em Base64
        encoded = base64.b64encode(txt_bytes).decode("ascii")

        # Retorna o conteúdo codificado com base64=True
        return dict(
            content=encoded,
            filename="resultado.txt",
            type="text/plain",
            base64=True
        )

    @app.callback(
        Output("download-modelos", "data"),
        Input("btn-modelos", "n_clicks"),
        prevent_initial_call=True
    )
    def download_modelos_callback(n_clicks):
        if not n_clicks:
            return None
        # Cria um ZIP na memória com os dois arquivos
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.write("assets/tipo_R01.xlsx", arcname="tipo_R01.xlsx")
            zf.write("assets/tipo_R03.xlsx", arcname="tipo_R03.xlsx")
        buf.seek(0)
        return dcc.send_bytes(buf.getvalue(), "modelos_dimob.zip")



# =============================================================================
# Funções auxiliares
# =============================================================================

def parse_excel(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    if 'xlsx' in filename:
        df = pd.read_excel(io.BytesIO(decoded))
    else:
        raise ValueError("Tipo de arquivo inválido. Somente .xlsx é suportado.")
    return df


def gerar_txt_r01_e_r03(df_r01, df_r03):
    
# =============================================================================
# Regras de Negócio para o Header
# =============================================================================    
    
    # Filtra primeira linha R01
    df_r01_filtered = df_r01[df_r01['tipo'].str.upper() == 'R01']
    r01_first = df_r01_filtered.iloc[0] if not df_r01_filtered.empty else None

    # Filtra primeira linha R03
    df_r03_filtered = df_r03[df_r03['tipo'].str.upper() == 'R03']
    r03_first = df_r03_filtered.iloc[0] if not df_r03_filtered.empty else None

    # 1) DIMOB (5 colunas)  ***********
    dimob = "DIMOB"  

    # 2) 7 colunas em branco  ***********
    branco_7 = " " * 7

    # 3) ano_calendario (4 colunas) - vem da primeira linha R03  ***********
    if r03_first is not None:
        ano_cal = str(r03_first.get("ano_calendario", "")).strip()
    else:
        ano_cal = ""
    ano_cal = ano_cal[:4].ljust(4, "0")  

    # 4) 5 colunas de "0"  ***********
    zero_5 = "0" * 5

    # 5) cnpj_do_declarante (R01) (14 colunas) - obrigatório  ***********
    if r01_first is not None:
        cnpj = str(r01_first.get("cnpj_do_declarante", "")).strip()
    else:
        cnpj = ""
    cnpj = "".join(filter(str.isdigit, cnpj))
    cnpj = cnpj.zfill(14)
    cnpj = fix_length(cnpj, 14, pad_char=' ', align='left', truncate=True)

    # 6) 5 colunas de "0"  ***********
    zero_4 = "0" * 4

    # 7) nome_empresarial (R01) (60 colunas)  ***********
    if r01_first is not None:
        nome_emp = str(r01_first.get("nome_empresarial", "")).strip()
    else:
        nome_emp = ""
    nome_emp = nome_emp[:60].ljust(60, " ")  # Caso seja maior que 60, corta; se menor, completa espaços

    # 8) uf_do_contribuinte (R01) (2 colunas)  ***********
    if r01_first is not None:
        uf_r01 = str(r01_first.get("uf_do_contribuinte", "")).strip()
    else:
        uf_r01 = ""
    uf_r01 = uf_r01[:2].ljust(2, " ")

    # 9) 13 colunas preenchidas com "0"  ***********
    zero_13 = "0" * 13

    # 10) cpf_do_responsavel (R01) (11 colunas)  ***********
    if r01_first is not None:
        cpf_resp = str(r01_first.get("cpf_do_responsavel_pela_pessoa_juridica_perante_a_rfb", "")).strip()
    else:
        cpf_resp = ""
    # Remove não numéricos (pontos, traços, etc.)
    cpf_resp = "".join(filter(str.isdigit, cpf_resp))  
    # Ajusta para 11 dígitos
    cpf_resp = cpf_resp.zfill(11)
    cpf_resp = cpf_resp[:11]

    # 11) 32 colunas preenchidas com "0"  ***********
    zero_32 = "0" * 32

    # 12) 218 colunas em branco  ***********
    branco_217 = " " * 217

    # Montar a linha inicial 
    linha_inicial = (
        dimob +         # 5 col
        branco_7 +      # 7 col
        ano_cal +       # 4 col
        zero_5 +        # 5 col
        cnpj +   # 14 col
        zero_4 +
        nome_emp +      # 60 col
        uf_r01 +        # 2 col
        zero_13 +       # 13 col
        cpf_resp +      # 11 col
        zero_32 +       # 32 col
        branco_217      # 217 col
    )

    linhas = [linha_inicial]

   
    # Processamento (R01 / R03)

    for _, row in df_r01.iterrows():
        if str(row.get("tipo", "")).upper() == "R01":
            linhas.append(parse_R01_row(row))

    for _, row in df_r03.iterrows():
        if str(row.get("tipo", "")).upper() == "R03":
            linhas.append(parse_R03_row(row))

# =========================================================================
# Adicionando a linha T9 após o último R03
# =========================================================================
    
    tipo_t9 = "T9"  

    branco_101 = " " * 100

    linha_t9 = tipo_t9 + branco_101

    linhas.append(linha_t9)

    return "\n".join(linhas) + "\n"

# =============================================================================
# Regras de Negócio para o R01
# =============================================================================

def parse_R01_row(row):

    # 1) tipo (tamanho 3) - obrigatório
    tipo = get_str(row, "tipo", required=True)
    tipo = fix_length(tipo, 3, pad_char=' ', align='left', truncate=True)

    # 2) cnpj_do_declarante (14) - obrigatório
    cnpj = get_str(row, "cnpj_do_declarante", required=True)  
    cnpj = "".join(filter(str.isdigit, cnpj)) 
    cnpj = cnpj.zfill(14)  
    cnpj = fix_length(cnpj, 14, pad_char=' ', align='left', truncate=True)

    # 3) ano_calendario (4) - obrigatório
    ano_cal = get_str(row, "ano_calendario", required=True)
    if len(ano_cal) != 4:
        raise ValueError(f"Ano calendário deve ter 4 dígitos: {ano_cal}")
    ano_cal = fix_length(ano_cal, 4, pad_char=' ', align='left', truncate=True)

    # 4) declaracao_retificadora (1) - '0' ou '1'
    decl_ret = get_str(row, "declaracao_retificadora", required=True)
    if decl_ret not in ["0", "1"]:
        raise ValueError(f"Declaracao retificadora deve ser '0' ou '1': {decl_ret}")
    decl_ret = fix_length(decl_ret, 1)

    # 5) numero_do_recibo (10) - obrigatório
    num_recibo = get_str(row, "numero_do_recibo", required=True)
    num_recibo = num_recibo.rjust(10, '0')  # zeros à esquerda até 10
    num_recibo = num_recibo[:10]           # se exceder 10, trunca

    # 6) situacao_especial (1) - '0' ou '1'
    sit_esp = get_str(row, "situacao_especial", required=True)
    if sit_esp not in ["0", "1"]:
        raise ValueError(f"Situacao especial deve ser '0' ou '1': {sit_esp}")
    sit_esp = fix_length(sit_esp, 1)

    # 7) data_do_evento_situacao_especial (8) - obrigatório (ddmmaaaa)
    data_evento = get_str(row, "data_do_evento_situacao_especial", required=False).strip()

    # Se estiver em branco ou contiver valores inválidos, atribui "00000000"
    if not data_evento or data_evento.strip() in ["", " ", "0", "000000", "00000000", None]:
        data_evento = "00000000"
    else:
        try:
            data_evento = formata_data_ddmmaaaa(data_evento)
        except ValueError:
            data_evento = "00000000"  # Se a conversão falhar, forçar o "00000000"

    # Lança erro 
    if len(data_evento) != 8 or not data_evento.isdigit():
        raise ValueError(f"Data do evento inválida (esperado ddmmaaaa): {data_evento}")


    # 8) codigo_da_situacao_especial (2) - "00", "02", "03" ou "04"
    cod_sit_esp = get_str(row, "codigo_da_situacao_especial", required=True)
    mapa_codigos = {"0": "00", "2": "02", "3": "03", "4": "04"}
    cod_sit_esp_mapeado = mapa_codigos.get(str(cod_sit_esp).strip(), None)
    if cod_sit_esp_mapeado is None:
        raise ValueError(f"Código da situação especial inválido: {cod_sit_esp}")
    cod_sit_esp = fix_length(cod_sit_esp_mapeado, 2)

    # 9) nome_empresarial (60) - obrigatório
    nome_emp = get_str(row, "nome_empresarial", required=True)
    nome_emp = fix_length(nome_emp, 60, pad_char=' ', align='left', truncate=True)

    # 10) cpf_do_responsavel (11) - obrigatório
    cpf_resp = get_str(row, "cpf_do_responsavel_pela_pessoa_juridica_perante_a_rfb", required=True)
    cpf_resp = "".join(filter(str.isdigit, cpf_resp))
    cpf_resp = cpf_resp.zfill(11)

    if len(cpf_resp) != 11:
        raise ValueError(f"CPF inválido: {cpf_resp} (deve ter exatamente 11 dígitos)")

    # Garante 11 caracteres
    cpf_resp = fix_length(cpf_resp, 11, pad_char=' ', align='left', truncate=True)

    # 11) endereco_completo_do_contribuinte (120) - obrigatório
    endereco = get_str(row, "endereco_completo_do_contribuinte", required=True)
    endereco = fix_length(endereco, 120, pad_char=' ', align='left', truncate=True)

    # 12) uf_do_contribuinte (2) - obrigatório
    uf = get_str(row, "uf_do_contribuinte", required=True)
    uf = fix_length(uf, 2, pad_char=' ', align='left', truncate=True)

    # 13) codigo_do_municipio_do_contribuinte (4) - obrigatório
    cod_mun = get_str(row, "codigo_do_municipio_do_contribuinte", required=True)
    cod_mun = cod_mun.strip().zfill(4)
    cod_mun = fix_length(cod_mun, 4, pad_char=' ', align='left', truncate=True)

    # 14) reservado (20) - obrigatório
    reservado_1 = ' ' * 20

    # 15) reservado (9) - obrigatório
    reservado_2 = ' ' * 9

    # 16) delimitador_de_registro (2)
    delim = " " * 1

    linha = (
        tipo +
        cnpj +
        ano_cal +
        decl_ret +
        num_recibo +
        sit_esp +
        data_evento +
        cod_sit_esp +
        nome_emp +
        cpf_resp +
        endereco +
        uf +
        cod_mun +
        reservado_1 +
        reservado_2 +
        delim
    )
    return linha


# =============================================================================
# Regras de Negócio para o R03
# =============================================================================

def parse_R03_row(row):

    linhas=[]

    # 1) tipo (3)
    tipo = get_str(row, "tipo", required=True)
    tipo = fix_length(tipo, 3, pad_char=' ', align='left', truncate=True)

    # 2) cnpj_do_declarante (14)
    cnpj = get_str(row, "cnpj_do_declarante", required=True)
    cnpj = "".join(filter(str.isdigit, cnpj))  # remove pontuação
    cnpj = cnpj.zfill(14)
    cnpj = fix_length(cnpj, 14, pad_char=' ', align='left', truncate=True)

    # 3) ano_calendario (4)
    ano_cal = get_str(row, "ano_calendario", required=True)
    if len(ano_cal) != 4:
        raise ValueError(f"Ano calendário deve ter 4 dígitos: {ano_cal}")
    ano_cal = fix_length(ano_cal, 4, pad_char=' ', align='left', truncate=True)

    # 4) sequencial_da_venda (7)
    if not hasattr(parse_R03_row, "_seq_counter"):
        parse_R03_row._seq_counter = 0

    sequencial = get_str(row, "sequencial_da_venda", required=False).strip()

    if not sequencial:
        parse_R03_row._seq_counter += 1
        sequencial_int = parse_R03_row._seq_counter
    else:
        if not sequencial.isdigit():
            raise ValueError(f"Sequencial da venda inválido: {sequencial} (deve conter apenas números)")
        sequencial_int = int(sequencial)
        if not (1 <= sequencial_int <= 9999999):
            raise ValueError(f"Sequencial da venda fora do intervalo permitido: {sequencial_int}")
        parse_R03_row._seq_counter = sequencial_int

    sequencial = str(sequencial_int).zfill(7)

    # 5) cpf_cnpj_comprador (14) - Pode ser CPF ou CNPJ
    cpf_cnpj_comprador = get_str(row, "cpf_cnpj_do_comprador", required=True)

    # Remove tudo que não for número
    cpf_cnpj_comprador = "".join(filter(str.isdigit, cpf_cnpj_comprador))

    # Se for CPF (menos de 11 dígitos), completa com 0 à esquerda até 11 e adiciona 3 espaços no final
    if len(cpf_cnpj_comprador) < 11:
        cpf_cnpj_comprador = cpf_cnpj_comprador.zfill(11) + "   "  # 3 espaços no final

    # Se for CPF (exatamente 11 dígitos), adiciona 3 espaços no final para completar 14
    elif len(cpf_cnpj_comprador) == 11:
        cpf_cnpj_comprador = cpf_cnpj_comprador + "   "  # 3 espaços no final

    # Se for CNPJ (menos de 14 dígitos), completa com 0 à esquerda até 14
    elif len(cpf_cnpj_comprador) < 14:
        cpf_cnpj_comprador = cpf_cnpj_comprador.zfill(14)

    # Se não for CPF (11) nem CNPJ (14), lança erro
    elif len(cpf_cnpj_comprador) not in [11, 14]:
        raise ValueError(f"CPF/CNPJ inválido: {cpf_cnpj_comprador} (deve ter 11 ou 14 dígitos)")

    # Garante que o campo tenha exatamente 14 caracteres
    cpf_cnpj_comprador = fix_length(cpf_cnpj_comprador, 14, pad_char=' ', align='left', truncate=True)


    # 6) nome_empresarial_do_comprador (60)
    nome_emp = get_str(row, "nome_empresarial_do_comprador", required=True)
    nome_emp = fix_length(nome_emp, 60, pad_char=' ', align='left', truncate=True)

    # 7) numero_do_contrato (6) - Deve ter exatamente 6 dígitos
    num_contrato = get_str(row, "numero_do_contrato", required=True).strip()

    # Remove tudo que não for número
    num_contrato = "".join(filter(str.isdigit, num_contrato))

    # Se tiver mais de 6 dígitos, remove os 3 primeiros à esquerda
    if len(num_contrato) > 6:
        num_contrato = num_contrato[-6:]

    # Se tiver menos de 6, completa com 0 à esquerda
    num_contrato = num_contrato.zfill(6)

    # Garantia final que tenha exatamente 6 caracteres
    if len(num_contrato) != 6:
        raise ValueError(f"Número do contrato inválido: {num_contrato} (deve ter exatamente 6 dígitos)")

    # 8) data_do_contrato (8) (ddmmaaaa)
    data_contrato = get_str(row, "data_do_contrato", required=True)
    data_contrato = formata_data_ddmmaaaa(data_contrato)
    if len(data_contrato) != 8:
        raise ValueError(f"Data do evento inválida (esperado ddmmaaaa): {data_contrato}")

    from decimal import Decimal
  

    # 9) valor_da_operacao
    valor_op_raw = get_str(row, "valor_da_operacao", required=True)

    valor_op_limpo = re.sub(r"\.(?=\d{3},)", "", valor_op_raw)

    try:
        # Troca a vírgula (decimal) por ponto, depois cria Decimal
        valor_op_decimal = Decimal(valor_op_limpo.replace(",", "."))
    except:
        raise ValueError(f"Valor da operação inválido: {valor_op_raw}")

    # Se quiser armazenar sempre duas casas decimais, multiplica por 100 antes de converter em int
    valor_op_int = int(valor_op_decimal * 100)

    # Garante 14 dígitos, com zeros à esquerda
    valor_op_str = str(valor_op_int).zfill(14)

    # Checagem de limite
    if len(valor_op_str) > 14:
        raise ValueError(f"Valor da operação ({valor_op_str}) ultrapassa 14 dígitos. Ajuste o valor.")


    # 10) valor_pago_no_ano
    valor_pago_raw = get_str(row, "valor_pago_no_ano", required=True)

    def formatar_valor(valor_raw):
        """Remove pontos de milhar, converte para Decimal e transforma em string de 14 dígitos."""
        
        # Remove apenas pontos de milhar (mantém a vírgula decimal)
        valor_limpo = re.sub(r"\.(?=\d{3},)", "", valor_raw)

        try:
            # Troca a vírgula decimal por ponto e converte para Decimal
            valor_decimal = Decimal(valor_limpo.replace(",", "."))
        except:
            raise ValueError(f"Valor inválido: {valor_raw}")

        # Converte para centavos multiplicando por 100
        valor_int = int(valor_decimal * 100)

        # Formata com 14 dígitos e zeros à esquerda
        valor_str = str(valor_int).zfill(14)

        # Checa limite de 14 caracteres
        if len(valor_str) > 14:
            raise ValueError(f"Valor ({valor_str}) ultrapassa 14 dígitos. Ajuste o valor.")

        return valor_str

    # Aplica a formatação para os dois valores
    valor_op_str = formatar_valor(valor_op_raw)
    valor_pago_str = formatar_valor(valor_pago_raw)

    # 11) tipo_do_imovel (1 caractere)
    tipo_imovel = get_str(row, "tipo_do_imovel", required=True).upper().strip()
    if tipo_imovel not in ["U", "R"]:
        raise ValueError(f"Tipo do imóvel inválido: {tipo_imovel}. Deve ser 'U' ou 'R'.")
    tipo_imovel = fix_length(tipo_imovel, 1, pad_char=' ', align='left', truncate=True)

    # 12) endereco_do_imovel (60)
    endereco_imovel = get_str(row, "endereco_do_imovel", required=True)
    endereco_imovel = fix_length(endereco_imovel, 60, pad_char=' ', align='left', truncate=True)

    # 13) cep (8)
    cep = get_str(row, "cep", required=True)
    cep = "".join(filter(str.isdigit, cep))  
    try:
        cep_int = int(cep)
    except ValueError:
        raise ValueError(f"CEP inválido: {cep}")
    if len(cep) > 8:
        raise ValueError(f"CEP muito longo: {cep}")
    cep = str(cep_int).zfill(8)

    # 14) codigo_do_municipio_do_imovel (4)
    cod_mun_imovel = get_str(row, "codigo_do_municipio_do_imovel", required=True)
    cod_mun_imovel = cod_mun_imovel.strip().zfill(4)
    cod_mun_imovel = fix_length(cod_mun_imovel, 4, pad_char=' ', align='left', truncate=True)

    # 15) reservado (20 espaços)
    reservado_1 = " " * 20

    # 16) uf (2)
    uf = get_str(row, "uf", required=False)
    uf = fix_length(uf, 2, pad_char=' ', align='left', truncate=True) if uf else "  "

    # 17) reservado (9 espaços)
    reservado_2 = " " * 9

    # 18) delimitador_de_registro (coloquei 1 espaço para inteirar 272)
    delimitador = " " * 1

    linha = (
        tipo + cnpj + ano_cal + sequencial +
        cpf_cnpj_comprador + nome_emp + num_contrato + data_contrato +
        valor_op_str + valor_pago_str + tipo_imovel + endereco_imovel +
        cep + cod_mun_imovel + reservado_1 + uf +
        reservado_2 + delimitador
    )
    return linha


# =============================================================================
# Funções utilitárias
# =============================================================================

def get_str(row, column_name, required=False):
    val = row.get(column_name, "")
    if pd.isnull(val):
        val = ""
    val = str(val).strip()
    if required and not val:
        raise ValueError(f"Campo obrigatório '{column_name}' está vazio.")
    return val

def fix_length(text, length, pad_char=' ', align='left', truncate=True):
    if truncate and len(text) > length:
        text = text[:length]

    if align == 'left':
        text = text.ljust(length, pad_char)
    else:
        text = text.rjust(length, pad_char)
    return text

def formata_data_ddmmaaaa(data_str):
    if not data_str or str(data_str).strip() in ["0", ""]:
        return "00000000"
    try:
        dt = pd.to_datetime(data_str, dayfirst=False, errors='raise')
        return dt.strftime('%d%m%Y')
    except:
        raise ValueError(f"Data inválida: {data_str}")
