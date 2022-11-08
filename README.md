# pybinclock
Binary clock for Raspberry Pi with Unicorn Mini HAT

## What?
This LED binary clock displays the date and time (in local 24-hour time. Top row is the year, next the month, then day, 
followed by hour, minute and second. This code requires a Raspberry Pi equipped with a 
[Unicorn Mini HAT](https://shop.pimoroni.com/products/unicorn-hat-mini). Set that up (rtfm and such), run the examples, 
and then continue setting up this repo.

## Why?
Everyone needs a hobby and coding random things is my hobby. I also find coding to be a nice distraction from daily 
stresses. And, binary clocks are just cool.

## How?
First, clone the repo 
```
git clone https://github.com/rmrfslashbin/pybinclock.git
```

Set up the Python environement and fetch dependencies. This project uses [Poetry](https://python-poetry.org), but also 
provides `requirements.txt` for generic env set ups.

## Run!
The binary clock can be run via Poetry, from the root of the project directory.
```
poetry run BinClockLEDs
```
If not using Poetry, do something like
```
python pybinclock/BinClockLEDs
```

## Buttons!
Yeah, the buttons do stuff!
- Button A: Pause the clock, count the dots, do the math, and figure out what time it was when the button was pushed. Push the button again to resume.
- Button B: Mode toggle. Tired of counting binary bits? Push this button and get a scrolling ISO
- self.button_x.when_pressed = self.setExit
