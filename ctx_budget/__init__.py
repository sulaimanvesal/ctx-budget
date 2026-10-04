"""ctx-budget: estimate how much of a codebase fits inside an LLM context window."""

from .budget import pack_files, BudgetResult
from .scan import scan_directory, FileStat
from .tokenizer import estimate_tokens

__all__ = ["scan_directory", "FileStat", "pack_files", "BudgetResult", "estimate_tokens"]
__version__ = "0.1.0"
