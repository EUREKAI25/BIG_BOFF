class BddStorage:
    def __init__(self, catalog=None):
        self.catalog = catalog

    def get_scenario(self, ident):
        raise NotImplementedError("BDD storage not implemented yet")

    def get_function(self, ident):
        raise NotImplementedError("BDD storage not implemented yet")

    def get_filter(self, ident):
        raise NotImplementedError("BDD storage not implemented yet")

    def get_first_object_by_filter(self, filter_name):
        raise NotImplementedError("BDD storage not implemented yet")
