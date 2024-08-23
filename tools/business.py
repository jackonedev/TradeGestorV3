from schemas.targets import TargetResults


def calculate_targets(df, real_price=None):
    results = TargetResults.calculate(df, real_price)
    return results.dict()
