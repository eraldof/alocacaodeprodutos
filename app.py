"""
Aplicativo Streamlit para otimização de empacotamento 3D em gaiolas ou contêineres.
Calcula a disposição ótima de produtos retangulares em um espaço retangular.
"""

import streamlit as st
from optimizer import Container, Product, PackingOptimizer
from visualization import visualize_static, visualize_interactive


def display_optimization_results(st_obj, comprimento, profundidade, altura, results, eficiencia):
    """
    Função para exibir os resultados da otimização de forma padronizada.
    
    Args:
        st_obj: Objeto Streamlit para exibição
        comprimento: Comprimento do produto
        profundidade: Profundidade do produto
        altura: Altura do produto
        results: Dicionário com resultados da otimização
        eficiencia: Porcentagem de eficiência de preenchimento calculada
    """
    st_obj.markdown(f"**Dimensões:** {comprimento}m × {profundidade}m × {altura}m")
    
    if results["best_count"] > 0:
        st_obj.markdown(f"**Melhor orientação:** {results['best_orientation']}m")
        st_obj.markdown(f"**Distribuição (x,y,z):** {results['best_distribution']}")
        st_obj.markdown(f"**Total de produtos:** {results['best_count']}")
        st_obj.markdown(f"**Eficiência de preenchimento:** {eficiencia:.2f}%")
        st_obj.markdown(f"**Quantos cm ficaria p/ fora do rack:** {results['overflow_y']:.2f}cm")
    else:
        st_obj.error("Nenhuma configuração possível para este produto no contêiner.")
    
    # Exibir log detalhado
    with st_obj.expander("Ver detalhes de cálculo"):
        st_obj.text(results["log_text"])


def calculate_optimization():
    """Executa os cálculos de otimização e armazena os resultados no session_state"""
    
    # Obter os parâmetros do session_state
    container_x = st.session_state.container_x
    container_y = st.session_state.container_y
    container_z = st.session_state.container_z
    y_tolerance = st.session_state.y_tolerance
    comprimento = st.session_state.comprimento
    profundidade = st.session_state.profundidade
    altura = st.session_state.altura
    travar_altura = st.session_state.travar_altura
    
    # Criar o contêiner
    container = Container(
        x=container_x,
        y=container_y,
        z=container_z,
        y_tolerance=y_tolerance
    )
    
    # Criar o produto
    product = Product(
        comprimento,
        profundidade,
        altura
    )
    
    # Criar e executar o otimizador
    optimizer = PackingOptimizer(container, product, travar_altura)
    results = optimizer.optimize()
    
    # Calcular eficiência de preenchimento
    volume_container = container_x * container_y * container_z
    volume_produto = comprimento * profundidade * altura
    volume_ocupado = results["best_count"] * volume_produto
    eficiencia = (volume_ocupado / volume_container) * 100 if volume_container > 0 else 0
    
    # Armazenar resultados no session_state
    st.session_state.optimizer = optimizer
    st.session_state.results = results
    st.session_state.eficiencia = eficiencia
    st.session_state.calculation_done = True


def calculate_streamlit():
    """Função principal para executar a otimização de empacotamento no Streamlit."""
    
    st.title("Otimizador de Empacotamento 3D")
    
    # Inicializar session_state se necessário
    if 'calculation_done' not in st.session_state:
        st.session_state.calculation_done = False
    
    # Botão para calcular (agora no topo)
    st.sidebar.header("Calcular Otimização")
    calcular = st.sidebar.button("Calcular Otimização")
    
    # Configurações do Produto (agora em segundo lugar)
    st.sidebar.header("Configurações do Produto")
    st.session_state.comprimento = st.sidebar.number_input("Comprimento do produto (m)", value=None, step=0.05, format="%.2f", min_value=0.01)
    st.session_state.profundidade = st.sidebar.number_input("Profundidade do produto (m)", value=None, step=0.05, format="%.2f", min_value=0.01)
    st.session_state.altura = st.sidebar.number_input("Altura do produto (m)", value=None, step=0.4, format="%.2f", min_value=0.01)
    st.session_state.travar_altura = st.sidebar.checkbox("Travar altura do produto", value=True)
    
    # Configurações do Contêiner (agora em terceiro lugar)
    st.sidebar.header("Configurações do Contêiner")
    st.session_state.container_x = st.sidebar.number_input("Comprimento do contêiner (m)", value=2.2, step=0.1, format="%.2f")
    st.session_state.container_y = st.sidebar.number_input("Profundidade do contêiner (m)", value=1.25, step=0.1, format="%.2f")
    st.session_state.container_z = st.sidebar.number_input("Altura do contêiner (m)", value=2.25, step=0.1, format="%.2f")
    st.session_state.y_tolerance = st.sidebar.number_input("Tolerância na profundidade (m)", value=0.10, step=0.01, format="%.2f")
    
    # Configurações de Visualização
    st.sidebar.header("Configurações de Visualização")
    cor_produto = st.sidebar.color_picker("Cor da box produto", "#87CEEB")  # skyblue
    transparencia = st.sidebar.slider("Transparência do produto", 0.0, 1.0, 0.7, 0.1)
    
    # Se o botão de calcular foi pressionado, realizar otimização
    if calcular:
        calculate_optimization()
    
    # Se a otimização foi realizada, mostrar resultados
    if st.session_state.calculation_done:
        # Recuperar dados do session_state
        optimizer = st.session_state.optimizer
        results = st.session_state.results
        eficiencia = st.session_state.eficiencia
        
        comprimento = st.session_state.comprimento
        profundidade = st.session_state.profundidade  
        altura = st.session_state.altura
        
        # Exibir resultados na área principal
        st.header("Resultados da Otimização")
        
        # Mostrar informações gerais antes das abas
        display_optimization_results(
            st, 
            comprimento, 
            profundidade, 
            altura, 
            results, 
            eficiencia
        )
        
        # Criar abas para os diferentes tipos de visualização
        tab_estatica, tab_interativa = st.tabs(["Visualização Estática", "Visualização 3D Interativa"])
        
        # Na aba de visualização estática
        with tab_estatica:
            fig, ax = visualize_static(
                optimizer,
                fig_size=(10, 8),
                style='ggplot',
                product_color=cor_produto,
                product_alpha=transparencia
            )
            st.pyplot(fig)
        
        # Na aba de visualização interativa
        with tab_interativa:
            fig_plotly = visualize_interactive(
                optimizer=optimizer, 
                cor_produto=cor_produto, 
                transparency=transparencia
            )
            st.plotly_chart(fig_plotly, use_container_width=True)
    else:
        st.info("Basta preencher as informações do produto e clicar em 'Calcular Otimização' para visualizar os resultados.")


if __name__ == "__main__":
    calculate_streamlit()