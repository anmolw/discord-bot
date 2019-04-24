def pretty_print_time(time_s):
    time_s = int(time_s)
    times = [
        ("year", 31536000),
        ("month", 2592000),
        ("week", 604800),
        ("day", 86400),
        ("hour", 3600),
        ("minute", 60),
        ("second", 1),
    ]

    result = []
    for name, length in times:
        val, time_s = divmod(time_s, length)
        if int(val) > 0:
            result.append(f"{int(val)} {name}{'s' if val > 1 else ''}")
            if int(time_s) <= 0:
                break
    return ", ".join(result)
