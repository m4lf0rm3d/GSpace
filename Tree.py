import os


class TreeNode:
    def __init__(self, value, drive_id=None, isDir=None, fileSize=0):
        self.value    = value
        self.children = {}
        self.id       = drive_id
        self.isDir    = isDir
        self.fileSize = fileSize


class Tree:
    def __init__(self):
        self.root = None

    def add(self, path, drive_id=None, isDir=None, fileSize=0):
        if not self.root:
            self.root = TreeNode(path[0], drive_id, isDir, fileSize)
        else:
            self._add_recursive(self.root, path[1:], drive_id, isDir, fileSize)

    def _add_recursive(self, node, path, drive_id, isDir=None, fileSize=0):
        if not path:
            return
        current_value = path[0]
        if current_value not in node.children:
            node.children[current_value] = TreeNode(current_value, drive_id, isDir, fileSize)
        self._add_recursive(node.children[current_value], path[1:], drive_id, isDir, fileSize)

    def remove(self, path):
        if self.root:
            self._remove_recursive(self.root, path)

    def _remove_recursive(self, node, path):
        if not path:
            return
        current_value = path[0]
        if current_value in node.children:
            if len(path) == 1:
                del node.children[current_value]
            else:
                self._remove_recursive(node.children[current_value], path[1:])

    def find_difference_path(self, tree2):
        """
        Compare two trees and return additions, deletions, and modifications.

        BUG FIX: The original code used os.path.isdir(key) which checks if a
        filename string is a directory on the *current machine's filesystem* —
        it always returned False for drive-side nodes.  We now use the isDir
        flag stored on the node itself, which is correct for both sides.
        """
        changes = {"Additions": [], "Deletions": [], "Modifications": []}

        def _compare(node1, node2, current_path):
            keys1 = set(node1.children)
            keys2 = set(node2.children)

            for name in keys1.symmetric_difference(keys2):
                change_node = node1.children[name] if name in keys1 else node2.children[name]
                final_path  = f"/{'/'.join(current_path + [name])}"
                if name in keys1:
                    changes["Additions"].append((final_path, change_node.id, change_node.isDir))
                else:
                    changes["Deletions"].append((final_path, change_node.id, change_node.isDir))

            for name in keys1 & keys2:
                n1 = node1.children[name]
                n2 = node2.children[name]

                file_id    = n1.id or n2.id
                final_path = f"/{'/'.join(current_path + [name])}"

                # Use the stored isDir flag instead of os.path.isdir(name)
                is_directory = n1.isDir or n2.isDir or False

                if not is_directory and int(n1.fileSize) != int(n2.fileSize):
                    changes["Modifications"].append((final_path, file_id, False))

                _compare(n1, n2, current_path + [name])

        if self.root and tree2.root:
            _compare(self.root, tree2.root, [])

        return changes

    def traverse_and_print(self):
        if self.root:
            self._traverse_and_print_recursive(self.root)

    def _traverse_and_print_recursive(self, node, depth=0):
        print("\\__ " * depth + str(node.value) + f" ({node.id})")
        for _, child in node.children.items():
            self._traverse_and_print_recursive(child, depth + 1)

    def get_node(self, path):
        if self.root:
            return self._get_node(self.root, path, 0)
        return None, 0

    def _get_node(self, node, path, nodes_traversed):
        if not path:
            return node, nodes_traversed
        current_value = path[0]
        if current_value in node.children:
            return self._get_node(node.children[current_value], path[1:], nodes_traversed + 1)
        return node, nodes_traversed

    def find_parent_node_by_id(self, file_id):
        if self.root:
            return self._find_parent_node_by_id(self.root, file_id)
        return None

    def _find_parent_node_by_id(self, node, file_id):
        for child in node.children.values():
            if child.id == file_id:
                return node
            result = self._find_parent_node_by_id(child, file_id)
            if result:
                return result
        return None