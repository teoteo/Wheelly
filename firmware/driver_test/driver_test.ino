// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// Wheelly - why the TMC2209 is not answering, asked of the board instead of
// the tester.
//
//     cd firmware && ./flash.sh driver_test
//
// `diag` in the real firmware can only say "SILENT", which is one bit of
// information and sends the hunt to five places at once. This sketch splits the
// tree instead, and it needs no probe on the board:
//
//   1. DOES THE SINGLE WIRE LOOP BACK? The TMC2209 UART is half duplex: TX goes
//      through R2 (1 k) onto the same hole RX comes off. So whatever we send
//      must come straight back to us - and that is true whether or not the
//      driver chip is alive, because it is our own transmitter driving the
//      line. If the echo does not come back, the fault is in the wire, in R2 or
//      in a joint, and the driver is not even in the picture yet. If it does
//      come back, the wire is good and the driver is the suspect.
//
//   2. IS IT LISTENING SOMEWHERE ELSE? The address is set by MS1 and MS2, and
//      the firmware asks for address 0, which the chip only takes with both of
//      them grounded. A pin left floating is the classic way to get exactly
//      this silence, so all four addresses are tried and the raw bytes printed.
//
//   3. WHAT CAME BACK, BYTE BY BYTE. A reply that arrives mangled - right
//      length, wrong CRC - means the wire works and the timing or the resistor
//      value is off, which looks identical to silence through the library.
//
// Nothing here writes to the driver: it only reads registers. Safe to run with
// the motor connected and 12 V on, which is the condition it needs anyway -
// without VM the chip is off and says nothing, and that is not a finding.

#include <string.h>

// The pins, from the board as it is wired. Same source as the real firmware:
// mechanics/wheelly-cad/src/wiring.py.
static const int PIN_UART_TX = 7;   // D8, through R2
static const int PIN_UART_RX = 8;   // D9, straight
static const long BAUD = 115200;

// The TMC2209 datagram CRC: poly 0x07, LSB first. Datasheet section 5.2.
static uint8_t crc_tmc(const uint8_t *datagram, uint8_t length)
{
    uint8_t crc = 0;
    for (uint8_t i = 0; i < length; i++) {
        uint8_t byte = datagram[i];
        for (uint8_t bit = 0; bit < 8; bit++) {
            if ((crc >> 7) ^ (byte & 0x01)) crc = (uint8_t)((crc << 1) ^ 0x07);
            else                            crc = (uint8_t)(crc << 1);
            byte >>= 1;
        }
    }
    return crc;
}

static void drain()
{
    while (Serial1.available()) Serial1.read();
}

// Reads up to `count` bytes, giving up after `ms`. Returns how many arrived.
static uint8_t read_reply(uint8_t *dest, uint8_t count, uint32_t ms)
{
    const uint32_t end = millis() + ms;
    uint8_t got = 0;
    while (got < count && (int32_t)(end - millis()) > 0) {
        if (Serial1.available()) dest[got++] = (uint8_t)Serial1.read();
    }
    return got;
}

static void print_bytes(const char *title, const uint8_t *b, uint8_t n)
{
    Serial.print(title);
    for (uint8_t i = 0; i < n; i++) {
        Serial.print(' ');
        if (b[i] < 0x10) Serial.print('0');
        Serial.print(b[i], HEX);
    }
    if (n == 0) Serial.print(" (nothing)");
    Serial.println();
}

// ---- 1. the single wire -------------------------------------------------
static bool test_echo()
{
    Serial.println("# 1. THE SINGLE WIRE: four bytes out, and they must come back");
    const uint8_t send[4] = {0x55, 0xAA, 0x0F, 0xF0};
    drain();
    Serial1.write(send, sizeof(send));
    Serial1.flush();

    uint8_t returned[8];
    const uint8_t n = read_reply(returned, sizeof(send), 50);
    print_bytes("#    sent: 55 AA 0F F0   came back:", returned, n);

    if (n == 0) {
        Serial.println("#    NOTHING COMES BACK. The fault is in the wire, not in the driver:");
        Serial.println("#    R2 between D8 (F08 / S08) and UART (M08 / L08) must read 1 kohm,");
        Serial.println("#    and D9 (E08 / T08) must read 0 ohm onto that same UART hole.");
        Serial.println("#    Until the echo comes back the TMC2209 is not the suspect.");
        return false;
    }
    if (n != sizeof(send) || memcmp(send, returned, sizeof(send)) != 0) {
        Serial.println("#    IT COMES BACK MANGLED. The wire is there but something spoils it:");
        Serial.println("#    R2 too large, a cold joint, or two resistors in series - some BTT");
        Serial.println("#    batches carry 1 kohm already, and then R2 has to come out.");
        return false;
    }
    Serial.println("#    THE ECHO COMES BACK CLEAN: wire, R2 and joints are all good.");
    Serial.println("#    So the whole suspicion moves onto the driver.");
    return true;
}

// ---- 2. the four addresses ----------------------------------------------
// Reads IOIN (0x06): it also tells which pins the chip sees high, which is the
// answer to the MS1/MS2 question if anybody answers at all.
static bool test_address(uint8_t node)
{
    uint8_t request[4] = {0x05, node, 0x06, 0};
    request[3] = crc_tmc(request, 3);

    drain();
    Serial1.write(request, sizeof(request));
    Serial1.flush();

    uint8_t all_ok[12];
    const uint8_t n = read_reply(all_ok, sizeof(all_ok), 50);

    Serial.print("#    address ");
    Serial.print(node);
    Serial.print(":");
    // The first four bytes are our own echo, which the single wire always
    // returns: only what comes after them is the driver talking.
    if (n <= 4) {
        Serial.println(" only our own echo, no reply");
        return false;
    }
    print_bytes(" reply", all_ok + 4, (uint8_t)(n - 4));
    if (n < 12) {
        Serial.println("#       short reply: fewer than eight bytes arrived");
        return false;
    }
    const uint8_t expected = crc_tmc(all_ok + 4, 7);
    if (expected != all_ok[11]) {
        Serial.print("#       WRONG CRC: expected ");
        Serial.print(expected, HEX);
        Serial.print(", got ");
        Serial.println(all_ok[11], HEX);
        return false;
    }
    const uint32_t ioin = ((uint32_t)all_ok[7] << 24) | ((uint32_t)all_ok[8] << 16)
                        | ((uint32_t)all_ok[9] << 8)  | (uint32_t)all_ok[10];
    Serial.print("#       IT ANSWERS. IOIN = 0x");
    Serial.println(ioin, HEX);
    Serial.print("#       silicon version: 0x");
    Serial.print((uint8_t)(ioin >> 24), HEX);
    Serial.println("  (a TMC2209 says 0x21)");
    Serial.print("#       MS1 = ");
    Serial.print((ioin >> 2) & 1);
    Serial.print("   MS2 = ");
    Serial.print((ioin >> 3) & 1);
    Serial.println("   (address 0 needs both of them at 0)");
    Serial.print("#       ENN = ");
    Serial.print(ioin & 1);
    Serial.println("   (1 = driver disabled, which is right at rest)");
    return true;
}

void setup()
{
    Serial.begin(115200);
    const uint32_t end = millis() + 2500;
    while (!Serial && (int32_t)(end - millis()) > 0) { }

    Serial1.begin(BAUD, SERIAL_8N1, PIN_UART_RX, PIN_UART_TX);
    delay(50);

    Serial.println();
    Serial.println("# ====================================================");
    Serial.println("# Wheelly - why the TMC2209 does not answer");
    Serial.println("# TX = D8 (GPIO7, behind R2)   RX = D9 (GPIO8, straight)");
    Serial.println("# 12 V must be on: without VM the chip is off and says nothing");
    Serial.println("# ====================================================");

    const bool wire = test_echo();

    Serial.println("#");
    Serial.println("# 2. THE FOUR ADDRESSES: the real firmware asks for 0");
    bool anyone = false;
    for (uint8_t node = 0; node < 4; node++)
        if (test_address(node)) anyone = true;

    Serial.println("#");
    Serial.println("# 3. WHAT IT ADDS UP TO");
    if (!wire) {
        Serial.println("#    The wire. Fix that first, then come back here.");
    } else if (!anyone) {
        Serial.println("#    The wire is good and nobody answers at any address.");
        Serial.println("#    Three things left, in this order:");
        Serial.println("#    - VM: do the 12 V really reach the driver VM (P02 / I02)?");
        Serial.println("#    - VDD: does the XIAO 3V3 (C08 / V08) reach driver VDD (J02 / O02)?");
        Serial.println("#    - the module: some stepsticks do not bring PDN_UART out to the");
        Serial.println("#      pin header at all, and those will never talk.");
    } else {
        Serial.println("#    Somebody answered: see above at which address.");
        Serial.println("#    If it is not 0, MS1 and MS2 are not grounded.");
    }
    Serial.println("# end");
}

void loop()
{
    delay(1000);
}
