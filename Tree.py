class TreeNode:
    def __init__(self, value, drive_id=None, isDir=None):
        """
        Initialize a TreeNode.

        Parameters:
        - value: The value of the node.
        - drive_id: Identifier for the drive associated with the node.
        - isDir: Boolean indicating whether the node represents a directory.
        """
        self.value = value
        self.children = {}
        self.id = drive_id
        self.isDir = isDir


class Tree:
    def __init__(self):
        """
        Initialize a Tree.
        """
        self.root = None

    def add(self, path, drive_id=None, isDir=None):
        """
        Add a node to the tree based on the given path.

        Parameters:
        - path: List representing the path to the node.
        - drive_id: Identifier for the drive associated with the node.
        - isDir: Boolean indicating whether the node represents a directory.
        """
        if not self.root:
            self.root = TreeNode(path[0], drive_id, isDir)
        else:
            self._add_recursive(self.root, path[1:], drive_id, isDir)

    def _add_recursive(self, node, path, drive_id, isDir=None):
        """
        Recursively add a node to the tree.

        Parameters:
        - node: The current node being processed.
        - path: Remaining path to traverse.
        - drive_id: Identifier for the drive associated with the node.
        - isDir: Boolean indicating whether the node represents a directory.
        """
        if len(path) == 0:
            return

        current_value = path[0]

        if current_value in node.children:
            self._add_recursive(node.children[current_value], path[1:], drive_id, isDir)
        else:
            node.children[current_value] = TreeNode(current_value, drive_id, isDir)
            self._add_recursive(node.children[current_value], path[1:], drive_id, isDir)

    def remove(self, path):
        """
        Remove a node from the tree based on the given path.

        Parameters:
        - path: List representing the path to the node to be removed.
        """
        if self.root:
            self._remove_recursive(self.root, path)

    def _remove_recursive(self, node, path):
        """
        Recursively remove a node from the tree.

        Parameters:
        - node: The current node being processed.
        - path: Remaining path to traverse for node removal.
        """
        if len(path) == 0:
            return

        current_value = path[0]

        if current_value in node.children:
            if len(path) == 1:
                del node.children[current_value]
            else:
                self._remove_recursive(node.children[current_value], path[1:])
        else:
            pass  # Value not found in the children, do nothing

    def find_difference_path(self, tree2):
        """
        Compare two trees and find the differences in node paths between them.

        Parameters:
        - tree2: The second tree to compare with.

        Returns:
        A dictionary containing lists of additions and deletions.
        """
        changes_dic = {"Additions": [], "Deletions": []}

        def compare_and_print_paths(node1, node2, current_path):
            """
            Helper function to recursively compare nodes in two trees.

            Parameters:
            - node1: Current node in the first tree.
            - node2: Current node in the second tree.
            - current_path: Current path being traversed.
            """
            keys1 = set(node1.children.keys())
            keys2 = set(node2.children.keys())

            common_keys = keys1.intersection(keys2)
            changes = keys1.symmetric_difference(keys2)

            for file_change in changes:
                change_node = node1.children[file_change] if file_change in keys1 else node2.children[file_change]
                final_path = f"{'/'.join(current_path)}/{file_change}" if not current_path else f"/{'/'.join(current_path)}/{file_change}"
                if file_change in keys1:
                    changes_dic["Additions"].append((final_path, change_node.id, change_node.isDir))
                else:
                    changes_dic["Deletions"].append((final_path, change_node.id, change_node.isDir))

            for key in common_keys:
                compare_and_print_paths(node1.children[key], node2.children[key], current_path + [key])

        if self.root and tree2.root:
            compare_and_print_paths(self.root, tree2.root, [])

        return changes_dic

    def traverse_and_print(self):
        """
        Traverse and print the tree structure.
        """
        if self.root:
            self._traverse_and_print_recursive(self.root)

    def _traverse_and_print_recursive(self, node, depth=0):
        """
        Recursively traverse and print the tree structure.

        Parameters:
        - node: The current node being processed.
        - depth: Current depth in the tree.
        """
        print("\__ " * depth + str(node.value) + f" ({node.id})")
        for child_value, child_node in node.children.items():
            self._traverse_and_print_recursive(child_node, depth + 1)

    def get_node(self, path):
        """
        Get the node at the specified path.

        Parameters:
        - path: List representing the path to the desired node.

        Returns:
        The node at the specified path.
        """
        if self.root:
            return self._get_node(self.root, path, nodes_traversed=0)

    def _get_node(self, node, path, nodes_traversed):
        """
        Recursively get the node at the specified path.

        Parameters:
        - node: The current node being processed.
        - path: Remaining path to traverse.
        - nodes_traversed: Number of nodes traversed.

        Returns:
        The node at the specified path and the number of nodes traversed.
        """
        if not path:
            return node, nodes_traversed

        current_value = path[0]

        if current_value in node.children:
            return self._get_node(node.children[current_value], path[1:], nodes_traversed + 1)
        else:
            return node, nodes_traversed  # Return the current node and nodes traversed
