def _fmt_size(b):
    if b < 1024:
        return f'{b} B'
    if b < 1048576:
        return f'{b / 1024:.1f} KB'
    return f'{b / 1048576:.2f} MB'
