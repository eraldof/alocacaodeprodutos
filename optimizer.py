"""
Módulo com classes para otimização de empacotamento 3D em gaiolas ou contêineres.
"""

import math
import itertools
from dataclasses import dataclass
from typing import Tuple, List, Dict


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
            Dicionário com resultados da otimização, incluindo quanto os produtos
            ultrapassam a dimensão original do contêiner em centímetros
        """
        orientations = self.product.get_orientations(self.lock_vertical)
        results = []

        log_text = "Testando orientações:\n"
        for orientation in orientations:
            total, distribution = self.calculate_quantity(orientation)
            orientation_log = f"Orientação {orientation}: {distribution} produtos por eixo, total = {total}"
            log_text += orientation_log + "\n"
            
            # Calcular o quanto ultrapassa na dimensão y
            y_overhang = max(0, distribution[1] * orientation[1] - self.container.dimensions.y)
            y_overhang_cm = round(y_overhang * 100, 1)  # Converter para centímetros
            
            results.append({
                "orientation": orientation,
                "total": total,
                "distribution": distribution,
                "y_overhang_cm": y_overhang_cm
            })

            if total > self.best_count:
                self.best_count = total
                self.best_orientation = orientation
                self.best_distribution = distribution
                self.best_overhang_cm = y_overhang_cm

        if self.best_count == 0:
            log_text += "\nNenhuma orientação do produto cabe no contêiner."
            self.best_overhang_cm = 0
        else:
            log_text += "\nMelhor orientação encontrada:\n"
            log_text += f"Produto orientado como: {self.best_orientation}\n"
            log_text += f"Quantidade por eixo (x, y, z): {self.best_distribution}\n"
            log_text += f"Total de produtos que cabem: {self.best_count}\n"
            log_text += f"Projeção além da gaiola: {self.best_overhang_cm} cm"

        return {
            "best_orientation": self.best_orientation,
            "best_count": self.best_count,
            "best_distribution": self.best_distribution,
            "overflow_y": self.best_overhang_cm,
            "all_results": results,
            "log_text": log_text
        }
