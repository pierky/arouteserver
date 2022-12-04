# To show the output of pytest using the description of the test case.
def pytest_itemcollected(item):
    par = item.parent.obj

    short_descr = getattr(par, "SHORT_DESCR", "")

    node = item.obj

    suf = node.__doc__.strip() if node.__doc__ else node.__name__

    if suf:
        item._nodeid = suf.format(short_descr)
