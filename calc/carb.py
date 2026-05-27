import pandas as pd

# Fatores de emissão 
FATOR_EE = 0.085   # kg CO2 / kWh
FATOR_COMB = 2.68  # kg CO2 / Litro
FATOR_RES = 0.45   # kg CO2 / Kg 

def calc_emissoes(dados_banco):
    if not dados_banco:
        return {
            "meses": [], "co2_totais": [], "total_geral": 0,
            "escopo1": 0, "escopo2": 0, "escopo3": 0
        }

    df = pd.DataFrame(dados_banco)

    # Cálculo dos Escopos GHG Protocol
    df['escopo1_co2'] = df['comb_lt'] * FATOR_COMB  # Emissões Diretas
    df['escopo2_co2'] = df['cons_ee'] * FATOR_EE    # Energia Indireta
    df['escopo3_co2'] = df['res_kg'] * FATOR_RES    # Cadeia de Valor (Resíduos)
    
    # Total da linha (mês)
    df['co2_tot'] = df['escopo1_co2'] + df['escopo2_co2'] + df['escopo3_co2']

    # Evolução temporal para o Gráfico de Linha
    resumo_mensal = df.groupby('dt_ref')['co2_tot'].sum().reset_index()

    # Totais absolutos para o Gráfico de Rosca (GHG Protocol Compliance)
    tot_escopo1 = round(df['escopo1_co2'].sum(), 2)
    tot_escopo2 = round(df['escopo2_co2'].sum(), 2)
    tot_escopo3 = round(df['escopo3_co2'].sum(), 2)
    total_geral = round(tot_escopo1 + tot_escopo2 + tot_escopo3, 2)

    return {
        "meses": resumo_mensal['dt_ref'].tolist(),
        "co2_totais": [round(val, 2) for val in resumo_mensal['co2_tot'].tolist()],
        "total_geral": total_geral,
        "escopo1": tot_escopo1,
        "escopo2": tot_escopo2,
        "escopo3": tot_escopo3
    }



def processar_excel(caminho_arquivo, id_emp, id_usr, con):
    try:
        df = pd.read_excel(caminho_arquivo)
        
        # Garante que a planilha segue o padrão do sistema NesmEco
        colunas_obrigatorias = ['dt_ref', 'cons_ee', 'comb_lt', 'res_kg']
        for col in colunas_obrigatorias:
            if col not in df.columns:
                return False, f"Erro: A coluna obrigatória '{col}' não foi encontrada na planilha."
        
       
        df = df.fillna(0)
        
        # Insercao em Massa no MySQL
        with con.cursor() as cur:
            for _, linha in df.iterrows():
                cur.execute('''
                    INSERT INTO reg (id_emp, id_usr, dt_ref, cons_ee, comb_lt, res_kg)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    id_emp, 
                    id_usr, 
                    str(linha['dt_ref']),      # Ex: "2026-01"
                    float(linha['cons_ee']),   # Energia
                    float(linha['comb_lt']),   # Combustível
                    float(linha['res_kg'])     # Residuos
                ))
        con.commit()
        return True, f"Sucesso! {len(df)} registros importados e processados pelo Pandas."
        
    except Exception as e:
        return False, f"Erro crítico ao processar o Excel: {str(e)}"