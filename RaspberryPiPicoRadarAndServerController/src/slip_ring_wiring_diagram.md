# Slip Ring Wiring Diagram (6-Wire)

This diagram and pinout will help you connect all devices through your 6-wire slip ring for I2C, UART, GND, and 5V power.

## Wire Assignments

| Slip Ring Wire | Function         | Pico Pin (Example) | Description                |
|:--------------:|:----------------|:-------------------|:---------------------------|
| 1              | SDA (I2C Data)  | GPIO 0             | I2C Data Line              |
| 2              | SCL (I2C Clock) | GPIO 1             | I2C Clock Line             |
| 3              | TX (UART Out)   | GPIO 16            | UART Transmit (Master Out) |
| 4              | RX (UART In)    | GPIO 17            | UART Receive (Master In)   |
| 5              | GND             | GND                 | Common Ground              |
| 6              | 5V              | VSYS or VBUS        | Power for all devices      |

## Example Pico Wiring

```
Slip Ring Wire 1 (SDA)  →  All Picos GPIO 0 (I2C0 SDA)
Slip Ring Wire 2 (SCL)  →  All Picos GPIO 1 (I2C0 SCL)
Slip Ring Wire 3 (TX)   →  Master Pico GPIO 16 (UART0 TX)
Slip Ring Wire 4 (RX)   →  Master Pico GPIO 17 (UART0 RX)
Slip Ring Wire 5 (GND)  →  All Picos GND
Slip Ring Wire 6 (5V)   →  All Picos VSYS/5V
```

- For **slave Picos** that do not use UART, leave TX/RX unconnected or available for future use.
- All Picos must share the same GND and 5V.
- Use pull-up resistors (2.2k–4.7kΩ) on SDA and SCL if not already present on your board.

## Visual Diagram

```
[Slip Ring]
 |--1-- SDA (I2C Data)  -----> GPIO 0 (All Picos)
 |--2-- SCL (I2C Clock) -----> GPIO 1 (All Picos)
 |--3-- TX (UART Out)   -----> GPIO 16 (Master Pico)
 |--4-- RX (UART In)    -----> GPIO 17 (Master Pico)
 |--5-- GND             -----> GND (All Picos)
 |--6-- 5V              -----> VSYS/5V (All Picos)
```

## Labeling Tips
- Use colored heat shrink or labels for each wire at both ends.
- Double-check continuity with a multimeter before powering up.
- Document which slip ring wire number corresponds to each function in your build log.

---

**This layout ensures clear, reliable connections for I2C, UART, GND, and power through your 6-wire slip ring.**
