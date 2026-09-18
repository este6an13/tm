# transform to absolute minutes to plot scaled correctly
# if treated as time_int, plot shows a longer jump when going from 445 to 500
# if transform we would have equidistant jumps: 285 -> 300
def time_int_to_minutes(time_int: int) -> int:
    return (time_int // 100) * 60 + time_int % 100
