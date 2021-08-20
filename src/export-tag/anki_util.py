from aqt import mw


def all_tags():
    return _all_partial_paths(mw.col.tags.all(), '::')


def _all_partial_paths(paths, seperator):
    result = set()
    for path in paths:
        while True:
            if path in result:
                break

            result.add(path)
            path = path.rsplit(seperator, maxsplit=1)[0]

    return result
