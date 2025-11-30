"""Minimal models used by Logic Apps clients in tests."""

class Workflow:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.name = kwargs.get("name", "")
        self.id = kwargs.get("id", "")
        self.location = kwargs.get("location", "")
        self.state = kwargs.get("state", "")
        self.created_time = kwargs.get("created_time")
        self.changed_time = kwargs.get("changed_time")
        self.definition = kwargs.get("definition")
        self.parameters = kwargs.get("parameters")
