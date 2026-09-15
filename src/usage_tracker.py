class UsageTracker:
    """
    Tracks LLM token usage and estimated cost.
    """

    def __init__(
        self,
        input_cost_per_million: float = 0.0,
        output_cost_per_million: float = 0.0,
    ):
        self.input_cost_per_million = input_cost_per_million
        self.output_cost_per_million = output_cost_per_million

        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.llm_calls = 0

    def record(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ):
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

        self.total_tokens = (
            self.input_tokens
            + self.output_tokens
        )

        self.llm_calls += 1

    @property
    def estimated_cost(self) -> float:
        input_cost = (
            self.input_tokens
            / 1_000_000
            * self.input_cost_per_million
        )

        output_cost = (
            self.output_tokens
            / 1_000_000
            * self.output_cost_per_million
        )

        return input_cost + output_cost

    def summary(self) -> dict:
        return {
            "llm_calls": self.llm_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(
                self.estimated_cost,
                6,
            ),
        }