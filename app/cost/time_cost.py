class TimeCost:
    def estimate(self, minutes, hourly_rate=0.0):
        minutes = max(0.0, float(minutes))
        return {"minutes": round(minutes, 2), "estimated_cost": round(minutes / 60 * max(0.0, float(hourly_rate)), 2)}
