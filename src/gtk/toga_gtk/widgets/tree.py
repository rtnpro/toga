from gi.repository import Gtk

from .base import Widget


class Tree(Widget):
    def create(self):
        self.store = Gtk.TreeStore(*[str for h in self.interface.headings])

        # flat dict, maps Node to Gtk.TreeIter
        self.nodes = {}

        # Create a tree view, and put it in a scroll view.
        # The scroll view is the _impl, because it's the outer container.
        self.treeview = Gtk.TreeView(self.store)
        self.selection = self.treeview.get_selection()
        self.selection.set_mode(Gtk.SelectionMode.SINGLE)
        self.selection.connect("changed", self._on_select)

        for i, heading in enumerate(self.interface.headings):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(heading, renderer, text=i)
            self.treeview.append_column(column)

        self.native = Gtk.ScrolledWindow()
        self.native.interface = self.interface
        self.native.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.native.add(self.treeview)
        self.native.set_min_content_width(200)
        self.native.set_min_content_height(200)

    def row_data(self, item):
        return [
            str(getattr(item, attr))
            for attr in self.interface._accessors
        ]

    # Gtk.TreeIter cannot be compared with __eq__ !!!
    def compare_tree_iters(self, one, two):
        return self.store.get_path(one) == self.store.get_path(two)

    # find `tree_iter` in `self.rows`
    def get_node(self, tree_iter):
        if not isinstance(tree_iter, Gtk.TreeIter):
            raise TypeError("expected Gtk.TreeIter, got {}".format(type(tree_iter)))

        for node, it in self.nodes.items():
            if self.compare_tree_iters(tree_iter, it):
                return node

    def set_tree_iter(self, item, tree_iter):
        item._tree_iters = getattr(item, "_tree_iters", {})
        item._tree_iters[self] = tree_iter
        self.nodes[item] = tree_iter

    def _on_select(self, selection):
        if hasattr(self.interface, "_on_select") and self.interface.on_select:
            tree_model, tree_iter = selection.get_selected()
            row = self.get_node(tree_iter) if tree_iter else None
            self.interface.on_select(None, row=row)

    def change_source(self, source):
        # Temporarily disconnecting the TreeStore improves performance for large
        # updates by deferring row rendering until the update is complete.
        self.treeview.set_model(None)

        self.store.clear()

        def append_node(parent, root=False):
            parent_impl = None if root else self.nodes[parent]
            for i, child_node in enumerate(parent):
                self.insert(parent, i, child_node)
                # impl = self.store.append(parent_impl, self.row_data(child_node))
                # self.set_impl(child_node, impl)
                append_node(child_node)

        append_node(self.interface.data, root=True)

        self.treeview.set_model(self.store)

    def insert(self, parent, index, item, **kwargs):
        tree_iter = self.store.insert(
            self.nodes.get(item, None),
            index,
            self.row_data(item)
        )
        self.set_tree_iter(item, tree_iter)

    def change(self, item):
        tree_iter = self.nodes[item]
        self.store[tree_iter] = self.row_data(item)

    def remove(self, item):
        tree_iter = self.nodes[item]
        del self.store[tree_iter]
        del self.nodes[item]

    def clear(self):
        self.store.clear()

    def set_on_select(self, handler):
        pass
