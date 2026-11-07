# Robot tactile sensor: locate a touch from a taxel grid

This Python lab replays a synthetic 3 × 3 tactile pad. It estimates normal load and its center from integer readings after subtracting each sensing element's unloaded offset. It also shows when the estimate is misleading or invalid.

The full illustrated lesson is at [WIFA Robotics](https://wifarobotics.com/learn/robot-tactile-sensor/).

## Run it from zero

Install Python 3.10 or later using the [Python setup guide](https://docs.python.org/3/using/index.html). Download the repository ZIP from **Code → Download ZIP**, extract it, and open a terminal in the folder containing `tactile.py`. No pip installs are needed. On Windows, replace `python3` with `py -3`; on macOS or Linux, use the commands below.

```sh
python3 --version
python3 tactile.py examples/single-patch.json
python3 tactile.py examples/two-contacts.json
python3 tactile.py examples/quiet.json
python3 tactile.py examples/clipped.json
python3 -m unittest discover -s tests -v
```

| Input | Status | Estimated load | Center (x, y), mm |
| --- | --- | ---: | --- |
| `single-patch.json` | `contact` | 3 N | (8.333…, 5) |
| `two-contacts.json` | `contact` | 4 N | (5, 5), despite zero load at that cell |
| `quiet.json` | `below_threshold` | 0 N after filtering | `null` |
| `clipped.json` | `clipped` | `null` | `null`; inspect `clipped_row_col` |

The two axes start at the center of the top left taxel. x increases across columns; y increases down rows. JSON row and column indices start at zero. This is a flat sensor frame, independent of the robot coordinate system. Samples at ADC rails are unusable in this lab. They return a quality status without a load or center. A malformed file or configuration exits with code 2.

## Try a change

Copy the single patch file. Change `frame[1][2]` from 210 to 160. That taxel goes from 2 N to 1 N; total falls to 2 N and the x center moves to 7.5 mm. If Python reports a missing file, check that the terminal is beside `tactile.py`. If the result is unexpectedly quiet, inspect the unloaded baseline, deadband and minimum load before changing any threshold.

The supplied gains and frames are synthetic. The model assumes separate positive linear gains and ignores drift after baseline acquisition, cross talk, hysteresis, shear and slip. A force weighted center cannot identify individual contacts. No hardware, robot motion, safety logic or grasp controller was tested.

## Figures and tests

`diagrams/` contains editable SVGs and compact WebPs. From this directory, `python3 diagrams/draw.py` recreates the SVGs from the JSON inputs. Open the SVGs in an editor or export them using Inkscape. The tests check independent hand calculations, asymmetric coordinates, invalid readings, offset cancellation, threshold boundaries and the two contact ambiguity.
