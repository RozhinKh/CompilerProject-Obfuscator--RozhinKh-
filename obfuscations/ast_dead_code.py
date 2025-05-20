

PREFIX_DEADCODE = "deadcode_"
deadcode_counters = {'var': 0}


def generate_deadcode_variable_name():
    deadcode_counters['var'] += 1
    return f"{PREFIX_DEADCODE}{deadcode_counters['var']}"


def reset_dead_code_state():
    deadcode_counters['var'] = 0