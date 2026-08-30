class TokenCost:
    def estimate(self, calls=0, tokens_per_call=0, rate_per_thousand=0.0):
        calls, tokens_per_call = max(0, int(calls)), max(0, int(tokens_per_call))
        tokens = calls * tokens_per_call
        return {"ai_calls": calls, "tokens": tokens, "estimated_cost": round(tokens / 1000 * max(0.0, float(rate_per_thousand)), 6)}
