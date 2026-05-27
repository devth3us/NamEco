from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pymysql
from calc.carb import calc_emissoes
import os
from werkzeug.utils import secure_filename
from calc.carb import calc_emissoes, processar_excel 




app = Flask(__name__)
app.secret_key = 'cnamdndnams'

UPLOAD_FOLDER = 'temp_uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 


def get_bd():
    return pymysql.connect(
        host='localhost',          
        user='root',              
        password='Math8080@', 
        database='diag_esg',
        cursorclass=pymysql.cursors.DictCursor 
    )




@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        try:
            con = get_bd()
            with con.cursor() as cur:
                # Busca o usurio pelo e-mail
                cur.execute("SELECT * FROM usr WHERE email = %s", (email,))
                usr = cur.fetchone()
            con.close()
            
            
            if usr and usr['senha'] == senha:
                session['id_usr'] = usr['id_usr']
                session['id_emp'] = usr['id_emp']
                session['nm_usr'] = usr['nm_usr']
                return redirect(url_for('pnl'))
            else:
                flash('E-mail ou senha incorretos. Tente novamente.')
                
        except Exception as e:
            flash(f'Erro ao conectar no banco de dados: {e}')
            
    return render_template('login.html')

# sair
@app.route('/sair')
def sair():
    session.clear() 
    return redirect(url_for('login'))




@app.route('/pnl')
def pnl():
    if 'id_usr' not in session:
        return redirect(url_for('login'))
    
    # Busca o historico para preencher a tabela do DataTables
    con = get_bd()
    with con.cursor() as cur:
        cur.execute('''
            select dt_ref, cons_ee, comb_lt, res_kg 
            from reg 
            where id_emp = %s 
            order by dt_ref desc
        ''', (session['id_emp'],))
        historico = cur.fetchall()
    con.close()
        
    return render_template('pnl.html', nm_usr=session['nm_usr'], historico=historico)


@app.route('/api/dados')
def api_dados():
    if 'id_emp' not in session:
        return jsonify({"erro": "Não autorizado"}), 403

    try:
        con = get_bd()
        with con.cursor() as cur:
            # Seleciona todos os meses inseridos da empresa atual de forma ordenada
            cur.execute('''
                select dt_ref, cons_ee, comb_lt, res_kg 
                from reg 
                where id_emp = %s 
                order by dt_ref ASC
            ''', (session['id_emp'],))
            dados = cur.fetchall()
        con.close()

       
        resultado = calc_emissoes(dados)
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({"erro": f"Erro interno no processamento: {e}"}), 500

# Recebe as informaçoes do formulario e insere no banco
@app.route('/add_reg', methods=['POST'])
def add_reg():
    if 'id_usr' not in session:
        return redirect(url_for('login'))

    # Coleta as variaveis vindas do formulario html
    dt_ref = request.form['dt_ref']
    cons_ee = float(request.form['cons_ee'])
    comb_lt = float(request.form['comb_lt'])
    res_kg = float(request.form['res_kg'])

    try:
        con = get_bd()
        with con.cursor() as cur:
            cur.execute('''
                insert into reg (id_emp, id_usr, dt_ref, cons_ee, comb_lt, res_kg) 
                values (%s, %s, %s, %s, %s, %s)
            ''', (session['id_emp'], session['id_usr'], dt_ref, cons_ee, comb_lt, res_kg))
        con.commit()
        con.close()
    except Exception as e:
        print(f"Erro ao salvar registro: {e}")
      
    return redirect(url_for('pnl'))






@app.route('/importar', methods=['POST'])
def importar():
    if 'id_usr' not in session:
        return redirect(url_for('login'))
        
    if 'planilha' not in request.files:
        flash('Nenhum arquivo enviado.')
        return redirect(url_for('pnl'))
        
    arquivo = request.files['planilha']
    if arquivo.filename == '':
        flash('Nenhum arquivo selecionado.')
        return redirect(url_for('pnl'))
        
    # Validação de Formato 
    if arquivo and (arquivo.filename.endswith('.xlsx') or arquivo.filename.endswith('.xls')):
        nome_seguro = secure_filename(arquivo.filename)
        caminho_salvo = os.path.join(app.config['UPLOAD_FOLDER'], nome_seguro)
        arquivo.save(caminho_salvo)
        
        # Executa os dados do Pandas
        con = get_bd()
        sucesso, msg = processar_excel(caminho_salvo, session['id_emp'], session['id_usr'], con)
        con.close()
        
        # Remove o arquivo fisico temporário da sua máquina/servidor aps salvar no banco
        if os.path.exists(caminho_salvo):
            os.remove(caminho_salvo)
            
        flash(msg)
    else:
        flash('Formato inválido! O NesmEco aceita apenas arquivos .xlsx (Excel).')
        
    return redirect(url_for('pnl'))





if __name__ == '__main__':
    app.run(debug=True)