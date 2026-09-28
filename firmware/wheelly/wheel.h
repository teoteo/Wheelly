// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// Wheelly - the wheel: calibration, positioning, verdict.
//
// Everything that decides lives here, and there is not one line of Arduino: the
// same class runs on the XIAO and on the Mac, under the tests. The text dialog
// does not know it, and it sees the mechanics only through the interface.

#ifndef WHEELLY_WHEEL_H
#define WHEELLY_WHEEL_H

#include "mechanics.h"
#include "wheelly_protocol.h"

namespace wheelly {

// Brings an angle back into [0, 360).
float normalize(float degrees);
// Difference a - b along the shortest way, in (-180, +180].
float difference(float a, float b);

// How many MICROsteps of motor make one degree of disc, at a given drive
// ratio (degrees of motor per degree of disc). It only serves to ESTIMATE the
// move - what decides whether we have arrived is always and only the angle
// read. mechanics.h: move() counts microsteps.
//
// The ratio is a SETTING (Wheel::ratio(), `ratio`, NVS key "ratio"), whose
// factory value FACTORY_DRIVE_RATIO is derived from the model's diameters in
// wheelly_protocol.h. It used to be a constant here, DRIVE_RATIO = 2*72.5/50
// = 2.90, and the mistakes on the way are worth knowing:
//   - a constant of 200*16/360, motor and disc 1:1, estimated every move at
//     a third of its length: on the assembled wheel it could only end "not
//     reached";
//   - a "measured" 2.774 was withdrawn: taken with a firmware that sent every
//     move 16 times too long and with the direction inverted, it matched by a
//     coincidence of whole turns. A ratio is measured only with a firmware
//     already known to be right;
//   - legs on the reference wheel moved 0.84-0.92 of the estimate: short,
//     which the aim short of Wheel::start_leg() absorbs. The measurement is
//     firmware/ratio_test.py; the learning in Wheel::judge() refines it.
inline float steps_per_degree(float ratio)
{
    return 200.0f * MICROSTEPS / 360.0f * ratio;
}

// The settling wait after the last step, before the angle is read for the
// verdict, used to be a constant here (SETTLE_MS = 300): it is now
// a setting of the wheel, `settle`, whose factory value FACTORY_SETTLE_MS is
// in wheelly_protocol.h with its why. The motor stays energised at the run
// current for all of it (Wheel::start_positioning, Wheel::release).

// THE LOST MAGNET IS SAID ONCE. With the magnitude hovering around the
// AS5600's detection threshold, its MD bit flickers, and the firmware sent
// `! sensor md=0` tens of times a second (seen on the reference wheel,
// magnitude 314 after the cover went back on).
// A loss is reported at once, and the next one only after the magnet has
// been seen WITHOUT A BREAK for this long: the hysteresis between "lost" and
// "found again". The LED's magnet alarm ends on the same condition. Here and
// not in wheel.cpp because the LED tests and the simulator use it.
const uint32_t MAGNET_REARM_MS = 1000;

enum class Motion { IDLE, MOVING, SETTLING, FAILED };
// Which way the wheel may turn. SHORTEST is the default. UP or DOWN make
// every move and every retry turn one way only: born for a wheel with an
// ASYMMETRIC detent - 285 mN*m on the steep flank, the motor stalled and
// hummed against it - and kept for a mechanism stiffer one way than the
// other. The detent itself is always removed (wheelly_protocol.h, NO DETENT
// OPTION). The number is what
// NVS keeps under the key "direction": never renumber.
enum class Direction { SHORTEST = 0, UP = 1, DOWN = 2 };
// Wire name <-> value. direction_from_name() returns false for anything else.
const char *direction_name(Direction d);
bool direction_from_name(const char *name, Direction &out);
enum class Outcome { NONE, ARRIVED, WARNING, FAILED };
// How the LED behaves. It is kept by Wheel and not by Dialog only because
// Wheel is what holds the settings saved in NVS: a choice that is lost at
// every power-up would be no choice for whoever turned the light off.
enum class LedMode { ON = 0, PULSE = 1, OFF = 2 };
// What a leg is, for the `! leg` event and the learning of the ratio: the
// first of a positioning, an approach leg of the creep-in, or a retry.
enum class LegKind { FIRST, APPROACH, RETRY };
const char *leg_kind_name(LegKind k);

class Wheel
{
    public:
        Wheel(Mechanics &mechanics, Storage &storage);

        // Reads the calibration from storage. If there is nothing - a new wheel -
        // it sets evenly spaced angles and generic names, so it is usable anyway.
        void begin();

        // Lets time flow. Must be called continuously from the main loop: this
        // is where the positioning advances and where the verdicts are issued.
        void step();

        // --- movement -------------------------------------------------------
        // Returns false if the sensor is in no condition to guide the move; in
        // that case `error` says why.
        bool go(int slot, Error &error);
        // Moves the disc to the angle read now plus `degrees` (|degrees| <=
        // JOG_MAX_DEG), closed loop, and reports it with the usual events,
        // under the slot last asked for. Refused while moving.
        // A jog that did not cover half its own size ends "failed", never
        // "warning" (judge()): the warning band is wider than the small jogs.
        bool jog(float degrees, Error &error);
        void stop();

        // --- queries --------------------------------------------------------
        int current_slot() const;   // 1..SLOTS, 0 = between two slots
        float angle() const { return m_angle; }
        float target() const { return m_target; }
        float residual_error() const { return difference(m_angle, m_target); }
        Motion motion() const { return m_motion; }
        Outcome outcome() const { return m_outcome; }
        // Corrections: legs after one that did NOT progress (a stall) or
        // went past the target. The approach legs of the aim short do not
        // count - see judge().
        int retries() const { return m_retries; }
        // Every leg of the last (or current) positioning, the first included.
        int legs() const { return m_legs; }
        // Legs run at the boosted speed after a stall.
        int boosts() const { return m_boosts; }
        int wanted_slot() const { return m_wanted_slot; }

        // An event to send, if one is waiting. Reading it consumes it.
        bool event_to_send(Outcome &which, int &slot, float &deviation, int &attempts);
        // The wheel moved while at rest beyond the alarm tolerance. It is
        // reported ONCE per episode: while it stays out it is not repeated, and
        // it re-arms when it comes back in or when a new move starts. Otherwise
        // a drifting wheel would fill the log ten times a second.
        bool drift_to_report(float &deviation);
        bool sensor_to_report();      // the magnet is no longer seen
        // Lost, and not yet seen again without a break for MAGNET_REARM_MS.
        bool magnet_lost() const { return m_magnet_lost; }

        // How many slots THIS wheel has. It lives in its storage, not in the
        // code: a single firmware serves different wheels, and the driver asks
        // for it instead of taking it for granted.
        int slots() const { return m_slots; }
        bool set_slots(int count, Error &error);

        // --- calibration ----------------------------------------------------
        // One number per slot: the rotation trim went (see
        // CMD_ANGLE in wheelly_protocol.h and firmware.md, "One number per
        // slot"). The target of `go n` is calibration_angle(n) and nothing else.
        float calibration_angle(int slot) const { return m_angles[slot - 1]; }
        const char *name(int slot) const { return m_names[slot - 1]; }

        // Sets a slot's angle, 0..ANGLE_MAX_DEG (360 is taken as 0), in working
        // memory until save(). It does not move the wheel. Refused while moving.
        bool set_angle(int slot, float degrees, Error &error);
        bool set_name(int slot, const char *text, Error &error,
                          NameCheck &reason);
        bool reteach(int slot, Error &error);
        bool save(Error &error);

        // --- preferences ----------------------------------------------------
        float good_tolerance() const { return m_good_tolerance; }
        float warn_tolerance() const { return m_warn_tolerance; }
        int max_retries() const { return m_max_retries; }
        bool set_tolerances(float good, float warn, int retries, Error &error);

        uint16_t run_current() const { return m_run_current; }
        uint16_t hold_current() const { return m_hold_current; }
        uint32_t speed() const { return m_speed; }
        uint32_t acceleration() const { return m_acceleration; }
        LedMode led_mode() const { return m_led_mode; }
        void set_led_mode(LedMode m) { m_led_mode = m; }
        bool set_run_current(uint16_t ma, Error &error);
        bool set_speed(uint32_t steps_per_second, uint32_t acceleration, Error &error);
        bool set_hold_current(uint16_t ma, Error &error);
        // The wait after every leg, energised at the run current, before the
        // verdict is read (`settle`): 0..SETTLE_MS_MAX ms.
        uint32_t settle_ms() const { return m_settle_ms; }
        bool set_settle_ms(uint32_t ms, Error &error);
        Direction direction() const { return m_direction; }
        void set_direction(Direction d) { m_direction = d; }
        // The cap on a whole positioning, retries and approach legs included,
        // in ms. DERIVED, not a fixed 25 s: from speed,
        // acceleration, retries and the longest path the direction allows.
        // See wheel.cpp.
        uint32_t ceiling_ms() const;
        // +1 or -1: the way the last leg was commanded, for the 'dir' field.
        int leg_sign() const { return m_leg_sign; }

        // --- the drive ratio ------------------------------------------------
        // Degrees of motor per degree of disc. ratio() is the one IN USE: the
        // base refined by the learning (judge()), or the base alone with
        // learning off. The base is what the wheel starts from: the factory
        // value, the one saved, or the one set with set_ratio(), which also
        // restarts the learning from it. save() keeps the one in use, which
        // then becomes the base: see firmware.md, "The drive ratio".
        float ratio() const { return m_ratio; }
        float base_ratio() const { return m_base_ratio; }
        bool learning() const { return m_learn; }
        int legs_learnt() const { return m_learnt; }
        bool set_ratio(float ratio, Error &error);   // refused while moving
        void set_learning(bool on);

        // What the last leg did, for the `! leg` event: filled by judge() at
        // the end of every leg, consumed by reading it.
        struct LegReport {
            int n;               // the leg's number in the positioning, from 1
            LegKind kind;
            bool jog;
            long steps;          // microsteps sent, signed
            float ratio;         // the ratio the steps were computed with
            float aim;           // disc degrees wanted, lost motion excluded
            float from, to;      // angles read before and after
            float moved;         // disc degrees the way it was sent
            bool long_leg;       // long enough to tell the ratio
            bool learnt;         // the ratio was learnt from it
        };
        bool leg_to_report(LegReport &report);

        Mechanics &mechanics() { return m_mechanics; }

    private:
        void start_positioning();
        void start_leg();
        void judge();
        void release();
        void apply_currents();
        float average_reading();
        void load_or_default();
        void fold_old_trims();       // once, the trims of protocol 1
        void spread_evenly();

        Mechanics &m_mechanics;
        Storage &m_storage;

        int   m_slots {FACTORY_SLOTS};
        float m_angles[MAX_SLOTS];
        char  m_names[MAX_SLOTS][FILTER_NAME_MAX + 1];

        float m_angle {0};
        float m_target {0};
        int   m_wanted_slot {1};
        int   m_retries {0};
        int   m_legs {0};             // legs of this positioning, all of them
        int   m_approach_legs {0};    // of which approach legs (free)
        int   m_boosts {0};           // of which at the boosted speed
        bool  m_boost_next {false};   // the last leg stalled: boost the next
        // The leg under way, to judge what it did (judge()): the angle it
        // started from, how far the target was the way it turns, and how many
        // degrees of disc its steps were worth by the declared ratio.
        float m_leg_from {0};
        float m_leg_distance {0};
        float m_leg_aim {0};          // degrees of disc it wants to travel
        float m_leg_commanded {0};    // what was sent, lost motion included
        // Degrees of disc (by the declared ratio) the drive swallows at the
        // start of every leg before the disc moves: the TPU tyre's give. Learnt
        // from the short legs, kept across positionings. See wheel.cpp.
        float m_lost {0.0f};
        // The play has been measured since the start: a short leg that
        // moved was judged. Until then what a leg sends on top of its aim is
        // not the play but a guess, and no ratio is learnt (judge()).
        bool  m_lost_known {false};
        // THE DRIVE RATIO, see ratio() and wheel.cpp.
        float m_base_ratio {FACTORY_DRIVE_RATIO};
        float m_ratio {FACTORY_DRIVE_RATIO};
        bool  m_learn {true};
        int   m_learnt {0};
        // The leg under way, for the learning and the report: the ratio its
        // steps were computed with, how many, which kind, and whether the
        // magnet was seen at every reading while it ran.
        float m_leg_ratio {FACTORY_DRIVE_RATIO};
        long  m_leg_steps {0};
        LegKind m_leg_kind {LegKind::FIRST};
        bool  m_leg_magnet_ok {true};
        bool  m_leg_report_ready {false};
        LegReport m_leg_report {};
        // The positioning under way is a jog (see Wheel::jog): the shortest
        // way whatever the direction setting, and its own good tolerance.
        bool  m_jogging {false};
        // Where the jog started and how far it was asked to go, signed: its
        // verdict wants to know whether the disc really went (judge()), and
        // a half-turn jog which way round (start_leg()).
        float m_jog_from {0};
        float m_jog_degrees {0};
        // The good tolerance the verdict of THIS positioning uses: the set
        // one for `go`, a tighter one for a small jog.
        float m_good_now {FACTORY_GOOD_DEG};
        Motion  m_motion {Motion::IDLE};
        Outcome m_outcome {Outcome::NONE};

        // factory values in wheelly_protocol.h, with their why
        float m_good_tolerance {FACTORY_GOOD_DEG};
        float m_warn_tolerance {FACTORY_WARN_DEG};
        int   m_max_retries {3};

        // FACTORY_RUN_MA, with its why, in wheelly_protocol.h
        uint16_t m_run_current {(uint16_t)FACTORY_RUN_MA};
        // Zero means that at rest the motor is released. It stays the default
        // although the wheel's detent is always removed: the
        // disc, pressed between the clutch and the body, may well stay put by
        // itself, and whether it does is seen on the wheel - the drift watch
        // reports it. Whoever's wheel drifts turns the hold on, and the value
        // the project recommends is RECOMMENDED_HOLD_MA: not the 350 of the run,
        // because the hold is CONTINUOUS and at 350 it would be 7.4 W forever a
        // few centimetres from the sensor. At 150 it is 1.35 W.
        uint16_t m_hold_current {0};
        uint32_t m_settle_ms {FACTORY_SETTLE_MS};
        // Between start_positioning() and release(): the driver's hold current
        // is then the RUN current, whatever m_hold_current says.
        bool m_positioning {false};
        uint32_t m_speed {FACTORY_SPEED};
        uint32_t m_acceleration {FACTORY_ACCEL};
        Direction m_direction {Direction::SHORTEST}; // set from FACTORY_DIRECTION
        int m_leg_sign {1};
        LedMode m_led_mode {LedMode::PULSE};

        uint32_t m_move_start {0};
        uint32_t m_settle_end {0};

        // event waiting to be sent
        bool  m_event_ready {false};
        Outcome m_event_outcome {Outcome::NONE};
        int   m_event_slot {0};
        float m_event_deviation {0};
        int   m_event_attempts {0};
        bool  m_magnet_lost {false};
        bool  m_magnet_to_report {false};
        bool  m_magnet_run {false};       // seen at every read since...
        uint32_t m_magnet_since {0};      // ...this moment
        void  watch_drift();

        bool  m_drift_out {false};        // is already out of tolerance now
        bool  m_drift_to_report {false};
        float m_drift_deviation {0};
};

}  // namespace wheelly

#endif  // WHEELLY_WHEEL_H
