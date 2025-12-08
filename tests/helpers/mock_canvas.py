class MockCanvas:
    def __init__(self):
        self.next_id = 1
        self.items = {}
    def create_text(self, *args, **kwargs):
        _id = self.next_id; self.next_id += 1
        self.items[_id] = {'type': 'text', 'args': args, 'kwargs': kwargs}
        return _id
    def create_oval(self, *args, **kwargs):
        _id = self.next_id; self.next_id += 1
        self.items[_id] = {'type': 'oval', 'args': args, 'kwargs': kwargs}
        return _id
    def create_rectangle(self, *args, **kwargs):
        _id = self.next_id; self.next_id += 1
        self.items[_id] = {'type': 'rectangle', 'args': args, 'kwargs': kwargs}
        return _id
    def create_polygon(self, *args, **kwargs):
        _id = self.next_id; self.next_id += 1
        self.items[_id] = {'type': 'polygon', 'args': args, 'kwargs': kwargs}
        return _id
    def create_line(self, *args, **kwargs):
        _id = self.next_id; self.next_id += 1
        self.items[_id] = {'type': 'line', 'args': args, 'kwargs': kwargs}
        return _id
    def itemconfig(self, item_id, **kwargs):
        if item_id in self.items:
            self.items[item_id]['kwargs'].update(kwargs)
    def coords(self, item_id, *args):
        if item_id in self.items:
            self.items[item_id]['args'] = args
    def delete(self, item_id):
        self.items.pop(item_id, None)
    def tag_lower(self, item_id):
        pass
    def winfo_width(self):
        return 600
    def winfo_height(self):
        return 400
    def after(self, ms, func=None):
        # No timing in tests
        pass
    def update_idletasks(self):
        pass
    def bind(self, *args, **kwargs):
        # Event binding not needed in headless tests
        pass
    def winfo_pointerx(self):
        return 0
    def winfo_rootx(self):
        return 0
    def winfo_pointery(self):
        return 0
    def winfo_rooty(self):
        return 0
