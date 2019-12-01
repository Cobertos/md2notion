def pytest_generate_tests(metafunc):
    if "headerLevel" in metafunc.fixturenames:
        metafunc.parametrize("headerLevel", map(lambda n: n+1, range(6)))