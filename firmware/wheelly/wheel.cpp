// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

#include "wheel.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

namespace wheelly {

namespace {

// The settling wait is a setting (`settle`, m_settle_ms;
// FACTORY_SETTLE_MS in wheelly_protocol.h): the move time cap counts it. The
// disc has inertia and the tyre gives back a little: reading right after the
// last step gives an angle that then changes by itself. The motor holds at the
// run current through it (start_positioning, release).

// The AS5600 has a few LSB of noise, and at 4096 counts per turn one LSB is
// 0.088 degrees: exactly the scale of the tolerances at stake. It is averaged.
const int READINGS_PER_MEASURE = 8;

// The move time cap is not a fixed number (a fixed 25 s was REJECTED): with
// one-way moves the longest path is nearly two turns, not half of one, and a fixed
// number was either too short for a slow motor or pointlessly long for a
// fast one. It is derived in Wheel::ceiling_ms() from speed, acceleration,
// retries and direction; these two numbers are its margin, on top of the
// computed worst case: 25% for what the model leaves out, and one second for
// the readings and the serial line.
const float CEILING_MARGIN = 1.25f;
const float CEILING_ALLOWANCE_S = 1.0f;

// THE AIM SHORT, one way only (see start_leg). Each leg stops
// UNDERSHOOT_FRACTION of the distance short of the target, at least
// UNDERSHOOT_MIN_DEG; within 2 * UNDERSHOOT_MIN_DEG it goes LAST_LEGS_SHARE of
// the way. The fraction must be MORE than the step estimate can be off by,
// or a leg overshoots and pays a whole turn: the factory ratio is declared
// from the model, and the learnt one is kept within 15 % of the base, so +-10 % is
// allowed for (the bench tries both ends), and 12 % leaves a margin for the
// reading and the detent. A trial value of 8 % (REJECTED) arrived in four
// legs on the reference wheel, the estimate being short (0.84-0.92): it only
// worked because the error happened to fall on the safe side.
const float UNDERSHOOT_FRACTION = 0.12f;
const float UNDERSHOOT_MIN_DEG = 1.0f;
const float LAST_LEGS_SHARE = 0.6f;
// Approach legs: legs after one that moved towards the target and did not
// pass it. They are the method, not a failure, so they do not use up the
// retries (counted as retries, a converging wheel ended "failed" or
// "warning" with retries=3); this is their own bound. With the aim short
// and the learnt lost motion a long move takes five to seven; the rest is
// margin.
const int APPROACH_LEGS_MAX = 10;
// A leg that moved less than this share of what it aimed at made no
// progress: a stall against the detent, a slipping clutch. The leg after it
// is a retry.
const float NO_PROGRESS_SHARE = 0.2f;
// A leg shorter than this is a SHORT leg: the lost motion is learnt from it,
// and when it does not move it may be the play being taken up, not a stall.
// The ratio is learnt from the LONG legs only, with the guards written at
// LEARN_MIN_DEG below. A first, unguarded attempt was REJECTED: it saved a
// leg now and then on the benches, and a leg cut short by a notch of the
// detent taught it a ratio 40 % low, so that the next legs went past the
// target.
const float SHORT_LEG_DEG = 5.0f;
// THE LOST MOTION (m_lost, seen on the reference wheel): the disc
// stopped 0.6-1.0 degrees short and the small creep legs did not close it -
// the TPU tyre of the clutch absorbs about 15 microsteps (0.6 degrees of disc)
// before the disc moves, and with the motor released at rest it gives them
// back, so every leg loses them again. Every leg therefore sends that much
// more, and it is learnt from the short legs (what they were sent minus what
// they did). A short leg that did not move at all says only that the loss is
// larger than what it was sent: the next one sends LOST_STEP_DEG more. Up to
// LOST_MAX_DEG; past that a leg that does not move is a stall. It starts at
// zero, so a drive without that play is never pushed past its target, and
// it is kept from one positioning to the next (in RAM, not saved): it is
// the drive's, not the move's.
// The step is also kept to half the good tolerance: if the loss was in
// fact exactly what the silent leg was sent, the next one overshoots by the
// step, and that must still land inside the good tolerance.
const float LOST_STEP_DEG = 0.2f;
const float LOST_MAX_DEG = 2.0f;

// THE RATIO IS LEARNT - see SHORT_LEG_DEG above, and firmware.md, "The drive
// ratio". An unguarded learning was rejected because a leg cut short by a
// notch of the detent taught a ratio 40 % low; the detent is now always
// removed, and every one of these guards is there so that a leg cut short for
// another reason cannot do it again. A leg teaches the ratio only if ALL of these hold:
//   - it is the FIRST leg of a `go`: not a jog (whoever jogs is centring by
//     hand, and may stop it), not an approach leg (short, and aimed from a
//     disc that has just stopped), not a retry (it follows a stall or an
//     overshoot, i.e. something that went wrong);
//   - it wanted at least LEARN_MIN_DEG of disc, so that the tyre's play and
//     the sensor's resolution weigh little: the play is ~0.6 degrees, 2 % of
//     30, and one AS5600 count is 0.09 degrees, 0.3 % of 30;
//   - the play is known (m_lost_known): what the leg sent on top of its aim is
//     the measured give of the tyre, not a guess;
//   - it progressed (the stall test of the approach legs), and the magnet was
//     seen at every reading while it ran: a leg during which the sensor was
//     lost has a "to" that means nothing;
//   - what it says is within LEARN_OUTLIER of the ratio in use: a leg cut
//     short by a third is thrown away, not averaged in.
// What it says goes in with the weight LEARN_WEIGHT (an exponential moving
// average: a leg 10 % off pulls the ratio by 2.5 %), and the ratio in use is
// kept within LEARN_CLAMP of the base: a wheel further off than that must be
// MEASURED (firmware/ratio_test.py) and the value set with `ratio`, because
// the learning is a refinement, not a calibration.
const float LEARN_MIN_DEG = 30.0f;
const float LEARN_OUTLIER = 0.15f;
const float LEARN_WEIGHT = 0.25f;
const float LEARN_CLAMP = 0.15f;

// The longest path one positioning may travel, in degrees of disc. Shortest
// way: half a turn, and the retries are corrections, paid as legs below.
// One way: just under a turn to get there - the approach legs of the aim
// short add up to that same distance, they do not add to it - plus ONE
// retry that goes round the whole turn after an overshoot: it cannot back up
// against the detent. Worse than that (overshooting twice) runs past the cap
// and ends "failed", which is the honest outcome.
// A JOG'S TOLERANCE. A jog of 0.05 or 0.1 degrees is smaller
// than the good tolerance (0.3 by default), so judged by it the wheel would "arrive"
// without moving at all. A jog is judged by half its own size instead, but
// never tighter than JOG_GOOD_MIN_DEG - half an AS5600 count (0.088 degrees),
// below which the sensor cannot tell - and never looser than the set good
// tolerance: a 10 degree jog is judged like a `go`.
const float JOG_GOOD_MIN_DEG = 0.044f;
// A JOG MUST HAVE GONE. A jog is judged by the distance from its
// own target, like a `go`, and a `go` that ends inside the warning tolerance
// is a warning. But the warning band (0.8 degrees by default) is wider than
// the small jogs: a +1 or +0.1 jog that STALLED, the
// disc never moving, ended 1 or 0.1 degrees from its target - inside the
// band - and was reported as a warning, which the panel shows as a done jog.
// So a jog that did not cover at least this share of its own size, the way
// it was asked, is not a warning: it goes on to the retries, like a leg that
// made no progress, and ends "failed" if they do not move it either. Half,
// as the jog's good tolerance: a jog that covered half of itself is judged by
// its distance from the target, as before.
const float JOG_MOVED_SHARE = 0.5f;
// A jog of half a turn (a two-slot wheel's pitch) has no shorter way, and
// the rounding of normalize() decided which way it went: within this much of
// half a turn, a jog goes the way its sign says.
const float JOG_TIE_DEG = 1.0f;

const float LONGEST_SHORTEST_DEG = 180.0f;
const float LONGEST_ONE_WAY_DEG = 720.0f;

// The storage keys are composed, instead of living in three tables to keep
// aligned by hand with the number of slots.
//
// The slot is a uint8_t and not an int, and it is not a matter of style: with
// an int the compiler has to allow for ten digits, that is up to twelve bytes
// in a buffer of eight, and it says so - "output may be truncated". The warning
// shows only when compiling for the ESP32, not in the tests on the Mac. Written
// uint8_t, the type declares the true range: slots are at most MAX_SLOTS = 12,
// the longest key is "a12" and four bytes of margin remain. The number has not
// changed, what the compiler knows about it has.
void key(char *out, size_t size, char letter, uint8_t slot)
{
    snprintf(out, size, "%c%d", letter, slot + 1);
}

// The names of a newborn wheel. Beyond the fifth it goes on with "Filter6" and
// so on: generic but valid names, which the user will change.
const char *FACTORY_NAMES[] = {"Lum", "Red", "Green", "Blue", "Ha"};

}  // namespace

const char *direction_name(Direction d)
{
    switch (d) {
        case Direction::UP:   return ARG_UP;
        case Direction::DOWN: return ARG_DOWN;
        default:              return ARG_SHORTEST;
    }
}

bool direction_from_name(const char *name, Direction &out)
{
    if (name == nullptr) return false;
    if (strcmp(name, ARG_SHORTEST) == 0) { out = Direction::SHORTEST; return true; }
    if (strcmp(name, ARG_UP) == 0)       { out = Direction::UP;       return true; }
    if (strcmp(name, ARG_DOWN) == 0)     { out = Direction::DOWN;     return true; }
    return false;
}

const char *leg_kind_name(LegKind k)
{
    switch (k) {
        case LegKind::APPROACH: return KIND_APPROACH;
        case LegKind::RETRY:    return KIND_RETRY;
        default:                return KIND_FIRST;
    }
}

float normalize(float degrees)
{
    float r = fmodf(degrees, 360.0f);
    if (r < 0) r += 360.0f;
    return r;
}

float difference(float a, float b)
{
    return normalize(a - b + 180.0f) - 180.0f;
}

Wheel::Wheel(Mechanics &mechanics, Storage &storage)
    : m_mechanics(mechanics), m_storage(storage)
{
    direction_from_name(FACTORY_DIRECTION, m_direction);
    spread_evenly();
}

void Wheel::spread_evenly()
{
    // A new wheel, or one whose number of slots has just changed: angles split
    // into equal parts and generic names. It is not the true calibration, but
    // it is a sensible starting point, and above all it is usable: the wheel
    // works even before someone calibrates it.
    const int count = (int)(sizeof(FACTORY_NAMES) / sizeof(FACTORY_NAMES[0]));
    for (int i = 0; i < m_slots; i++) {
        m_angles[i] = normalize(i * (360.0f / m_slots));
        if (i < count && m_slots == FACTORY_SLOTS)
            snprintf(m_names[i], sizeof(m_names[i]), "%s", FACTORY_NAMES[i]);
        else
            snprintf(m_names[i], sizeof(m_names[i]), "Filter%d", i + 1);
    }
}

bool Wheel::set_slots(int count, Error &error)
{
    if (count < MIN_SLOTS || count > MAX_SLOTS) { error = ERR_OUT_OF_RANGE; return false; }
    if (m_motion == Motion::MOVING || m_motion == Motion::SETTLING) { error = ERR_NOT_NOW; return false; }
    if (count == m_slots) return true;

    // Changing the number of slots throws away the old calibration, and it
    // could not be otherwise: the angles of a five-slot wheel mean nothing on a
    // seven-slot one. Better to start again from evenly spaced angles than to
    // keep numbers that look like a calibration and are not.
    m_slots = count;
    spread_evenly();
    m_wanted_slot = 1;
    m_outcome = Outcome::NONE;
    return true;
}

void Wheel::load_or_default()
{
    float value;
    // The number of slots is read first: everything else depends on it.
    if (m_storage.load("slots", value)) {
        const int count = (int)value;
        // a 1 saved by a firmware older than MIN_SLOTS is not taken: the
        // wheel starts again from the factory number, and says so in `slots`
        if (count >= MIN_SLOTS && count <= MAX_SLOTS) m_slots = count;
    }
    spread_evenly();

    char k[8];
    for (int i = 0; i < m_slots; i++) {
        key(k, sizeof(k), 'a', i);
        if (m_storage.load(k, value)) m_angles[i] = normalize(value);
        key(k, sizeof(k), 'n', i);
        const char *text = nullptr;
        if (m_storage.load(k, text) && text != nullptr &&
            check_filter_name(text) == NAME_OK) {
            snprintf(m_names[i], sizeof(m_names[i]), "%s", text);
        }
    }
    if (m_storage.load("tol_good", value)) m_good_tolerance = value;
    if (m_storage.load("tol_warn", value)) m_warn_tolerance = value;
    if (m_storage.load("retries", value))  m_max_retries = (int)value;
    if (m_storage.load("run_ma", value))   m_run_current = (uint16_t)value;
    if (m_storage.load("hold_ma", value))  m_hold_current = (uint16_t)value;
    // a later key: a wheel saved before it keeps the factory
    // 300 ms, which is what its firmware did; out of range = corrupted key
    if (m_storage.load("settle_ms", value) && value >= 0.0f && value <= (float)SETTLE_MS_MAX)
        m_settle_ms = (uint32_t)value;
    if (m_storage.load("speed", value))    m_speed = (uint32_t)value;
    if (m_storage.load("accel", value))    m_acceleration = (uint32_t)value;
    // "detent" (a removed setting) is no longer read: a wheel that saved it
    // keeps the key, harmless (wheelly_protocol.h, NO DETENT OPTION)
    // a later key: a wheel saved before it keeps the factory way
    if (m_storage.load("direction", value) && value >= 0.0f && value <= 2.0f)
        m_direction = (Direction)(int)value;
    if (m_storage.load("led_mode", value) && value >= 0.0f && value <= 2.0f)
        m_led_mode = (LedMode)(int)value;
    // later keys: a wheel saved before them starts from the
    // factory ratio, learning. A saved ratio outside the protocol's range is
    // not taken (it could only be a corrupted key): the factory one is.
    if (m_storage.load("ratio", value) && value >= DRIVE_RATIO_MIN && value <= DRIVE_RATIO_MAX)
        m_base_ratio = value;
    m_ratio = m_base_ratio;
    if (m_storage.load("ratio_learn", value)) m_learn = value != 0.0f;
    fold_old_trims();
}

void Wheel::fold_old_trims()
{
    // THE ROTATION TRIM WENT (protocol 2; firmware.md, "One number per
    // slot"), but a wheel saved before keeps its trims in NVS, o1..o12, and
    // the wheel went to angle + trim. Dropping them would move every slot
    // that had one by that much, without a word. So a trim different from
    // zero is added to its slot's angle, the angle is written back, and the
    // trim's key is erased - ONCE: the next start finds no key and adds
    // nothing. The order is the one that loses nothing: the angle first, the
    // key after. A power cut between the two (a few milliseconds, once in the
    // life of a wheel) would add the trim twice at the next start, a slot off
    // by its trim and put right by teaching it again; the other order would
    // lose the trim instead, silently. Every key up to MAX_SLOTS goes, the
    // slots beyond m_slots too: they belong to a number of slots the wheel
    // no longer has, and nobody would ever erase them.
    char k[8];
    float value;
    bool wrote = false;
    for (int i = 0; i < MAX_SLOTS; i++) {
        key(k, sizeof(k), 'o', (uint8_t)i);
        if (!m_storage.load(k, value)) continue;
        if (i < m_slots && value != 0.0f) {
            m_angles[i] = normalize(m_angles[i] + value);
            char a[8];
            key(a, sizeof(a), 'a', (uint8_t)i);
            m_storage.store(a, m_angles[i]);
        }
        m_storage.erase(k);
        wrote = true;
    }
    if (wrote) m_storage.commit();
}

void Wheel::begin()
{
    load_or_default();
    apply_currents();
    m_mechanics.speed(m_speed, m_acceleration);

    // The encoder is absolute over the disc's turn, so at power-up the position
    // is already known: no homing, ever. It is read and we know where we are,
    // even if someone turned the wheel by hand with the machine off.
    if (m_mechanics.sensor_responds()) {
        m_angle = average_reading();
        const int where = current_slot();
        m_wanted_slot = where > 0 ? where : 1;
        m_target = m_angles[m_wanted_slot - 1];
    }
    release();
}

float Wheel::average_reading()
{
    // Angles are averaged on the circle, not as numbers: between 359 and 1 the
    // arithmetic mean would give 180, that is the opposite side of the wheel.
    float sx = 0, sy = 0;
    for (int i = 0; i < READINGS_PER_MEASURE; i++) {
        const float a = m_mechanics.angle() * (float)M_PI / 180.0f;
        sx += cosf(a);
        sy += sinf(a);
    }
    return normalize(atan2f(sy, sx) * 180.0f / (float)M_PI);
}

void Wheel::apply_currents()
{
    // During a positioning the driver's HOLD current is the RUN current.
    // The TMC2208 drops to its hold current by itself 0.44 s
    // after the last step (TPOWERDOWN, left at its default), and with the
    // hold at 0 it then lets the coils freewheel: a settling wait longer than
    // that would have released the disc half way through, while the verdict
    // still waited. With the hold raised to the run current the chip's own
    // drop changes nothing, and the wait holds as long as it is set.
    m_mechanics.currents(m_run_current, m_positioning ? m_run_current : m_hold_current);
}

void Wheel::release()
{
    // At rest the driver is disabled by default: no heat next to the cooled
    // sensor, no chopper singing during the exposure. Whoever's wheel drifts
    // at rest (the drift watch says so) sets a holding current, and then the
    // driver stays enabled. It is called after the settling wait, never
    // before: the wait is what lets the stopped motor brake the disc.
    m_positioning = false;
    if (m_hold_current > 0) {
        apply_currents();
        m_mechanics.enable(true);
    } else {
        // off first, then the hold current back to 0: the other way round
        // the coils would freewheel for an instant with EN still low
        m_mechanics.enable(false);
        apply_currents();
    }
}

bool Wheel::go(int slot, Error &error)
{
    if (slot < 1 || slot > m_slots) { error = ERR_OUT_OF_RANGE; return false; }
    if (!m_mechanics.sensor_responds())    { error = ERR_SENSOR_SILENT; return false; }
    if (!m_mechanics.magnet_seen())       { error = ERR_NO_MAGNET;     return false; }

    m_wanted_slot = slot;
    m_jogging = false;
    m_good_now = m_good_tolerance;
    m_angle = average_reading();
    m_target = m_angles[slot - 1];
    start_positioning();
    return true;
}

bool Wheel::jog(float degrees, Error &error)
{
    // the order of teach: range, motion, sensor
    if (!(fabsf(degrees) <= (float)JOG_MAX_DEG)) { error = ERR_OUT_OF_RANGE; return false; }
    if (m_motion == Motion::MOVING || m_motion == Motion::SETTLING) { error = ERR_NOT_NOW; return false; }
    if (!m_mechanics.sensor_responds()) { error = ERR_SENSOR_SILENT; return false; }
    if (!m_mechanics.magnet_seen())    { error = ERR_NO_MAGNET;     return false; }

    // A TARGET, not a number of steps: the angle read
    // now plus the jog, reached by the same legs as `go`. Raw steps would not
    // do: the TPU tyre swallows ~0.6 degrees before the disc moves, so a
    // 0.05 degree jog of steps moves nothing, and a 1 degree one moves 0.4.
    // The slot asked for last stays the one the events name: jogging is how
    // that slot is centred, then taught ("Save position" in the panel).
    //
    // THE SHORTEST WAY, whatever `direction` says. A jog is a few degrees one
    // way, chosen by whoever presses the button; one way only, a jog against
    // it would go round the whole turn, across the other filters, and a
    // correction after an overshoot too. On a mechanism stiffer one way (as
    // an asymmetric detent is) a jog the stiff way may stall: it then ends
    // "warning" or "failed", honestly, and the jog the other way still works.
    m_jogging = true;
    m_good_now = fminf(m_good_tolerance, fmaxf(JOG_GOOD_MIN_DEG, 0.5f * fabsf(degrees)));
    m_angle = average_reading();
    m_jog_from = m_angle;
    m_jog_degrees = degrees;
    m_target = normalize(m_angle + degrees);
    start_positioning();
    return true;
}

void Wheel::start_positioning()
{
    m_retries = 0;
    m_legs = 0;
    m_approach_legs = 0;
    m_boosts = 0;
    m_boost_next = false;
    m_outcome = Outcome::NONE;
    m_move_start = m_mechanics.milliseconds();

    // held at the run current from now until release(), settling waits
    // included (apply_currents)
    m_positioning = true;
    apply_currents();
    m_mechanics.enable(true);
    m_leg_kind = LegKind::FIRST;
    start_leg();
}

void Wheel::start_leg()
{
    // Which way round. The encoder sits downstream of the clutch, so the
    // backlash is not compensated on paper: it is measured and corrected from
    // whichever side we arrive - and that is what lets the direction be a
    // free choice.
    //
    // SHORTEST: the shorter way on the circle.
    // UP / DOWN: always the same way, for a mechanism stiffer one way (born
    // for an asymmetric detent, now always removed: the motor stalled and
    // hummed against its steep flank). Every leg
    // goes that way, retries included: after an overshoot the wheel goes
    // round (360 - overshoot) instead of backing up into the detent. Already
    // within the good tolerance nothing moves - a hair behind the target
    // would otherwise cost a whole turn - and the verdict, as always, is
    // given by the angle read, not by the steps counted.
    float delta = difference(m_target, m_angle);
    if (m_direction != Direction::SHORTEST && !m_jogging) {
        if (fabsf(delta) <= m_good_tolerance) delta = 0.0f;
        else if (m_direction == Direction::UP) delta = normalize(m_target - m_angle);
        else delta = -normalize(m_angle - m_target);
        m_leg_sign = (m_direction == Direction::UP) ? 1 : -1;
        m_leg_distance = fabsf(delta);
        // AIM SHORT (learnt from the first moves on the reference wheel).
        // One way, an
        // overshoot is paid with a whole turn, and the whole turn overshoots
        // by the same few percent again: the wheel went round and round and
        // ended "not reached". So each leg stops short of the target by more
        // than the step estimate can be off (the constants say how much), and
        // the next legs creep forward; the last few degrees go at
        // LAST_LEGS_SHARE so they cannot jump past either. The shortest way
        // does not need it: an overshoot there costs a small step back.
        const float d = m_leg_distance;
        float aim = d;
        if (d > 2.0f * UNDERSHOOT_MIN_DEG)
            aim = d - fmaxf(UNDERSHOOT_FRACTION * d, UNDERSHOOT_MIN_DEG);
        else if (d > m_good_tolerance)
            aim = LAST_LEGS_SHARE * d;
        delta = (delta < 0.0f) ? -aim : aim;
    } else {
        // Half a turn has no shorter way: difference() puts it at -180 or
        // just under +180 as the rounding falls, and a +180 jog went
        // backwards (jogs go up to a slot pitch, 180 on a two-slot
        // wheel). A jog near the tie goes the way it was asked.
        if (m_jogging && fabsf(delta) > 180.0f - JOG_TIE_DEG &&
            (delta < 0.0f) != (m_jog_degrees < 0.0f))
            delta = (m_jog_degrees < 0.0f) ? -(360.0f - fabsf(delta)) : 360.0f - fabsf(delta);
        m_leg_sign = delta >= 0 ? 1 : -1;
        m_leg_distance = fabsf(delta);
    }
    // What the leg's steps are worth by the declared ratio: the degrees
    // wanted, PLUS the lost motion the drive swallows before the disc starts
    // to turn (m_lost, learnt). A leg that wants nothing sends nothing.
    m_leg_from = m_angle;
    m_leg_aim = fabsf(delta);
    const float commanded = m_leg_aim > 0.0f ? m_leg_aim + m_lost : 0.0f;
    m_leg_commanded = delta < 0.0f ? -commanded : commanded;
    m_legs++;
    delta = m_leg_commanded;
    // THE BOOST: after a stall, this one leg at twice the speed and the
    // acceleration (see BOOST_SPEED_MAX); every other leg at the set speed,
    // which is also what brings it back after a boosted one.
    uint32_t v = m_speed, a = m_acceleration;
    if (m_boost_next) {
        const uint32_t v_max = BOOST_SPEED_MAX < MOTOR_SPEED_MAX ? BOOST_SPEED_MAX
                                                                 : MOTOR_SPEED_MAX;
        v = 2 * m_speed < v_max ? 2 * m_speed : v_max;
        a = 2 * m_acceleration < MOTOR_ACCEL_MAX ? 2 * m_acceleration
                                                 : (uint32_t)MOTOR_ACCEL_MAX;
        if (v < m_speed) v = m_speed;           // a set speed above the cap stays
        if (a < m_acceleration) a = m_acceleration;
        if (v > m_speed) m_boosts++;
        m_boost_next = false;
    }
    m_mechanics.speed(v, a);
    const long steps = (long)lroundf(delta * steps_per_degree(m_ratio));
    m_leg_ratio = m_ratio;
    m_leg_steps = steps;
    m_leg_magnet_ok = true;
    // A move re-arms the watch: during it and right after, a large error is
    // the move and not a drift.
    m_drift_out = false;
    m_drift_to_report = false;
    m_motion = Motion::MOVING;
    m_mechanics.move(steps);
}

uint32_t Wheel::ceiling_ms() const
{
    // The worst case of a whole positioning, from the motor's own numbers:
    // the longest path the direction allows as one trapezoidal move (ramp up
    // at the acceleration, cruise at the speed, ramp down), plus, for every
    // leg - the first, each approach leg and each retry - its own ramps and
    // the settling wait.
    // Speed and acceleration are in FULL steps (mechanics.h), the path in
    // microsteps: hence the MICROSTEPS. The path is counted at the BASE
    // ratio, not the learnt one: the cap travels to the driver
    // in the replies of `motor`, `direction` and `ratio`, and one that moved
    // by itself with every leg learnt would be a number the driver holds
    // stale. The learnt ratio stays within LEARN_CLAMP (15 %) of the base,
    // and CEILING_MARGIN (25 %) covers it.
    const float v = (float)m_speed * MICROSTEPS;
    const float a = (float)m_acceleration * MICROSTEPS;
    const float path = (m_direction == Direction::SHORTEST ? LONGEST_SHORTEST_DEG
                                                           : LONGEST_ONE_WAY_DEG)
                       * steps_per_degree(m_base_ratio);
    // below v*v/a pulses the move never reaches full speed: a triangle
    const float travel = (path <= v * v / a) ? 2.0f * sqrtf(path / a) : path / v + v / a;
    // every leg pays its ramps and the settling: the first, the approach
    // legs and the retries
    const float per_leg = (float)m_settle_ms / 1000.0f + v / a;
    const int legs = 1 + APPROACH_LEGS_MAX + m_max_retries;
    const float seconds = CEILING_MARGIN * (travel + legs * per_leg)
                          + CEILING_ALLOWANCE_S;
    return (uint32_t)lroundf(seconds * 1000.0f);
}

void Wheel::stop()
{
    m_mechanics.stop();
    m_motion = Motion::IDLE;
    release();
}

void Wheel::step()
{
    // A magnet that disappears is serious trouble and must be told when it
    // happens, not at the next question.
    if (m_mechanics.sensor_responds()) {
        // Once per loss, with hysteresis (MAGNET_REARM_MS, wheel.h): when a
        // single "seen" re-armed it, a flickering MD bit sent the event tens
        // of times a second.
        const bool seen = m_mechanics.magnet_seen();
        const uint32_t now = m_mechanics.milliseconds();
        if (!seen) {
            m_magnet_run = false;
            if (!m_magnet_lost) { m_magnet_lost = true; m_magnet_to_report = true; }
        } else {
            if (!m_magnet_run) { m_magnet_run = true; m_magnet_since = now; }
            if (m_magnet_lost && (uint32_t)(now - m_magnet_since) >= MAGNET_REARM_MS)
                m_magnet_lost = false;
        }
        // The angle is read live, always: at rest, after a failed move too -
        // a wheel turned by hand onto a slot after a failure must be SEEN
        // there, by `status` and by the LED alarm that it ends (an angle
        // frozen at the verdict's reading would hide it) - and WHILE MOVING.
        // A move that showed in `status` the angle of the last stop until
        // the next verdict gave a magnet sweep with points only at the five
        // slots, while the simulator, which interpolates, drew a continuous
        // curve. One
        // raw reading, not the 8-reading mean of the verdict: it is for
        // watching, and the verdict still reads its own mean after settling.
        // Reading the AS5600 in the loop does not disturb the motion: the
        // step pulses come from a peripheral of the ESP32 and the ramp from
        // FastAccelStepper's own task, not from loop(); an I2C read at
        // 400 kHz takes about 0.1 ms, and the same loop already reads the
        // magnet flag at every pass. The drift watch stays for IDLE only:
        // after "failed" the wheel is known to be off.
        m_angle = m_mechanics.angle();
        if (m_motion == Motion::IDLE) watch_drift();
        // a leg during which the magnet was lost teaches no ratio (judge())
        if (!seen && (m_motion == Motion::MOVING || m_motion == Motion::SETTLING))
            m_leg_magnet_ok = false;
    } else if (m_motion == Motion::MOVING || m_motion == Motion::SETTLING) {
        m_leg_magnet_ok = false;
    }

    if (m_motion == Motion::MOVING) {
        if (!m_mechanics.is_moving()) {
            m_motion = Motion::SETTLING;
            m_settle_end = m_mechanics.milliseconds() + m_settle_ms;
        }
    } else if (m_motion == Motion::SETTLING) {
        if ((int32_t)(m_mechanics.milliseconds() - m_settle_end) >= 0) {
            m_angle = average_reading();
            judge();
        }
    }
}

void Wheel::judge()
{
    // The verdict is given by the firmware, not by the driver: that way the
    // wheel behaves the same way even when driven by hand from a serial
    // monitor, and there are no two copies of the same logic that can diverge.
    const float deviation = fabsf(residual_error());
    const bool timed_out =
        (uint32_t)(m_mechanics.milliseconds() - m_move_start) > ceiling_ms();

    // What the leg did, the way it turned. Measured as the distance still to
    // go that way: if it shrank, the leg moved towards the target; if it
    // grew, the disc either passed the target (and the distance wrapped to
    // nearly a turn) or went back - whichever of the two is the smaller
    // movement is what happened. It needs no guess on how far a leg of N
    // steps goes, which is exactly the number that is not known.
    const float left = normalize((float)m_leg_sign * (m_target - m_angle));
    float moved;
    bool past = false;
    if (left <= m_leg_distance) {
        moved = m_leg_distance - left;
    } else if (360.0f - left < left - m_leg_distance) {
        past = true;
        moved = m_leg_distance + (360.0f - left);
    } else {
        moved = m_leg_distance - left;          // negative: it went back
    }
    const float sent = fabsf(m_leg_commanded);
    const bool progressed = m_leg_aim > 0.0f && moved > NO_PROGRESS_SHARE * m_leg_aim;
    const bool short_leg = m_leg_aim > 0.0f && sent < SHORT_LEG_DEG;
    const float lost_before = m_lost;
    if (short_leg && progressed) m_lost_known = true;
    if (short_leg) {
        // a short leg says the lost motion: what it was sent minus what the
        // disc did
        const float step = fminf(LOST_STEP_DEG, 0.5f * m_good_tolerance);
        float lost = progressed ? sent - moved : sent + step;
        if (!progressed && lost < m_lost + step) lost = m_lost + step;
        m_lost = lost < 0.0f ? 0.0f : (lost > LOST_MAX_DEG ? LOST_MAX_DEG : lost);
    }
    // A short leg that did not move, while the lost motion can still grow,
    // is the play being taken up, not a stall.
    const bool taking_up_play = short_leg && !progressed && lost_before < LOST_MAX_DEG;
    // A STALL: a leg that wanted to move and did not, and not because of the
    // play. The next leg, whatever it is, gets the boost.
    m_boost_next = m_leg_aim > 0.0f && !progressed && !past && !taking_up_play;

    // THE RATIO, learnt from this leg if it qualifies (LEARN_MIN_DEG and the
    // guards above it). The leg sent (aim + play) degrees at the ratio it
    // used; the play is swallowed, so the aim is what should have come out:
    // the disc's degrees per estimated degree are moved / aim, and the ratio
    // that would have made them 1 is the leg's ratio times aim / moved.
    const bool long_leg = m_leg_aim >= LEARN_MIN_DEG;
    bool learnt = false;
    if (m_learn && long_leg && !m_jogging && m_leg_kind == LegKind::FIRST
        && m_lost_known && m_leg_magnet_ok && progressed && moved > 0.0f) {
        const float seen = m_leg_ratio * m_leg_aim / moved;
        if (fabsf(seen / m_leg_ratio - 1.0f) <= LEARN_OUTLIER) {
            float r = m_ratio + LEARN_WEIGHT * (seen - m_ratio);
            const float lo = m_base_ratio * (1.0f - LEARN_CLAMP);
            const float hi = m_base_ratio * (1.0f + LEARN_CLAMP);
            r = r < lo ? lo : (r > hi ? hi : r);
            // the play is the drive's, a number of STEPS: kept in steps
            m_lost *= m_ratio / r;
            m_ratio = r;
            m_learnt++;
            learnt = true;
        }
    }
    m_leg_report.n = m_legs;
    m_leg_report.kind = m_leg_kind;
    m_leg_report.jog = m_jogging;
    m_leg_report.steps = m_leg_steps;
    m_leg_report.ratio = m_leg_ratio;
    m_leg_report.aim = m_leg_aim;
    m_leg_report.from = m_leg_from;
    m_leg_report.to = m_angle;
    m_leg_report.moved = moved;
    m_leg_report.long_leg = long_leg;
    m_leg_report.learnt = learnt;
    m_leg_report_ready = true;

    // how far a jog has gone, the way it was asked, from where it started:
    // a little backwards reads negative, an overshoot of a half-turn jog
    // still positive (see JOG_MOVED_SHARE)
    bool jog_went = true;
    if (m_jogging) {
        float along = normalize((m_jog_degrees < 0.0f ? -1.0f : 1.0f) * (m_angle - m_jog_from));
        if (along > 270.0f) along -= 360.0f;
        jog_went = along >= JOG_MOVED_SHARE * fabsf(m_jog_degrees);
    }

    if (deviation <= m_good_now) {
        m_motion = Motion::IDLE;
        m_outcome = Outcome::ARRIVED;
    } else if ((progressed || taking_up_play) && !past
               && m_approach_legs < APPROACH_LEGS_MAX && !timed_out) {
        // Short of the target and getting there: another approach leg, which
        // is the method and not a failure, so it does not use up a retry.
        // Also inside the warning band: going on costs a
        // fraction of a second, stopping would leave the error the next
        // exposure sees.
        m_approach_legs++;
        m_leg_kind = LegKind::APPROACH;
        start_leg();
        return;
    } else if (deviation <= m_warn_tolerance && jog_went) {
        // Outside the good tolerance but inside the alarm one: it is reported
        // and we go on. Never a failure here: a recoverable warning that
        // stopped the night would be worse than the problem it reports.
        // Not for a jog that did not go (JOG_MOVED_SHARE): it retries.
        m_motion = Motion::IDLE;
        m_outcome = Outcome::WARNING;
    } else if (m_retries < m_max_retries && !timed_out) {
        // A RETRY: the leg made no progress (a stall, the clutch slipping) or
        // went past the target - one way, the next leg goes round the turn.
        m_retries++;
        m_leg_kind = LegKind::RETRY;
        start_leg();
        return;
    } else {
        m_motion = Motion::FAILED;
        m_outcome = Outcome::FAILED;
    }

    release();
    m_event_ready = true;
    m_event_outcome = m_outcome;
    m_event_slot = m_wanted_slot;
    m_event_deviation = deviation;
    m_event_attempts = m_retries;
}

void Wheel::watch_drift()
{
    // No watching before the first positioning: until someone has asked for a
    // slot there is no target to drift from, and the residual error would be
    // the distance from a number that means nothing.
    if (m_outcome == Outcome::NONE) return;

    const float deviation = residual_error();
    const float amount = deviation < 0 ? -deviation : deviation;

    if (amount > m_warn_tolerance) {
        // Once per episode. The value is updated anyway, so what is sent is the
        // one from the moment it went out.
        if (!m_drift_out) {
            m_drift_out = true;
            m_drift_to_report = true;
            m_drift_deviation = deviation;
        }
    } else {
        // Back in: it re-arms. A wheel oscillating around the threshold would
        // report at every crossing, and rightly so: they are distinct episodes,
        // and whoever reads the log must see that it goes on.
        m_drift_out = false;
    }
}

bool Wheel::drift_to_report(float &deviation)
{
    if (!m_drift_to_report) return false;
    m_drift_to_report = false;
    deviation = m_drift_deviation;
    return true;
}

bool Wheel::event_to_send(Outcome &which, int &slot, float &deviation, int &attempts)
{
    if (!m_event_ready) return false;
    m_event_ready = false;
    which = m_event_outcome;
    slot = m_event_slot;
    deviation = m_event_deviation;
    attempts = m_event_attempts;
    return true;
}

bool Wheel::sensor_to_report()
{
    if (!m_magnet_to_report) return false;
    m_magnet_to_report = false;
    return true;
}

int Wheel::current_slot() const
{
    // During a move a valid slot is never reported: it would be a lie while
    // passing in front of the slots, and the Alpaca bridge must be able to
    // translate it into the -1 that ASCOM demands.
    if (m_motion == Motion::MOVING || m_motion == Motion::SETTLING) return 0;
    for (int i = 0; i < m_slots; i++) {
        if (fabsf(difference(m_angle, m_angles[i])) <= m_warn_tolerance) return i + 1;
    }
    return 0;
}

bool Wheel::set_angle(int slot, float degrees, Error &error)
{
    // the order of teach: range, motion. No sensor needed: it is a number.
    if (slot < 1 || slot > m_slots) { error = ERR_OUT_OF_RANGE; return false; }
    if (!(degrees >= 0.0f && degrees <= (float)ANGLE_MAX_DEG)) { error = ERR_OUT_OF_RANGE; return false; }
    if (m_motion == Motion::MOVING || m_motion == Motion::SETTLING) { error = ERR_NOT_NOW; return false; }

    // It does NOT move the wheel, unlike the trim it replaced:
    // the driver decides - one angle changed, it sends `go`; several, it
    // does not move - and a serial monitor sends `go` by hand. The target of
    // the positioning already done is left as it is, so the drift watch keeps
    // measuring from where the wheel was sent, not from a number it was
    // never asked to reach.
    m_angles[slot - 1] = normalize(degrees);
    return true;
}

bool Wheel::set_name(int slot, const char *text, Error &error, NameCheck &reason)
{
    if (slot < 1 || slot > m_slots) { error = ERR_OUT_OF_RANGE; return false; }

    reason = check_filter_name(text);
    if (reason != NAME_OK) { error = ERR_BAD_FILTER_NAME; return false; }

    // Unique even ignoring upper and lower case: two slots that collapse into
    // the same folder on Windows are a silent disaster.
    for (int i = 0; i < m_slots; i++) {
        if (i == slot - 1) continue;
        if (name_equal_nocase(m_names[i], text)) {
            error = ERR_BAD_FILTER_NAME;
            reason = NAME_OK;          // it is not the name that is wrong
            return false;
        }
    }
    snprintf(m_names[slot - 1], sizeof(m_names[slot - 1]), "%s", text);
    return true;
}

bool Wheel::reteach(int slot, Error &error)
{
    if (slot < 1 || slot > m_slots) { error = ERR_OUT_OF_RANGE; return false; }
    if (m_motion == Motion::MOVING || m_motion == Motion::SETTLING) { error = ERR_NOT_NOW; return false; }
    if (!m_mechanics.sensor_responds()) { error = ERR_SENSOR_SILENT; return false; }
    if (!m_mechanics.magnet_seen())    { error = ERR_NO_MAGNET;     return false; }

    m_angle = average_reading();
    m_angles[slot - 1] = m_angle;
    m_target = m_angle;
    return true;
}

bool Wheel::save(Error &error)
{
    // Saving is an explicit gesture: one experiments as much as one likes in
    // volatile memory and writes only when happy. If something goes wrong,
    // restarting the wheel is enough to find the good calibration again.
    bool ok = m_storage.store("slots", (float)m_slots);
    char k[8];
    for (int i = 0; i < m_slots; i++) {
        key(k, sizeof(k), 'a', i);
        ok = m_storage.store(k, m_angles[i]) && ok;
        key(k, sizeof(k), 'n', i);
        ok = m_storage.store(k, m_names[i]) && ok;
    }
    ok = m_storage.store("tol_good", m_good_tolerance) && ok;
    ok = m_storage.store("tol_warn", m_warn_tolerance) && ok;
    ok = m_storage.store("retries", (float)m_max_retries) && ok;
    ok = m_storage.store("run_ma", (float)m_run_current) && ok;
    ok = m_storage.store("hold_ma", (float)m_hold_current) && ok;
    ok = m_storage.store("settle_ms", (float)m_settle_ms) && ok;
    ok = m_storage.store("speed", (float)m_speed) && ok;
    ok = m_storage.store("accel", (float)m_acceleration) && ok;
    ok = m_storage.store("direction", (float)(int)m_direction) && ok;
    ok = m_storage.store("led_mode", (float)(int)m_led_mode) && ok;
    // The ratio IN USE is saved, the learnt refinement included, and becomes
    // the base the learning is kept around. Only here, never by itself:
    // saving is the explicit gesture for everything else too, and a value
    // that wrote itself to flash would change what the wheel does after a
    // restart without anyone having asked (firmware.md, "The drive ratio").
    ok = m_storage.store("ratio", m_ratio) && ok;
    ok = m_storage.store("ratio_learn", m_learn ? 1.0f : 0.0f) && ok;
    ok = m_storage.commit() && ok;

    if (!ok) { error = ERR_NVS_WRITE; return false; }
    m_base_ratio = m_ratio;
    m_learnt = 0;
    return true;
}

bool Wheel::set_tolerances(float good, float warn, int retries, Error &error)
{
    if (!(good > 0.0f && good <= warn && warn <= (float)TOLERANCE_MAX_DEG) ||
        retries < 0 || retries > RETRIES_MAX) {
        error = ERR_OUT_OF_RANGE;
        return false;
    }
    m_good_tolerance = good;
    m_warn_tolerance = warn;
    m_max_retries = retries;
    return true;
}

bool Wheel::set_run_current(uint16_t ma, Error &error)
{
    if (ma == 0 || ma > MOTOR_MA_MAX) { error = ERR_OUT_OF_RANGE; return false; }
    m_run_current = ma;
    if (m_hold_current > m_run_current) m_hold_current = m_run_current;
    apply_currents();
    return true;
}

// Speed and acceleration of the moves, applied at once and kept by "save"
// like the rest (they were already read back from NVS at start, but nothing
// could set them, and the panel's fields went nowhere).
bool Wheel::set_speed(uint32_t steps_per_second, uint32_t acceleration, Error &error)
{
    if (steps_per_second == 0 || steps_per_second > MOTOR_SPEED_MAX
        || acceleration == 0 || acceleration > MOTOR_ACCEL_MAX) {
        error = ERR_OUT_OF_RANGE;
        return false;
    }
    m_speed = steps_per_second;
    m_acceleration = acceleration;
    m_mechanics.speed(m_speed, m_acceleration);
    return true;
}

bool Wheel::set_ratio(float ratio, Error &error)
{
    // Refused while moving, like `teach` and `angle`: the leg under way was
    // computed with the old ratio, and learning from it would mix the two.
    if (!(ratio >= DRIVE_RATIO_MIN && ratio <= DRIVE_RATIO_MAX)) {
        error = ERR_OUT_OF_RANGE;
        return false;
    }
    if (m_motion == Motion::MOVING || m_motion == Motion::SETTLING) {
        error = ERR_NOT_NOW;
        return false;
    }
    m_lost *= m_ratio / ratio;         // the play, kept in steps
    m_base_ratio = ratio;
    m_ratio = ratio;
    m_learnt = 0;
    return true;
}

void Wheel::set_learning(bool on)
{
    // Off means the base alone, as a wheel with no learning would run: the
    // refinement is dropped, not frozen, so that "off" is one known number.
    m_learn = on;
    if (!on && m_ratio != m_base_ratio) {
        m_lost *= m_ratio / m_base_ratio;
        m_ratio = m_base_ratio;
        m_learnt = 0;
    }
}

bool Wheel::leg_to_report(LegReport &report)
{
    if (!m_leg_report_ready) return false;
    m_leg_report_ready = false;
    report = m_leg_report;
    return true;
}

bool Wheel::set_hold_current(uint16_t ma, Error &error)
{
    if (ma > m_run_current) { error = ERR_OUT_OF_RANGE; return false; }
    m_hold_current = ma;
    apply_currents();
    // at rest - idle or after a failure - it applies at once; during a
    // positioning, at its release
    if (!m_positioning) release();
    return true;
}

bool Wheel::set_settle_ms(uint32_t ms, Error &error)
{
    // Allowed while moving, like the hold: the wait under way keeps the end
    // it was given, the next leg takes the new one.
    if (ms > SETTLE_MS_MAX) { error = ERR_OUT_OF_RANGE; return false; }
    m_settle_ms = ms;
    return true;
}

}  // namespace wheelly
