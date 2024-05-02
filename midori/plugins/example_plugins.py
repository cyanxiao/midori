from .helpers import PluginHelper


class SkaffoldSetup(PluginHelper):
    def action(self) -> str:
        return f"cd {self.subject_path} && skaffold delete && skaffold run"
