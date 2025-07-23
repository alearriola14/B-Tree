import time
import random
from collections import defaultdict


class Node:
    def __init__(self, leaf=False):
        self.leaf = leaf
        self.keys = []
        self.children = []


class BTreeWithMetrics:
    def __init__(self, t):
        self.root = Node(True)
        self.t = t
        # Métricas de rendimiento
        self.disk_accesses = 0
        self.operation_times = defaultdict(list)
        self.node_count = 1  # Empezamos con root
        
    def reset_metrics(self):
        """Reinicia las métricas para una nueva prueba"""
        self.disk_accesses = 0
        self.operation_times.clear()
    
    def _access_node(self):
        """Simula acceso a disco incrementando contador"""
        self.disk_accesses += 1

    def search(self, k, x=None):
        start_time = time.perf_counter()
        
        if x is not None:
            self._access_node()  # Acceso al nodo
            i = 0
            while i < len(x.keys) and x.keys[i] and k > x.keys[i][0]:
                i += 1
            if i < len(x.keys) and x.keys[i] and k == x.keys[i][0]:
                end_time = time.perf_counter()
                self.operation_times['search'].append(end_time - start_time)
                return x, i
            elif x.leaf:
                end_time = time.perf_counter()
                self.operation_times['search'].append(end_time - start_time)
                return None
            else:
                if i < len(x.children):
                    return self.search(k, x.children[i])
        else:
            return self.search(k, self.root)

    def insert(self, k):

        start_time = time.perf_counter()
        root = self.root
        self._access_node()  # Acceso al root
        
        if len(root.keys) == (2 * self.t) - 1:
            temp = Node()
            self.node_count += 1  # Nuevo nodo creado
            self.root = temp
            temp.children.insert(0, root)
            self._splitChild(temp, 0)
            self._insertNonFull(temp, k)
        else:
            self._insertNonFull(root, k)
            
        end_time = time.perf_counter()
        self.operation_times['insert'].append(end_time - start_time)

    def _insertNonFull(self, x, k):
        """Insert in non-full node with disk access tracking"""
        self._access_node()
        i = len(x.keys) - 1
        if x.leaf:
            x.keys.append((None, None))
            while i >= 0 and k[0] < x.keys[i][0]:
                x.keys[i + 1] = x.keys[i]
                i -= 1
            x.keys[i + 1] = k
        else:
            while i >= 0 and k[0] < x.keys[i][0]:
                i -= 1
            i += 1
            if len(x.children[i].keys) == (2 * self.t) - 1:
                self._splitChild(x, i)
                if k[0] > x.keys[i][0]:
                    i += 1
            self._insertNonFull(x.children[i], k)

    def _splitChild(self, x, i):
        """Split child with node counting"""
        t = self.t
        y = x.children[i]
        z = Node(y.leaf)
        self.node_count += 1  # Nuevo nodo creado
        x.children.insert(i + 1, z)
        x.keys.insert(i, y.keys[t - 1])
        z.keys = y.keys[t : (2 * t) - 1]
        y.keys = y.keys[0 : t - 1]
        if not y.leaf:
            z.children = y.children[t : 2 * t]
            y.children = y.children[0:t]

    def delete(self, x, k):

        start_time = time.perf_counter()
        self._delete_helper(x, k)
        end_time = time.perf_counter()
        self.operation_times['delete'].append(end_time - start_time)

    def _delete_helper(self, x, k):
        """Helper method for deletion with disk access tracking"""
        self._access_node()
        t = self.t
        i = 0
        while i < len(x.keys) and x.keys[i] and k[0] > x.keys[i][0]:
            i += 1
            
        if x.leaf:
            if i < len(x.keys) and x.keys[i] and x.keys[i][0] == k[0]:
                x.keys.pop(i)
                return
            return

        if i < len(x.keys) and x.keys[i] and x.keys[i][0] == k[0]:
            return self._deleteInternalNode(x, k, i)
        elif i < len(x.keys) and len(x.children[i].keys) >= t:
            self._delete_helper(x.children[i], k)
        else:
            if i != 0 and i + 2 < len(x.children):
                if len(x.children[i - 1].keys) >= t:
                    self._deleteSibling(x, i, i - 1)
                elif len(x.children[i + 1].keys) >= t:
                    self._deleteSibling(x, i, i + 1)
                else:
                    self._deleteMerge(x, i, i + 1)
            elif i == 0 and i + 1 < len(x.children):
                if len(x.children[i + 1].keys) >= t:
                    self._deleteSibling(x, i, i + 1)
                else:
                    self._deleteMerge(x, i, i + 1)
            elif i + 1 == len(x.children) and i != 0:
                if len(x.children[i - 1].keys) >= t:
                    self._deleteSibling(x, i, i - 1)
                else:
                    self._deleteMerge(x, i, i - 1)
            if i < len(x.children):
                self._delete_helper(x.children[i], k)

    def _deleteInternalNode(self, x, k, i):
        """Delete internal node with access tracking"""
        self._access_node()
        t = self.t
        if x.leaf:
            if x.keys[i][0] == k[0]:
                x.keys.pop(i)
                return
            return

        if len(x.children[i].keys) >= t:
            x.keys[i] = self._deletePredecessor(x.children[i])
            return
        elif len(x.children[i + 1].keys) >= t:
            x.keys[i] = self._deleteSuccessor(x.children[i + 1])
            return
        else:
            self._deleteMerge(x, i, i + 1)
            self._deleteInternalNode(x.children[i], k, self.t - 1)

    def _deletePredecessor(self, x):
        """Delete predecessor with access tracking"""
        self._access_node()
        if x.leaf:
            return x.keys.pop()
        n = len(x.keys) - 1
        if len(x.children[n].keys) >= self.t:
            self._deleteSibling(x, n + 1, n)
        else:
            self._deleteMerge(x, n, n + 1)
        self._deletePredecessor(x.children[n])

    def _deleteSuccessor(self, x):
        """Delete successor with access tracking"""
        self._access_node()
        if x.leaf:
            return x.keys.pop(0)
        if len(x.children[1].keys) >= self.t:
            self._deleteSibling(x, 0, 1)
        else:
            self._deleteMerge(x, 0, 1)
        self._deleteSuccessor(x.children[0])

    def _deleteMerge(self, x, i, j):
        """Merge nodes with node counting"""
        cNode = x.children[i]
        
        if j > i:
            rsNode = x.children[j]
            cNode.keys.append(x.keys[i])
            for k in range(len(rsNode.keys)):
                cNode.keys.append(rsNode.keys[k])
                if len(rsNode.children) > 0:
                    cNode.children.append(rsNode.children[k])
            if len(rsNode.children) > 0:
                cNode.children.append(rsNode.children.pop())
            new = cNode
            x.keys.pop(i)
            x.children.pop(j)
            self.node_count -= 1  # Nodo eliminado
        else:
            lsNode = x.children[j]
            lsNode.keys.append(x.keys[j])
            for k in range(len(cNode.keys)):
                lsNode.keys.append(cNode.keys[k])
                if len(lsNode.children) > 0:
                    lsNode.children.append(cNode.children[k])
            if len(lsNode.children) > 0:
                lsNode.children.append(cNode.children.pop())
            new = lsNode
            x.keys.pop(j)
            if i < len(x.children):
                x.children.pop(i)
            self.node_count -= 1  # Nodo eliminado

        if x == self.root and len(x.keys) == 0:
            self.root = new

    @staticmethod
    def _deleteSibling(x, i, j):
        """Borrow from sibling (sin cambios, pero podrías agregar _access_node)"""
        cNode = x.children[i]
        if i < j:
            rsNode = x.children[j]
            cNode.keys.append(x.keys[i])
            x.keys[i] = rsNode.keys[0]
            if len(rsNode.children) > 0:
                cNode.children.append(rsNode.children[0])
                rsNode.children.pop(0)
            rsNode.keys.pop(0)
        else:
            lsNode = x.children[j]
            cNode.keys.insert(0, x.keys[i - 1])
            x.keys[i - 1] = lsNode.keys.pop()
            if len(lsNode.children) > 0:
                cNode.children.insert(0, lsNode.children.pop())

    def get_statistics(self):
        """Retorna estadísticas de rendimiento"""
        stats = {
            'disk_accesses': self.disk_accesses,
            'node_count': self.node_count,
            'avg_search_time': sum(self.operation_times['search']) / len(self.operation_times['search']) if self.operation_times['search'] else 0,
            'avg_insert_time': sum(self.operation_times['insert']) / len(self.operation_times['insert']) if self.operation_times['insert'] else 0,
            'avg_delete_time': sum(self.operation_times['delete']) / len(self.operation_times['delete']) if self.operation_times['delete'] else 0
        }
        return stats


def run_performance_test():
    """Función para probar el rendimiento"""
    print("=== Prueba de Rendimiento B-Tree ===")
    # Probar diferentes grados mínimos
    for t in [2, 3, 5]:
        print(f"\nPrueba con grado mínimo t={t}")
        btree = BTreeWithMetrics(t)
        # Insertar datos
        print("Insertando 1000 elementos...")
        for i in range(1000):
            btree.insert((i, random.randint(1, 10000)))
        # Buscar elementos
        print("Realizando 100 búsquedas...")
        for _ in range(100):
            key = random.randint(0, 999)
            btree.search(key)
        # Eliminar algunos elementos
        print("Eliminando 50 elementos...")
        for _ in range(50):
            key = random.randint(0, 999)
            btree.delete(btree.root, (key,))
        # Mostrar estadísticas
        stats = btree.get_statistics()
        print(f"Accesos a disco: {stats['disk_accesses']}")
        print(f"Número de nodos: {stats['node_count']}")
        print(f"Tiempo promedio búsqueda: {stats['avg_search_time']:.6f}s")
        print(f"Tiempo promedio inserción: {stats['avg_insert_time']:.6f}s")
        print(f"Tiempo promedio eliminación: {stats['avg_delete_time']:.6f}s")


if __name__ == "__main__":
    run_performance_test()
