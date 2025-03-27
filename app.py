"""
Aplicativo Streamlit para otimização de empacotamento 3D em gaiolas ou contêineres.
Calcula a disposição ótima de produtos retangulares em um espaço retangular.
"""

import math
import itertools
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from dataclasses import dataclass
from typing import Tuple, List, Dict
import streamlit as st
import plotly.graph_objects as go


@dataclass
class Dimension3D:
    """Classe para representar dimensões 3D."""
    x: float
    y: float
    z: float

    def as_tuple(self) -> Tuple[float, float, float]:
        """Retorna as dimensões como uma tupla."""
        return (self.x, self.y, self.z)


class Container:
    """Classe para representar um contêiner ou gaiola."""

    def __init__(self, x: float, y: float, z: float, y_tolerance: float = 0):
        """
        Inicializa um contêiner com dimensões específicas.

        Args:
            x: Comprimento do contêiner (metros)
            y: Profundidade do contêiner (metros)
            z: Altura do contêiner (metros)
            y_tolerance: Tolerância adicional na dimensão y (metros)
        """
        self.dimensions = Dimension3D(x, y, z)
        self.y_tolerance = y_tolerance

    @property
    def effective_y(self) -> float:
        """Retorna a profundidade efetiva com tolerância."""
        return self.dimensions.y + self.y_tolerance

    def visualize(self, ax, color='lightgray', alpha=0.1, edgecolor='k'):
        """Adiciona visualização do contêiner ao eixo fornecido."""
        draw_cuboid(
            ax,
            origin=(0, 0, 0),
            size=(self.dimensions.x, self.dimensions.y, self.dimensions.z),
            color=color,
            alpha=alpha,
            edgecolor=edgecolor
        )


class Product:
    """Classe para representar um produto com dimensões 3D."""

    def __init__(self, length: float, width: float, height: float):
        """
        Inicializa um produto com dimensões específicas.

        Args:
            length: Primeira dimensão do produto (metros)
            width: Segunda dimensão do produto (metros)
            height: Terceira dimensão do produto (metros)
        """
        self.dimensions = (length, width, height)

    def get_orientations(self, lock_vertical: bool = False) -> List[Tuple[float, float, float]]:
        """
        Retorna todas as orientações possíveis para o produto.

        Args:
            lock_vertical: Se True, mantém a última dimensão fixa (vertical)

        Returns:
            Lista de orientações possíveis como tuplas (x, y, z)
        """
        if lock_vertical:
            # Apenas permuta as duas primeiras dimensões, mantendo a terceira fixa
            return [
                (self.dimensions[0], self.dimensions[1], self.dimensions[2]),
                (self.dimensions[1], self.dimensions[0], self.dimensions[2])
            ]
        else:
            # Retorna todas as permutações possíveis
            return list(itertools.permutations(self.dimensions))

    def visualize(self, ax, origin, orientation, color='skyblue', alpha=0.7, edgecolor='k'):
        """
        Adiciona visualização do produto ao eixo fornecido.

        Args:
            ax: Eixo matplotlib para desenho
            origin: Ponto de origem (x, y, z) para o produto
            orientation: Dimensões do produto na orientação escolhida
            color: Cor para o produto
            alpha: Transparência do produto
            edgecolor: Cor da borda
        """
        draw_cuboid(
            ax,
            origin=origin,
            size=orientation,
            color=color,
            alpha=alpha,
            edgecolor=edgecolor
        )


class PackingOptimizer:
    """Classe para otimizar o empacotamento de produtos em um contêiner."""

    def __init__(self, container: Container, product: Product, lock_vertical: bool = False):
        """
        Inicializa o otimizador com um contêiner e um produto.

        Args:
            container: O contêiner ou gaiola a ser preenchido
            product: O produto a ser colocado no contêiner
            lock_vertical: Se True, mantém a última dimensão do produto fixa
        """
        self.container = container
        self.product = product
        self.lock_vertical = lock_vertical
        self.best_orientation = None
        self.best_count = 0
        self.best_distribution = (0, 0, 0)

    def calculate_quantity(self, orientation: Tuple[float, float, float]) -> Tuple[int, Tuple[int, int, int]]:
        """
        Calcula a quantidade de produtos que cabem no contêiner com uma orientação específica.

        Args:
            orientation: Tupla com dimensões do produto na orientação a ser testada

        Returns:
            Tupla com (total de produtos, distribuição por eixo (x, y, z))
        """
        # Verifica se o produto cabe nas dimensões do contêiner
        if (orientation[0] > self.container.dimensions.x or
            orientation[1] > self.container.effective_y or
            orientation[2] > self.container.dimensions.z):
            return 0, (0, 0, 0)

        count_x = math.floor(self.container.dimensions.x / orientation[0])
        count_y = math.floor(self.container.effective_y / orientation[1])
        count_z = math.floor(self.container.dimensions.z / orientation[2])

        total = count_x * count_y * count_z
        return total, (count_x, count_y, count_z)

    def optimize(self) -> Dict:
        """
        Encontra a melhor orientação para maximizar a quantidade de produtos no contêiner.

        Returns:
            Dicionário com resultados da otimização
        """
        orientations = self.product.get_orientations(self.lock_vertical)
        results = []

        log_text = "Testando orientações:\n"
        for orientation in orientations:
            total, distribution = self.calculate_quantity(orientation)
            orientation_log = f"Orientação {orientation}: {distribution} produtos por eixo, total = {total}"
            log_text += orientation_log + "\n"
            
            results.append({
                "orientation": orientation,
                "total": total,
                "distribution": distribution
            })

            if total > self.best_count:
                self.best_count = total
                self.best_orientation = orientation
                self.best_distribution = distribution

        if self.best_count == 0:
            log_text += "\nNenhuma orientação do produto cabe no contêiner."
        else:
            log_text += "\nMelhor orientação encontrada:\n"
            log_text += f"Produto orientado como: {self.best_orientation}\n"
            log_text += f"Quantidade por eixo (x, y, z): {self.best_distribution}\n"
            log_text += f"Total de produtos que cabem: {self.best_count}"

        return {
            "best_orientation": self.best_orientation,
            "best_count": self.best_count,
            "best_distribution": self.best_distribution,
            "all_results": results,
            "log_text": log_text
        }

    def visualize(self, fig_size=(12, 8), style='default', product_color='skyblue', product_alpha=0.7):
        """
        Cria uma visualização 3D da disposição dos produtos no contêiner.

        Args:
            fig_size: Tamanho da figura (largura, altura)
            style: Estilo matplotlib a ser usado
            product_color: Cor fixa para todos os produtos
            product_alpha: Transparência (alpha) para todos os produtos

        Returns:
            Objeto figura e eixo matplotlib
        """

        fig = plt.figure(figsize=fig_size)
        ax = fig.add_subplot(111, projection='3d')
        
        # Definir fundo branco explicitamente
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        # Desenha o contêiner
        self.container.visualize(ax)

        # Desenha os produtos se houver uma solução válida
        if self.best_count > 0:
            count_x, count_y, count_z = self.best_distribution
            orientation = self.best_orientation

            for i in range(count_x):
                for j in range(count_y):
                    for k in range(count_z):
                        origin = (i * orientation[0], j * orientation[1], k * orientation[2])
                        self.product.visualize(
                            ax,
                            origin=origin,
                            orientation=orientation,
                            color=product_color,
                            alpha=product_alpha
                        )

        # Adicionar margem extra para evitar cortes
        x_margin = self.container.dimensions.x * 0.1
        y_margin = self.container.dimensions.y * 0.1
        z_margin = self.container.dimensions.z * 0.1
        
        # Configurações do gráfico com margens extras
        ax.set_xlim(-x_margin, self.container.dimensions.x + x_margin)
        ax.set_ylim(-y_margin, self.container.dimensions.y + y_margin)
        ax.set_zlim(-z_margin, self.container.dimensions.z + z_margin)
        
        ax.set_xlabel('Comprimento (m)')
        ax.set_ylabel('Profundidade (m)')
        ax.set_zlabel('Altura (m)')

        # Configurar melhor ângulo de visão
        ax.view_init(elev=30, azim=45)
        ax.grid(True)

        # Usar tight_layout com padding específico para evitar cortes
        plt.tight_layout(pad=3.0)
        
        return fig, ax
    
    def visualize_plotly(self, cor_produto):
        """
        Cria uma visualização 3D interativa usando Plotly.
        
        Args:
            nome_produto: Nome do produto para exibição
                
        Returns:
            Objeto de figura Plotly
        """
        fig = go.Figure()
        
        # Definir dimensões do contêiner
        container_x, container_y, container_z = self.container.dimensions.as_tuple()
        
        # Adicionar o contêiner (usando uma caixa transparente)
        fig.add_trace(go.Mesh3d(
            x=[0, container_x, container_x, 0, 0, container_x, container_x, 0],
            y=[0, 0, container_y, container_y, 0, 0, container_y, container_y],
            z=[0, 0, 0, 0, container_z, container_z, container_z, container_z],
            # Indices corretos para definir todas as faces do cubo
            i=[0, 0, 3, 4, 4, 4, 0, 0, 1, 5, 5, 7],
            j=[1, 2, 2, 5, 6, 7, 4, 5, 5, 6, 7, 3],
            k=[2, 3, 0, 6, 7, 3, 5, 1, 2, 2, 6, 2],
            opacity=0.2,
            color='lightgray',
            name='Contêiner'
        ))
        
        # Adicionar os produtos se houver uma solução válida
        if self.best_count > 0:
            # Uso direto das tuplas (count_x, count_y, count_z) e (o_x, o_y, o_z)
            count_x, count_y, count_z = self.best_distribution
            o_x, o_y, o_z = self.best_orientation

            for i in range(count_x):
                for j in range(count_y):
                    for k in range(count_z):
                        # Calcular a posição do produto
                        x0 = float(i) * float(o_x)
                        y0 = float(j) * float(o_y)
                        z0 = float(k) * float(o_z)
                        
                        # Criar os vértices do cubóide
                        x = [x0, x0+o_x, x0+o_x, x0, x0, x0+o_x, x0+o_x, x0]
                        y = [y0, y0, y0+o_y, y0+o_y, y0, y0, y0+o_y, y0+o_y]
                        z = [z0, z0, z0, z0, z0+o_z, z0+o_z, z0+o_z, z0+o_z]
                        
                        # Definição correta dos índices para todas as faces do cubo
                        i_indices = [0, 0, 0, 1, 1, 3, 4, 4, 4, 5, 5, 7]
                        j_indices = [1, 2, 3, 2, 5, 2, 5, 6, 7, 6, 7, 3]
                        k_indices = [2, 3, 0, 5, 6, 6, 6, 7, 3, 7, 3, 2]
                        
                        # Adicionar o produto
                        fig.add_trace(go.Mesh3d(
                            x=x, y=y, z=z, 
                            i=i_indices, j=j_indices, k=k_indices,
                            opacity=1,
                            color=cor_produto,
                            flatshading=False,
                            lighting=dict(
                                ambient=0.6,
                                diffuse=0.8,
                                specular=0.3,
                                roughness=0.4,
                                fresnel=0.2
                            ),
                            lightposition=dict(
                                x=100,
                                y=100,
                                z=100
                            ),
                            name=f'Produto'
                        ))
        
        # Configurar o layout da figura
        fig.update_layout(
            scene=dict(
                aspectmode='data',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            margin=dict(l=0, r=0, b=0, t=30)
        )
        
        return fig


def draw_cuboid(ax, origin, size, color='cyan', alpha=0.5, edgecolor='k'):
    """
    Desenha um paralelepípedo (cubóide) em um eixo 3D.

    Args:
        ax: Eixo matplotlib para desenho
        origin: (x, y, z) - coordenada da esquina inferior esquerda
        size: (dx, dy, dz) - dimensões do cubóide
        color: Cor do cubóide
        alpha: Transparência
        edgecolor: Cor da borda
    """
    ox, oy, oz = origin
    dx, dy, dz = size

    # Define os vértices do cubóide
    vertices = [
        [ox, oy, oz],
        [ox+dx, oy, oz],
        [ox+dx, oy+dy, oz],
        [ox, oy+dy, oz],
        [ox, oy, oz+dz],
        [ox+dx, oy, oz+dz],
        [ox+dx, oy+dy, oz+dz],
        [ox, oy+dy, oz+dz],
    ]

    # Define as faces usando os vértices
    faces = [
        [vertices[i] for i in [0,1,2,3]],  # base inferior
        [vertices[i] for i in [4,5,6,7]],  # base superior
        [vertices[i] for i in [0,1,5,4]],  # lateral 1
        [vertices[i] for i in [1,2,6,5]],  # lateral 2
        [vertices[i] for i in [2,3,7,6]],  # lateral 3
        [vertices[i] for i in [3,0,4,7]],  # lateral 4
    ]

    # Cria e adiciona a coleção de polígonos
    pc = Poly3DCollection(faces, facecolors=color, edgecolors=edgecolor, alpha=alpha)
    ax.add_collection3d(pc)


def calculate_streamlit():
    """Função principal para executar a otimização de empacotamento no Streamlit."""
    
    st.title("Otimizador de Empacotamento 3D")
    
    st.sidebar.header("Configurações do Contêiner")
    container_x = st.sidebar.number_input("Comprimento do contêiner (m)", value=2.2, step=0.1, format="%.2f")
    container_y = st.sidebar.number_input("Profundidade do contêiner (m)", value=1.3, step=0.1, format="%.2f")
    container_z = st.sidebar.number_input("Altura do contêiner (m)", value=2.4, step=0.1, format="%.2f")
    y_tolerance = st.sidebar.number_input("Tolerância na profundidade (m)", value=0.13, step=0.01, format="%.2f")
    
    st.sidebar.header("Configurações do Produto")
    #nome_produto = st.sidebar.text_input("Nome do produto", "Produto")
    comprimento = st.sidebar.number_input("Comprimento do produto (m)", value=1.38, step=0.05, format="%.2f", min_value=0.01)
    profundidade = st.sidebar.number_input("Profundidade do produto (m)", value=1.88, step=0.05, format="%.2f", min_value=0.01)
    altura = st.sidebar.number_input("Altura do produto (m)", value=0.2, step=0.4, format="%.2f", min_value=0.01)
    
    st.sidebar.header("Configurações de Visualização")
    cor_produto = st.sidebar.color_picker("Cor da box produto", "#87CEEB")  # skyblue
    transparencia = st.sidebar.slider("Transparência do produto", 0.0, 1.0, 0.7, 0.1)
    travar_altura = st.sidebar.checkbox("Travar altura do produto", value=True)
    
    visualizacao_tab = st.sidebar.radio("Tipo de visualização", ["Ambas", "Estática", "Interativa 3D"])
    
    # Botão para calcular
    if st.sidebar.button("Calcular Otimização"):
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
        
        # Exibir resultados na área principal
        if visualizacao_tab == "Ambas":
            # Mostrar informações no topo
            st.header("Resultados da Otimização")
            #st.markdown(f"**Produto:** {nome_produto}")
            st.markdown(f"**Dimensões:** {comprimento}m × {profundidade}m × {altura}m")
            
            if results["best_count"] > 0:
                st.markdown(f"**Melhor orientação:** {results['best_orientation']}m")
                st.markdown(f"**Distribuição (x,y,z):** {results['best_distribution']}")
                st.markdown(f"**Total de produtos:** {results['best_count']}")
                
                # Calcular eficiência de preenchimento
                volume_container = container_x * container_y * container_z
                volume_produto = comprimento * profundidade * altura
                volume_ocupado = results["best_count"] * volume_produto
                eficiencia = (volume_ocupado / volume_container) * 100
                
                st.markdown(f"**Eficiência de preenchimento:** {eficiencia:.2f}%")
            else:
                st.error("Nenhuma configuração possível para este produto no contêiner.")
            
            # Mostrar as duas visualizações
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Visualização Estática")
                fig, ax = optimizer.visualize(
                    #nome_produto=nome_produto,
                    fig_size=(10, 8),
                    style='ggplot',
                    product_color=cor_produto,
                    product_alpha=transparencia
                )
                st.pyplot(fig)
                
            with col2:
                st.subheader("Visualização 3D Interativa")
                fig_plotly = optimizer.visualize_plotly(cor_produto)
                st.plotly_chart(fig_plotly, use_container_width=True)
                
            # Exibir log detalhado
            with st.expander("Ver detalhes de cálculo"):
                st.text(results["log_text"])
                
        elif visualizacao_tab == "Estática":
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.header("Visualização Estática")
                fig, ax = optimizer.visualize(
                    #nome_produto=nome_produto,
                    fig_size=(10, 8),
                    style='ggplot',
                    product_color=cor_produto,
                    product_alpha=transparencia
                )
                st.pyplot(fig)
                
            with col2:
                st.header("Resultados da Otimização")
                #st.markdown(f"**Produto:** {nome_produto}")
                st.markdown(f"**Dimensões:** {comprimento}m × {profundidade}m × {altura}m")
                
                if results["best_count"] > 0:
                    st.markdown(f"**Melhor orientação:** {results['best_orientation']}m")
                    st.markdown(f"**Distribuição (x,y,z):** {results['best_distribution']}")
                    st.markdown(f"**Total de produtos:** {results['best_count']}")
                    
                    # Calcular eficiência de preenchimento
                    volume_container = container_x * container_y * container_z
                    volume_produto = comprimento * profundidade * altura
                    volume_ocupado = results["best_count"] * volume_produto
                    eficiencia = (volume_ocupado / volume_container) * 100
                    
                    st.markdown(f"**Eficiência de preenchimento:** {eficiencia:.2f}%")
                else:
                    st.error("Nenhuma configuração possível para este produto no contêiner.")
                
                # Exibir log detalhado
                with st.expander("Ver detalhes de cálculo"):
                    st.text(results["log_text"])
                    
        else:  # Interativa 3D
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.header("Visualização 3D Interativa")
                fig_plotly = optimizer.visualize_plotly(cor_produto)
                st.plotly_chart(fig_plotly, use_container_width=True)
                
            with col2:
                st.header("Resultados da Otimização")
                #st.markdown(f"**Produto:** {nome_produto}")
                st.markdown(f"**Dimensões:** {comprimento}m × {profundidade}m × {altura}m")
                
                if results["best_count"] > 0:
                    st.markdown(f"**Melhor orientação:** {results['best_orientation']}m")
                    st.markdown(f"**Distribuição (x,y,z):** {results['best_distribution']}")
                    st.markdown(f"**Total de produtos:** {results['best_count']}")
                    
                    # Calcular eficiência de preenchimento
                    volume_container = container_x * container_y * container_z
                    volume_produto = comprimento * profundidade * altura
                    volume_ocupado = results["best_count"] * volume_produto
                    eficiencia = (volume_ocupado / volume_container) * 100
                    
                    st.markdown(f"**Eficiência de preenchimento:** {eficiencia:.2f}%")
                else:
                    st.error("Nenhuma configuração possível para este produto no contêiner.")
                
                # Exibir log detalhado
                with st.expander("Ver detalhes de cálculo"):
                    st.text(results["log_text"])


if __name__ == "__main__":
    calculate_streamlit()