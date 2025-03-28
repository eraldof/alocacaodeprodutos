"""
Módulo para visualização 3D de contêineres e produtos empacotados.
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import plotly.graph_objects as go


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


def visualize_static(optimizer, fig_size=(12, 8), style='default', 
                     product_color='skyblue', product_alpha=0.7):
    """
    Cria uma visualização 3D estática da disposição dos produtos no contêiner.

    Args:
        optimizer: Objeto PackingOptimizer com resultados de otimização
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
    draw_cuboid(
        ax,
        origin=(0, 0, 0),
        size=(optimizer.container.dimensions.x, optimizer.container.dimensions.y, optimizer.container.dimensions.z),
        color='lightgray',
        alpha=0.1,
        edgecolor='k'
    )

    # Desenha os produtos se houver uma solução válida
    if optimizer.best_count > 0:
        count_x, count_y, count_z = optimizer.best_distribution
        orientation = optimizer.best_orientation

        for i in range(count_x):
            for j in range(count_y):
                for k in range(count_z):
                    origin = (i * orientation[0], j * orientation[1], k * orientation[2])
                    draw_cuboid(
                        ax,
                        origin=origin,
                        size=orientation,
                        color=product_color,
                        alpha=product_alpha,
                        edgecolor='k'
                    )

    # Adicionar margem extra para evitar cortes
    x_margin = optimizer.container.dimensions.x * 0.1
    y_margin = optimizer.container.dimensions.y * 0.1
    z_margin = optimizer.container.dimensions.z * 0.1
    
    # Configurações do gráfico com margens extras
    ax.set_xlim(-x_margin, optimizer.container.dimensions.x + x_margin)
    ax.set_ylim(-y_margin, optimizer.container.dimensions.y + y_margin)
    ax.set_zlim(-z_margin, optimizer.container.dimensions.z + z_margin)
    
    ax.set_xlabel('Comprimento (m)')
    ax.set_ylabel('Profundidade (m)')
    ax.set_zlabel('Altura (m)')

    # Configurar melhor ângulo de visão
    ax.view_init(elev=30, azim=45)
    ax.grid(True)

    # Usar tight_layout com padding específico para evitar cortes
    plt.tight_layout(pad=3.0)
    
    return fig, ax


def visualize_interactive(optimizer, cor_produto, transparency):
    """
    Cria uma visualização 3D interativa usando Plotly.

    Args:
        optimizer: Objeto PackingOptimizer com resultados de otimização
        cor_produto: Cor para os produtos
                
    Returns:
        Objeto de figura Plotly
    """
    fig = go.Figure()

    # Definir dimensões do contêiner
    container_x, container_y, container_z = optimizer.container.dimensions.as_tuple()

    # Adicionar o contêiner (transparente)
    fig.add_trace(go.Mesh3d(
        x=[0, container_x, container_x, 0, 0, container_x, container_x, 0],
        y=[0, 0, container_y, container_y, 0, 0, container_y, container_y],
        z=[0, 0, 0, 0, container_z, container_z, container_z, container_z],
        i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        opacity=0.6,
        color='lightgrey',
        name='Contêiner'
    ))

    # Adicionar os produtos se houver solução válida
    if optimizer.best_count > 0:
        count_x, count_y, count_z = optimizer.best_distribution
        o_x, o_y, o_z = optimizer.best_orientation

        for i in range(count_x):
            for j in range(count_y):
                for k in range(count_z):
                    x0 = float(i) * float(o_x)
                    y0 = float(j) * float(o_y)
                    z0 = float(k) * float(o_z)

                    # Criar os vértices individuais do cubo
                    x = [x0, x0+o_x, x0+o_x, x0, x0, x0+o_x, x0+o_x, x0]
                    y = [y0, y0, y0+o_y, y0+o_y, y0, y0, y0+o_y, y0+o_y]
                    z = [z0, z0, z0, z0, z0+o_z, z0+o_z, z0+o_z, z0+o_z]

                    # Índices para formar todas as 6 faces do cubo
                    i_indices = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
                    j_indices = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
                    k_indices = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]

                    # Adicionar cubo sólido
                    fig.add_trace(go.Mesh3d(
                        x=x, y=y, z=z, 
                        i=i_indices, j=j_indices, k=k_indices,
                        opacity = transparency,
                        color = cor_produto,
                        lighting=dict(
                            ambient=0.9,
                            roughness=0.1
                        ),
                        name='Produto'
                    ))

    # Configuração do layout
    fig.update_layout(
        scene=dict(
            aspectmode='data',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
        ),
        margin=dict(l=0, r=0, b=0, t=30)
    )

    return fig
