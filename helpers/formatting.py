def format_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} GB"


def format_time(seconds: float) -> str:
    return f"{seconds * 1000:.2f} ms" if seconds < 1 else f"{seconds:.2f} s"
