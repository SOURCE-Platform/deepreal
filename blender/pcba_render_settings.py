"""Review render settings for native, closely spaced PCB surface geometry."""


def configure(scene):
    # EEVEE in this build obscures mask/pads behind the native substrate.
    # Cycles resolves the actual surfaces without moving copper or the board.
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
