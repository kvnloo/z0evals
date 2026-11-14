def round_ratio(numerator, denominator):
    """Round an integer ratio to the nearest integer, with ties away from zero."""
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    return sign * (quotient + (2 * remainder >= denominator))
