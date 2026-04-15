def test_package_importable():
    import monkey_devs
    assert monkey_devs.__version__ == "0.1.0"
