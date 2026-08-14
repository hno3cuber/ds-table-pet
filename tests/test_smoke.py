def test_import_qt(qapp):
    from PySide6.QtWidgets import QWidget
    w = QWidget()
    assert w is not None
