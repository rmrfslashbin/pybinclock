# pybinclock
Binary clock for Raspberry Pi with Unicorn Mini HAT

## What?
The LED binary clock displays the date and time (local, 24-hour clock). The top row is the year, next the month, then day, 
followed by hours, minutes, and seconds. The code requires a Raspberry Pi equipped with a 
[Unicorn Mini HAT](https://shop.pimoroni.com/products/unicorn-hat-mini). Set up the rpi and the HAT (rtfm and such), run the examples, 
and then continue setting up this repo.

## Why?
Everyone needs a hobby and coding random things is my hobby. I also find coding to be a nice distraction from daily 
stresses. And, binary clocks are just cool.

## How?
First, clone the repo 
```
git clone https://github.com/rmrfslashbin/pybinclock.git
```

Set up the Python environement and fetch dependencies. This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

Set an env var `export GPIOZERO_PIN_FACTORY=lgpio` to force use of `lpgio`.

## Run!
The binary clock can be run via uv, from the root of the project directory.
```
uv run BinClockLEDs
```
Or without uv:
```
python pybinclock/BinClockLEDs
```

## Buttons!
Yeah, the buttons do stuff!
- Button A: Pause the clock, count the dots, do the math, and figure out what time it was when the button was pushed. Push the button again to resume.
- Button B: Mode toggle. Tired of counting binary bits? Push this button and get a scrolling ISO 8610 date & time.
- Button X: raise SystemExit.

## Feedback and Issues
I'm happy to review issues posts or PRs to fix issue or add features. However, this is a side project I work on when I need a break form the daily grind. I'm often distracted or sidetracked. This code does not follow any particular best practices or standards. It may or may not work on first try. YMMV.
