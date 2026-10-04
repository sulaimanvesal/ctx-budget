"""Budget packing: decide what fits inside a context window."""

from __future__ import annotations

from dataclasses import dataclass, field

from .scan import FileStat


@dataclass
class BudgetResult:
    """Outcome of packing files into a context window."""

    context_window: int
    reserved_for_output: int
    usable_tokens: int
    included: list = field(default_factory=list)   # FileStat, biggest first
    excluded: list = field(default_factory=list)  # FileStat, biggest first
    tokens_used: int = 0

    @property
    def tokens_left(self) -> int:
        return self.usable_tokens - self.tokens_used

    @property
    def utilization(self) -> float:
        return self.tokens_used / self.usable_tokens if self.usable_tokens else 0.0


def pack_files(
    files: list,
    context_window: int,
    reserved_for_output: int = 0,
    must_include: list | None = None,
) -> BudgetResult:
    """Greedily pack files (largest first) into the usable context budget.

    *reserved_for_output* tokens are held back for the model's reply.
    *must_include* lists relative paths that are packed first regardless
    of size; if they don't fit, everything else is excluded.
    """
    if context_window <= 0:
        raise ValueError("context_window must be positive")
    if reserved_for_output < 0:
        raise ValueError("reserved_for_output must be non-negative")

    usable = context_window - reserved_for_output
    if usable <= 0:
        raise ValueError("reserved_for_output leaves no usable context")

    must_include = set(must_include or [])
    must = [f for f in files if f.path in must_include]
    rest = sorted(
        (f for f in files if f.path not in must_include),
        key=lambda f: f.tokens,
        reverse=True,
    )

    result = BudgetResult(context_window, reserved_for_output, usable)
    for f in must + rest:
        if result.tokens_used + f.tokens <= usable:
            result.included.append(f)
            result.tokens_used += f.tokens
        else:
            result.excluded.append(f)
    return result


def format_report(result: BudgetResult, total_scanned_tokens: int) -> str:
    """Render a human-readable budget report."""
    lines = [
        f"Context window : {result.context_window:,} tokens",
        f"Reserved output: {result.reserved_for_output:,} tokens",
        f"Usable budget  : {result.usable_tokens:,} tokens",
        f"Scanned total  : {total_scanned_tokens:,} tokens",
        f"Packed         : {result.tokens_used:,} tokens "
        f"({result.utilization:.1%} of budget), "
        f"{len(result.included)} files in / {len(result.excluded)} out",
        "",
        "Included (largest first):",
    ]
    for f in result.included[:15]:
        lines.append(f"  {f.tokens:>8,}  {f.path}")
    if len(result.included) > 15:
        lines.append(f"  ... and {len(result.included) - 15} more")
    lines.append("")
    lines.append("Excluded (biggest offenders):")
    for f in result.excluded[:10]:
        lines.append(f"  {f.tokens:>8,}  {f.path}")
    if len(result.excluded) > 10:
        lines.append(f"  ... and {len(result.excluded) - 10} more")
    return "\n".join(lines)
