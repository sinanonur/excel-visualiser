from abc import ABC, abstractmethod
import pandas as pd

class LlmBase(ABC):
    @abstractmethod
    def generate_plot_code(self, prompt: str, df: pd.DataFrame, selected_columns: list = None) -> str:
        pass
