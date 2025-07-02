import streamlit as st
import json
import os
from datetime import datetime
from PIL import Image

class SistemaFinanceiro:
    def __init__(self):
        self.dados = {
            'faturamentos': [],
            'custos': {'categorias': {}},
            'lucros': []
        }
        self.carregar_dados()

    def carregar_dados(self):
        if os.path.exists('dados_financeiros.json'):
            with open('dados_financeiros.json', 'r') as f:
                self.dados = json.load(f)

    def salvar_dados(self):
        with open('dados_financeiros.json', 'w') as f:
            json.dump(self.dados, f, indent=4)

    def adicionar_faturamento(self, valor, descricao, data=None):
        if data is None:
            data = datetime.now().strftime('%Y-%m-%d')
        
        self.dados['faturamentos'].append({
            'valor': float(valor),
            'descricao': descricao,
            'data': data
        })
        self.salvar_dados()
        self.calcular_lucros()

    def adicionar_custo(self, categoria, valor, descricao, data=None, subcategoria=None):
        if data is None:
            data = datetime.now().strftime('%Y-%m-%d')
        
        registro = {
            'valor': float(valor),
            'descricao': descricao,
            'data': data
        }
        
        if subcategoria:
            if categoria not in self.dados['custos']['categorias']:
                self.dados['custos']['categorias'][categoria] = {'subcategorias': {}}
            
            if 'subcategorias' not in self.dados['custos']['categorias'][categoria]:
                self.dados['custos']['categorias'][categoria]['subcategorias'] = {}
                
            if subcategoria not in self.dados['custos']['categorias'][categoria]['subcategorias']:
                self.dados['custos']['categorias'][categoria]['subcategorias'][subcategoria] = []
            
            self.dados['custos']['categorias'][categoria]['subcategorias'][subcategoria].append(registro)
        else:
            if categoria not in self.dados['custos']['categorias']:
                self.dados['custos']['categorias'][categoria] = {'registros': []}
            
            if 'registros' not in self.dados['custos']['categorias'][categoria]:
                self.dados['custos']['categorias'][categoria]['registros'] = []
                
            self.dados['custos']['categorias'][categoria]['registros'].append(registro)
        
        self.salvar_dados()
        self.calcular_lucros()

    def calcular_lucros(self):
        total_faturamento = sum(f['valor'] for f in self.dados['faturamentos'])
        total_custos = self.calcular_total_custos()
        
        lucro = total_faturamento - total_custos
        
        self.dados['lucros'].append({
            'data': datetime.now().strftime('%Y-%m-%d'),
            'lucro': lucro,
            'faturamento_total': total_faturamento,
            'custos_total': total_custos
        })
        self.salvar_dados()

    def calcular_total_custos(self):
        total = 0
        for categoria, dados in self.dados['custos']['categorias'].items():
            if 'registros' in dados:
                total += sum(r['valor'] for r in dados['registros'])
            if 'subcategorias' in dados:
                for subcat, registros in dados['subcategorias'].items():
                    total += sum(r['valor'] for r in registros)
        return total

    def distribuir_custos_porcentagem(self, categoria, porcentagens):
        total = sum(p for p in porcentagens.values())
        if abs(total - 100) > 0.01:
            st.error(f"Erro: A soma das porcentagens deve ser 100% (atual: {total}%)")
            return
        
        for subcat, porcentagem in porcentagens.items():
            valor_total_categoria = self.calcular_total_categoria(categoria)
            valor_subcat = valor_total_categoria * (porcentagem / 100)
            self.adicionar_custo(categoria, valor_subcat, f"Alocação de {porcentagem}% para {subcat}", subcategoria=subcat)
        st.success("Custos distribuídos com sucesso!")

    def calcular_total_categoria(self, categoria):
        total = 0
        if categoria in self.dados['custos']['categorias']:
            dados = self.dados['custos']['categorias'][categoria]
            if 'registros' in dados:
                total += sum(r['valor'] for r in dados['registros'])
            if 'subcategorias' in dados:
                for subcat, registros in dados['subcategorias'].items():
                    total += sum(r['valor'] for r in registros)
        return total

def main():
    # Configuração da página
    st.set_page_config(page_title="Sistema Financeiro", layout="wide")
    
    # Cria uma instância do sistema financeiro
    sistema = SistemaFinanceiro()
    
    # Sidebar com logo fixa e menu
    with st.sidebar:
        # ======================================================
        # INSIRA O CAMINHO DA SUA LOGO AQUI (ex: "assets/logo.png")
        caminho_logo = "https://github.com/eFlow-hub/Gestor_Financeiro_e-flow/blob/main/I%CC%81cone%20Color.png?raw=true" 
        # ======================================================
        
        try:
            logo = Image.open(caminho_logo)
            # Tamanho ajustado para 150px (você pode alterar este valor)
            st.image(logo, width=150)
        except:
            st.warning(f"Logo não encontrada em: {caminho_logo}")
        
        st.title("Menu")
        menu = st.radio("Navegação", 
                       ["Dashboard", "Adicionar Faturamento", "Adicionar Custo", 
                        "Distribuir Custos", "Relatório Completo"])
    
    # Página principal
    st.title("Sistema Financeiro da Empresa")
    
    if menu == "Dashboard":
        st.header("📊 Dashboard Financeiro")
        
        if sistema.dados['lucros']:
            ultimo_lucro = sistema.dados['lucros'][-1]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Faturamento Total", f"R${ultimo_lucro['faturamento_total']:,.2f}")
            with col2:
                st.metric("Custos Total", f"R${ultimo_lucro['custos_total']:,.2f}")
            with col3:
                lucro_color = "green" if ultimo_lucro['lucro'] >= 0 else "red"
                st.metric("Lucro", f"R${ultimo_lucro['lucro']:,.2f}", delta_color="off")
        
        st.subheader("Últimos Faturamentos")
        if sistema.dados['faturamentos']:
            for fat in reversed(sistema.dados['faturamentos'][-5:]):
                st.write(f"📈 {fat['data']} - {fat['descricao']}: R${fat['valor']:,.2f}")
        else:
            st.info("Nenhum faturamento registrado ainda.")
        
        st.subheader("Últimos Custos")
        custos_recentes = []
        for categoria, dados in sistema.dados['custos']['categorias'].items():
            if 'registros' in dados:
                for reg in dados['registros'][-3:]:
                    custos_recentes.append((reg['data'], categoria, None, reg['descricao'], reg['valor']))
            if 'subcategorias' in dados:
                for subcat, registros in dados['subcategorias'].items():
                    for reg in registros[-3:]:
                        custos_recentes.append((reg['data'], categoria, subcat, reg['descricao'], reg['valor']))
        
        custos_recentes.sort(reverse=True)
        for data, cat, subcat, desc, valor in custos_recentes[:5]:
            if subcat:
                st.write(f"📉 {data} - {cat} > {subcat}: {desc} - R${valor:,.2f}")
            else:
                st.write(f"📉 {data} - {cat}: {desc} - R${valor:,.2f}")
        
        if not custos_recentes:
            st.info("Nenhum custo registrado ainda.")
    
    elif menu == "Adicionar Faturamento":
        st.header("💵 Adicionar Faturamento")
        
        with st.form("faturamento_form"):
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            descricao = st.text_input("Descrição")
            data = st.date_input("Data", datetime.now())
            
            if st.form_submit_button("Adicionar Faturamento"):
                sistema.adicionar_faturamento(valor, descricao, str(data))
                st.success("Faturamento adicionado com sucesso!")
    
    elif menu == "Adicionar Custo":
        st.header("💸 Adicionar Custo")
        
        with st.form("custo_form"):
            categoria = st.text_input("Categoria")
            subcategoria = st.text_input("Subcategoria (opcional)")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            descricao = st.text_input("Descrição")
            data = st.date_input("Data", datetime.now())
            
            if st.form_submit_button("Adicionar Custo"):
                sistema.adicionar_custo(
                    categoria, 
                    valor, 
                    descricao, 
                    str(data), 
                    subcategoria if subcategoria else None
                )
                st.success("Custo adicionado com sucesso!")
    
    elif menu == "Distribuir Custos":
        st.header("📊 Distribuir Custos por Porcentagem")
        
        categorias = list(sistema.dados['custos']['categorias'].keys())
        if not categorias:
            st.warning("Nenhuma categoria de custo disponível. Adicione custos primeiro.")
        else:
            categoria = st.selectbox("Selecione a categoria para distribuição", categorias)
            
            st.subheader(f"Distribuição para: {categoria}")
            st.write(f"Total atual na categoria: R${sistema.calcular_total_categoria(categoria):,.2f}")
            
            subcategorias = {}
            with st.form("distribuicao_form"):
                st.write("Adicione as subcategorias e porcentagens (total deve ser 100%)")
                
                col1, col2 = st.columns(2)
                with col1:
                    subcat1 = st.text_input("Subcategoria 1")
                    p1 = st.number_input("Porcentagem 1", min_value=0.0, max_value=100.0, step=0.1)
                with col2:
                    subcat2 = st.text_input("Subcategoria 2")
                    p2 = st.number_input("Porcentagem 2", min_value=0.0, max_value=100.0, step=0.1)
                
                col3, col4 = st.columns(2)
                with col3:
                    subcat3 = st.text_input("Subcategoria 3")
                    p3 = st.number_input("Porcentagem 3", min_value=0.0, max_value=100.0, step=0.1)
                with col4:
                    subcat4 = st.text_input("Subcategoria 4")
                    p4 = st.number_input("Porcentagem 4", min_value=0.0, max_value=100.0, step=0.1)
                
                if st.form_submit_button("Distribuir Custos"):
                    porcentagens = {}
                    if subcat1 and p1 > 0:
                        porcentagens[subcat1] = p1
                    if subcat2 and p2 > 0:
                        porcentagens[subcat2] = p2
                    if subcat3 and p3 > 0:
                        porcentagens[subcat3] = p3
                    if subcat4 and p4 > 0:
                        porcentagens[subcat4] = p4
                    
                    sistema.distribuir_custos_porcentagem(categoria, porcentagens)
    
    elif menu == "Relatório Completo":
        st.header("📑 Relatório Financeiro Completo")
        
        # Faturamentos
        st.subheader("Faturamentos")
        if sistema.dados['faturamentos']:
            for fat in sistema.dados['faturamentos']:
                st.write(f"📅 {fat['data']} - {fat['descricao']}: R${fat['valor']:,.2f}")
            total_fat = sum(f['valor'] for f in sistema.dados['faturamentos'])
            st.success(f"Total Faturamento: R${total_fat:,.2f}")
        else:
            st.info("Nenhum faturamento registrado ainda.")
        
        # Custos
        st.subheader("Custos")
        if sistema.dados['custos']['categorias']:
            for categoria, dados in sistema.dados['custos']['categorias'].items():
                with st.expander(f"Categoria: {categoria}"):
                    if 'registros' in dados:
                        st.write("**Custos diretos:**")
                        for reg in dados['registros']:
                            st.write(f"- {reg['data']} - {reg['descricao']}: R${reg['valor']:,.2f}")
                    
                    if 'subcategorias' in dados:
                        st.write("**Subcategorias:**")
                        for subcat, registros in dados['subcategorias'].items():
                            total_sub = sum(r['valor'] for r in registros)
                            with st.expander(f"{subcat} (R${total_sub:,.2f})"):
                                for reg in registros:
                                    st.write(f"- {reg['data']} - {reg['descricao']}: R${reg['valor']:,.2f}")
            
            total_custos = sistema.calcular_total_custos()
            st.error(f"Total Custos: R${total_custos:,.2f}")
        else:
            st.info("Nenhum custo registrado ainda.")
        
        # Lucros
        st.subheader("Lucros")
        if sistema.dados['lucros']:
            ultimo_lucro = sistema.dados['lucros'][-1]
            st.metric("Último Cálculo de Lucro", 
                     f"R${ultimo_lucro['lucro']:,.2f}", 
                     delta=f"Faturamento: R${ultimo_lucro['faturamento_total']:,.2f} | Custos: R${ultimo_lucro['custos_total']:,.2f}")
            
            st.write("Histórico de Lucros:")
            for lucro in reversed(sistema.dados['lucros']):
                st.write(f"📅 {lucro['data']} - Lucro: R${lucro['lucro']:,.2f}")
        else:
            st.info("Nenhum cálculo de lucro disponível.")

if __name__ == "__main__":
    main()
