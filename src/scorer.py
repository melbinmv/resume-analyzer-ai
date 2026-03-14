def calculate_score(matched, total_required):

    if total_required == 0:
        return 0

    score = (len(matched) / total_required) * 100

    return round(score, 2)