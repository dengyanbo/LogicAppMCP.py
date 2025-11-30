"""Minimal LogicManagementClient stub used for testing."""

class _Workflows:
    def list_by_resource_group(self, *args, **kwargs):
        return []

    def get(self, *args, **kwargs):
        raise NotImplementedError("Workflow retrieval not implemented in stub")

    def create_or_update(self, *args, **kwargs):
        return None

    def delete(self, *args, **kwargs):
        return None

class _WorkflowRuns:
    def list(self, *args, **kwargs):
        return []

class _WorkflowTriggers:
    def list_callback_url(self, *args, **kwargs):
        # Provide object with value attribute for callback URL
        class Callback:
            def __init__(self):
                self.value = ""
        return Callback()

class LogicManagementClient:
    def __init__(self, *args, **kwargs):
        self.workflows = _Workflows()
        self.workflow_runs = _WorkflowRuns()
        self.workflow_triggers = _WorkflowTriggers()
