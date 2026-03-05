# Defines the risk categories based on numeric scores

def get_risk_level(score):
    """
    Returns the classification level category for a calculated risk score.
    Returns:
      0  - 20  = LOW
      21 - 50  = MEDIUM
      51 - 100 = HIGH
      100+     = CRITICAL
    """
    if score <= 20:
        return "LOW"
    elif score <= 50:
        return "MEDIUM"
    elif score <= 100:
        return "HIGH"
    else:  # score > 100
        return "CRITICAL"
