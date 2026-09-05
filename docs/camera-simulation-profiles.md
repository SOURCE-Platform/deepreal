# Website Camera Simulation Profiles

Status: REFERENCE — for website video generation. These presets describe what footage
from the DeepReal reference cameras should look like. They are approximations of
documented hardware behavior, not captured prototype footage.

## 1. Verified hardware basis

Both drums currently reference the Sony IMX708-class bare sensor assembly
(Raspberry Pi Camera Module 3 sensor assembly). Production RGB sensors remain OPEN.

Official Raspberry Pi documentation values for the IMX708 / Camera Module 3:

| Property | Standard lens | Wide lens |
| --- | --- | --- |
| Sensor | Sony IMX708, 4608 × 2592 (11.9 MP) | same |
| Sensor active area | 6.45 × 3.63 mm (7.4 mm diagonal), 1/2.43" | same |
| Pixel size | 1.4 µm × 1.4 µm | same |
| Focal length | 4.74 mm | 2.75 mm |
| F-stop | F1.8 | F2.2 |
| Horizontal FoV | 66° | 102° |
| Vertical FoV | 41° | 67° |
| Focus | Motorized autofocus, ≈10 cm to ∞ | Motorized autofocus, ≈5 cm to ∞ |
| Video modes | 2304×1296p56, 2304×1296p30 HDR, 1536×864p120 | same |
| Max exposure | 112 s | same |
| IR filter | Standard variants have IR-cut filter | same |

Shutter: the IMX708 is a rolling-shutter sensor. Raspberry Pi's own documentation
states that all Camera Modules except the Global Shutter Camera (IMX296) use a
rolling shutter, scanning the image line by line. Fast lateral motion therefore
produces geometric skew.

Architecture capture targets (`docs/system-architecture/system-architecture.md`):

| Stream | Target | Note |
| --- | --- | --- |
| Face RGB | 1920×1080 @ 30 fps RAW10 | REFERENCE test target |
| Interaction RGB | 1920×1080 @ 60 fps RAW10 | preferred, may reduce |

1080p output is not a native sensor mode; it is produced by scaling/cropping the
2304×1296 readout, which preserves the lens field of view.

## 2. Face camera preset (face drum)

Simulate the **standard-lens** Camera Module 3 assembly.

- Resolution / frame rate: 1920×1080, 30 fps, 16:9.
- Field of view: 66° horizontal × 41° vertical. At a typical 50 cm face distance
  this frames the head and shoulders with margin; do not render wider.
- Depth of field: F1.8 at 4.74 mm on a 1/2.43" sensor gives a deep, webcam-like
  depth of field. At 40–70 cm the whole face is sharp; background softness is
  mild, not cinematic bokeh.
- Focus behavior: powered autofocus, minimum ≈10 cm. Occasional brief, subtle
  refocus hunting is realistic when the subject distance changes quickly.
- Shutter: rolling. A fast head turn produces slight vertical-edge lean
  (a few pixels of skew at most at 30 fps). Keep it subtle.
- Exposure: typical indoor office exposure around 1/60–1/120 s at low gain.
  Under dim lighting, gain rises and fine luminance/chroma noise appears
  (1.4 µm pixels are small); mild temporal noise reduction smearing on flat
  areas is realistic.
- Color: IR-cut filtered, neutral sRGB-style render, mild ISP sharpening with
  faint edge ringing on high-contrast text, and slight lens shading falloff
  toward corners (corrected, so only a hint remains).

## 3. Interaction camera preset (interaction drum)

Simulate the **wide-lens** Camera Module 3 assembly. The interaction drum watches
hands, keyboard and nearby space at short range, where the wide FoV and 5 cm
minimum focus are the appropriate documented variant.

- Resolution / frame rate: 1920×1080, 60 fps preferred (architecture target;
  may reduce to 30 fps if bandwidth/throughput validation fails).
- Field of view: 102° horizontal × 67° vertical. Hands and keyboard fill the
  frame from the drum's vantage point at close range.
- Lens distortion: the 2.75 mm wide lens shows visible barrel distortion.
  Simulate mild-to-moderate barrel distortion with straight keyboard edges
  curving outward near frame edges, plus slight corner sharpness falloff.
- Shutter: rolling, and this matters more here. Fast hand gestures at 60 fps
  show noticeable skew on fingers and keyboard edges moving laterally.
  Rolling-shutter wobble is also visible if the drum pans during capture.
- Exposure: motion-oriented; expect 1/120–1/240 s equivalents in good light to
  limit hand motion blur, with correspondingly higher gain and more visible
  noise than the face camera. Under poor light the auto-exposure trades off
  toward longer exposure and visible hand motion blur instead.
- Focus: minimum ≈5 cm; hands very close to the drum stay focusable.

## 4. Open decision: interaction rolling vs global shutter

The IMX708 is rolling shutter, and the interaction stream is the one most
exposed to fast motion. A global-shutter RGB alternative (for example an
OV9281-class derivative in color, matching the IR/depth receiver family) would
remove skew entirely but at much lower resolution and light sensitivity.

Recommendation: generate the website interaction videos with the IMX708 rolling-
shutter profile above, keep skew honest but not exaggerated, and revisit only if
hand-tracking quality requirements force a global-shutter RGB part.

## 5. Art-direction assumptions (not hardware specifications)

These are chosen presentation values, clearly separated from the verified values
above. Tune them for readability, but keep footage labeled as a simulation:

- Rolling-shutter skew strength: render at roughly one-frame readout
  (≈1/30 s face, ≈1/60 s interaction), applied as vertical shear by motion.
- Compression: H.264-like, ≈8–12 Mbit/s at 1080p; light macroblocking in
  shadows and on fast motion.
- White balance: auto, slightly cool office LED response, slow drift when the
  scene changes.
- Noise: fine grain, stronger in shadows and at high gain; no film grain
  stylization.
- No HDR tone mapping in the baseline simulations, even though the IMX708
  supports a 2304×1296p30 HDR mode.

## 6. Labeling requirement

All website videos using these profiles must be labeled as reference-camera
simulations, not footage captured from a DeepReal prototype. The exact
production RGB sensor is still an OPEN architecture decision.
