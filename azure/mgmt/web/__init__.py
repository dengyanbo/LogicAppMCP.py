"""Minimal WebSiteManagementClient stub for testing."""

class _WebApps:
    def __init__(self):
        self.list_publishing_profile_xml_with_secrets = self._not_implemented
        self.get = self._not_implemented

    def _not_implemented(self, *args, **kwargs):
        raise NotImplementedError("Web apps operations are not implemented in stub")

class WebSiteManagementClient:
    def __init__(self, *args, **kwargs):
        self.web_apps = _WebApps()
