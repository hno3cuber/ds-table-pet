from PySide6.QtWidgets import QLabel, QWidget
from pet.hud import HudPanel, OutlinedLabel


def test_hud_creates(qapp):
    hud = HudPanel()
    assert hud is not None


def test_add_block_appears_in_layout(qapp):
    hud = HudPanel()
    block = QLabel("CPU 12%")
    hud.add_block(block)
    # paused 标签本身也在 layout 末尾（add_block 插入其前），故 count = 1 block + 1 paused = 2
    assert hud.layout().count() == 2


def test_show_paused_sets_overlay(qapp):
    hud = HudPanel()
    hud.show_paused(True)
    assert hud._paused_label.isHidden() is False
    hud.show_paused(False)
    assert hud._paused_label.isHidden() is True


def test_set_scale_font(qapp):
    hud = HudPanel()
    block = QLabel("CPU 12%")
    hud.add_block(block)
    base = block.font().pointSizeF() or 13.0
    hud.set_scale(2.0)
    assert block.font().pointSizeF() >= base


def test_outlined_label_renders(qapp):
    """描边标签：渲染不崩溃且保留文本（真机需求：浅灰底上带描边字体）。"""
    from PySide6.QtGui import QPixmap

    label = OutlinedLabel("CPU 42%")
    label.resize(100, 30)
    pix = QPixmap(100, 30)
    pix.fill()
    label.render(pix)
    assert label.text() == "CPU 42%"
    assert label.outline.alpha() > 0
