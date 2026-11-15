"""Set dresser window. Reads its controls and calls the engine; nothing else.

    import set_dresser_ui; set_dresser_ui.show()
"""

import maya.cmds as cmds

import set_dresser

WINDOW = "setDresserWindow"


def show():
    """Open the Set Dresser window (closing an old copy first)."""
    if cmds.window(WINDOW, exists=True):
        cmds.deleteUI(WINDOW)

    cmds.window(WINDOW, title="Set Dresser", widthHeight=(380, 220), sizeable=False)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnOffset=("both", 8))

    rocks = cmds.intSliderGrp(label="Rocks", field=True, minValue=0, maxValue=200,
                              value=20, columnWidth3=(60, 50, 240))
    trees = cmds.intSliderGrp(label="Trees", field=True, minValue=0, maxValue=200,
                              value=10, columnWidth3=(60, 50, 240))
    area = cmds.floatSliderGrp(label="Area", field=True, minValue=10, maxValue=40,
                               value=40, precision=1, columnWidth3=(60, 50, 240))
    seed = cmds.intSliderGrp(label="Seed", field=True, minValue=0, maxValue=1000,
                             value=1, columnWidth3=(60, 50, 240))
    keep_clear = cmds.checkBox(label="Keep path and pond clear", value=True)

    def on_scatter(*_):
        set_dresser.scatter(
            rocks=cmds.intSliderGrp(rocks, query=True, value=True),
            trees=cmds.intSliderGrp(trees, query=True, value=True),
            area=cmds.floatSliderGrp(area, query=True, value=True),
            keep_clear=cmds.checkBox(keep_clear, query=True, value=True),
            seed=cmds.intSliderGrp(seed, query=True, value=True),
        )

    def on_clear(*_):
        set_dresser.clear()

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(180, 180), columnAttach2=("both", "both"))
    cmds.button(label="Scatter", height=32, command=on_scatter)
    cmds.button(label="Clear", height=32, command=on_clear)
    cmds.setParent("..")

    cmds.showWindow(WINDOW)
    return WINDOW
