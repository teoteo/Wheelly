// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// Automatic tests on wheelly_protocol.h, the file shared by firmware and
// driver. No hardware, no Arduino, no INDI needed: it compiles and runs
// wherever there is a C++ compiler.
//
//     cd firmware/test && ./test_protocol.sh
//
// What we want to verify, in order of importance:
//
//   1. The filter naming rule accepts what it must accept and rejects what it
//      must reject. It is the rule that protects the FITS headers and the file
//      names, and getting it wrong is paid for six months later, when stacking
//      no longer pairs lights and flats.
//   2. The sanitising INVARIANT: whatever junk goes in, what comes out passes
//      validation. The rest of the code relies on it.
//   3. That the protocol constants are consistent with each other and have
//      not been duplicated by a copy-paste slip.

// <limits.h> is included BEFORE the protocol, on purpose: it is the proof that
// none of our constants is named like a system macro. The preprocessor knows
// no namespaces, and a constant called LINE_MAX - as one really was, in a first
// draft - clashes with the one <limits.h> defines. On the Mac nobody noticed;
// compiling for the XIAO, where Arduino.h pulls in <limits.h> by itself, the
// build failed with a message that did not even name the clash. If someone
// brings back a name like that, from here on this file no longer compiles and
// it is found at once.
#include <limits.h>

#include "../wheelly/wheelly_protocol.h"

#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

using namespace wheelly;

static int failed = 0;
static int passed = 0;

static void ok(bool cond, const char *what, const std::string &detail = "")
{
    if (cond) {
        passed++;
    } else {
        failed++;
        std::printf("  FAILED: %s%s%s\n", what,
                    detail.empty() ? "" : " -> ", detail.c_str());
    }
}

static const char *result_name(NameCheck e)
{
    switch (e) {
        case NAME_OK:       return "OK";
        case NAME_EMPTY:    return "EMPTY";
        case NAME_TOO_LONG: return "TOO_LONG";
        case NAME_BAD_EDGE: return "BAD_EDGE";
        case NAME_BAD_CHAR: return "BAD_CHAR";
        case NAME_RESERVED: return "RESERVED";
    }
    return "?";
}

// Makes a non-printable byte visible, for the error messages.
static std::string readable(const std::string &s)
{
    std::string r;
    for (unsigned char c : s) {
        if (c >= 0x20 && c < 0x7F) {
            r += (char)c;
        } else {
            char buf[8];
            std::snprintf(buf, sizeof(buf), "\\x%02X", c);
            r += buf;
        }
    }
    return r;
}

// ---------------------------------------------------------------------------

static void test_valid_names()
{
    std::printf("names that must be ACCEPTED\n");

    // INDI's default set: if our rule rejected one of them, we would be
    // stricter than the ecosystem we have to live in.
    const char *indi_default[] = {
        "Red", "Green", "Blue", "H_Alpha", "SII", "OIII", "LPR", "Luminance"
    };
    for (const char *n : indi_default) {
        ok(check_filter_name(n) == NAME_OK, "INDI default accepted",
           std::string(n) + " -> " + result_name(check_filter_name(n)));
    }

    // Real cases from amateur astronomers
    const char *real[] = {
        "Ha", "Lum", "L", "O-III", "L-eXtreme", "Ha_3nm", "7nm_Ha",
        "Baader_7nm", "1_25in", "R_Astrodon", "Clear", "Dark", "V", "B",
        "1.25", "Ha.3nm", "a", "Z9"
    };
    for (const char *n : real) {
        ok(check_filter_name(n) == NAME_OK, "real name accepted",
           std::string(n) + " -> " + result_name(check_filter_name(n)));
    }

    // Exactly at the length limit
    std::string at_limit(FILTER_NAME_MAX, 'A');
    ok(check_filter_name(at_limit.c_str()) == NAME_OK,
       "32 characters accepted");
}

static void test_invalid_names()
{
    std::printf("names that must be REJECTED\n");

    struct Case { const char *name; NameCheck expected; const char *why; };
    const Case cases[] = {
        { "",              NAME_EMPTY,    "empty" },
        { "H\xCE\xB1",     NAME_BAD_CHAR, "Ha with the Greek alpha in UTF-8" },
        { "Luminosit\xC3\xA0", NAME_BAD_CHAR, "accent" },
        { "Baader 7nm",    NAME_BAD_CHAR, "space" },
        { "1.25\"",        NAME_BAD_CHAR, "quotes, forbidden on Windows" },
        { "R (Astrodon)",  NAME_BAD_CHAR, "parentheses" },
        { "L/RGB",         NAME_BAD_CHAR, "slash: in Ekos it would be a folder" },
        { "L\\RGB",        NAME_BAD_CHAR, "backslash" },
        { "Ha:3nm",        NAME_BAD_CHAR, "colon" },
        { "Ha*",           NAME_BAD_CHAR, "asterisk" },
        { "Ha?",           NAME_BAD_CHAR, "question mark" },
        { "Ha|L",          NAME_BAD_CHAR, "vertical bar" },
        { "Ha<L",          NAME_BAD_CHAR, "less-than" },
        { "Ha=1",          NAME_BAD_CHAR, "equals: would break key=value" },
        { "Ha\tL",         NAME_BAD_CHAR, "tab" },
        { "Ha\nL",         NAME_BAD_CHAR, "newline: would break the protocol" },
        { "-Ha",           NAME_BAD_EDGE, "leading dash: looks like an option" },
        { ".Ha",           NAME_BAD_EDGE, "leading dot: hidden file on Unix" },
        { "_Ha",           NAME_BAD_EDGE, "leading underscore" },
        { "Ha-",           NAME_BAD_EDGE, "trailing dash" },
        { "Ha.",           NAME_BAD_EDGE, "trailing dot: forbidden by Microsoft" },
        { "Ha_",           NAME_BAD_EDGE, "trailing underscore" },
        { "NUL",           NAME_RESERVED, "Windows device" },
        { "nul",           NAME_RESERVED, "same, lower case" },
        { "CON",           NAME_RESERVED, "Windows device" },
        { "Aux",           NAME_RESERVED, "same, mixed case" },
        { "PRN",           NAME_RESERVED, "Windows device" },
        { "COM1",          NAME_RESERVED, "serial port" },
        { "com9",          NAME_RESERVED, "serial port" },
        { "LPT1",          NAME_RESERVED, "parallel port" },
        { "lpt9",          NAME_RESERVED, "parallel port" },
        { "nul.fits",      NAME_RESERVED, "reserved even with the extension" },
    };

    for (const Case &c : cases) {
        NameCheck result = check_filter_name(c.name);
        ok(result == c.expected, c.why,
           readable(c.name) + " -> expected " + result_name(c.expected) +
           ", got " + result_name(result));
    }

    // One character over the limit
    std::string too_long(FILTER_NAME_MAX + 1, 'A');
    ok(check_filter_name(too_long.c_str()) == NAME_TOO_LONG,
       "33 characters rejected");

    // Precedence among the reasons for rejection. Not pedantry: the reason ends
    // up in front of the user, and for a name that is both too long and full
    // of odd characters "too long" is the useful information. It is also the
    // point where this rule and its copy in the Python simulator had diverged,
    // giving two different reasons for the same name.
    ok(check_filter_name((" " + std::string(FILTER_NAME_MAX * 3, 'A')).c_str())
           == NAME_TOO_LONG,
       "too long takes precedence over a forbidden character");
    ok(check_filter_name((std::string(FILTER_NAME_MAX * 3, 'A') + "-").c_str())
           == NAME_TOO_LONG,
       "too long takes precedence over a bad edge");
    ok(check_filter_name("-A B") == NAME_BAD_CHAR,
       "forbidden character takes precedence over a bad edge");

    // Every forbidden byte, one by one. Not pedantry: it is the guarantee that
    // no byte outside printable ASCII gets through, which is what the FITS
    // standard requires.
    int mismatches = 0;
    for (int b = 1; b < 256; b++) {
        char name[4] = { 'A', (char)b, 'B', '\0' };
        bool allowed = name_is_allowed((char)b);
        bool accepted = (check_filter_name(name) == NAME_OK);
        if (accepted != allowed) mismatches++;
    }
    ok(mismatches == 0, "all 255 bytes treated consistently",
       std::string("mismatched: ") + std::to_string(mismatches));

    // COM0 and LPT0 are NOT reserved: ports start at 1. Rejecting them would
    // make us stricter than Windows for no reason.
    ok(check_filter_name("COM0") == NAME_OK, "COM0 is not reserved");
    ok(check_filter_name("LPT0") == NAME_OK, "LPT0 is not reserved");
    ok(check_filter_name("CONE") == NAME_OK, "CONE is not CON");
    ok(check_filter_name("NULL") == NAME_OK, "NULL is not NUL");
}

static void test_sanitise_invariant()
{
    std::printf("INVARIANT: sanitising always produces a valid name\n");

    std::vector<std::string> inputs = {
        "", " ", "   ", "___", "---", "...", "_-.", "\t\n",
        "H\xCE\xB1", "Luminosit\xC3\xA0", "Baader 7nm", "1.25\"",
        "R (Astrodon)", "L/RGB", "L\\RGB", "Ha:3nm", "Ha=1", "Ha|L",
        "-Ha", ".Ha", "_Ha", "Ha-", "Ha.", "Ha_", "--Ha--",
        "NUL", "nul", "CON", "com1", "LPT9", "nul.fits", "NUL.FITS",
        "Ha", "O-III", "1.25", "Red",
        std::string(FILTER_NAME_MAX, 'A'),
        std::string(FILTER_NAME_MAX + 50, 'B'),
        std::string(FILTER_NAME_MAX + 50, ' '),
        "A" + std::string(FILTER_NAME_MAX + 50, '-') + "B",
        "\x01\x02\x03", "\x7F", "\xFF\xFE",
    };
    // and every single byte, to leave nothing uncovered
    for (int b = 1; b < 256; b++) inputs.push_back(std::string(1, (char)b));

    for (const std::string &in : inputs) {
        char out[FILTER_NAME_MAX + 1];
        sanitize_filter_name(in.c_str(), out, sizeof(out));
        NameCheck result = check_filter_name(out);
        ok(result == NAME_OK, "sanitised is valid",
           "\"" + readable(in) + "\" -> \"" + readable(out) + "\" (" +
           result_name(result) + ")");
    }

    // An already valid name must not be touched: if sanitising changed good
    // names, the user would see the filter renamed for no reason, and that is
    // exactly the silent damage we want to avoid.
    const char *already_good[] = { "Ha", "O-III", "1.25", "H_Alpha", "Luminance", "L-eXtreme" };
    for (const char *n : already_good) {
        char out[FILTER_NAME_MAX + 1];
        sanitize_filter_name(n, out, sizeof(out));
        ok(std::strcmp(n, out) == 0, "already valid name left untouched",
           std::string(n) + " -> " + out);
    }

    // Concrete examples, the ones quoted in firmware.md: if they change, the
    // document and the code have stopped telling the same story.
    struct Expected { const char *in; const char *out; };
    const Expected expected_list[] = {
        { "Baader 7nm",   "Baader_7nm" },
        { "R (Astrodon)", "R_Astrodon" },
        { "L/RGB",        "L_RGB" },
        { "1.25\"",       "1.25" },
        { "",             "Filter" },
        { "NUL",          "NUL0" },
    };
    for (const Expected &a : expected_list) {
        char out[FILTER_NAME_MAX + 1];
        sanitize_filter_name(a.in, out, sizeof(out));
        ok(std::strcmp(out, a.out) == 0, "sanitising as documented",
           std::string("\"") + readable(a.in) + "\" -> \"" + out +
           "\", expected \"" + a.out + "\"");
    }

    // Small buffer: nothing written past it, and the result stays valid.
    for (size_t dim = 2; dim <= 10; dim++) {
        char buf[64];
        std::memset(buf, '@', sizeof(buf));
        sanitize_filter_name("Baader 7nm Ha", buf, dim);
        ok(std::strlen(buf) < dim, "sanitising respects the buffer",
           "dim=" + std::to_string(dim) + " -> \"" + buf + "\"");
        ok(buf[dim] == '@', "no write past the buffer",
           "dim=" + std::to_string(dim));
        ok(check_filter_name(buf) == NAME_OK, "valid in a tight buffer too",
           "dim=" + std::to_string(dim) + " -> \"" + buf + "\"");
    }
}

static void test_uniqueness()
{
    std::printf("uniqueness of names across positions\n");

    const char *distinti[] = { "Lum", "Red", "Green", "Blue", "Ha" };
    ok(first_duplicate_name(distinti, 5) == -1, "five distinct names");

    // The case that matters: two names FITS considers different but that on
    // Windows and macOS end up in the same folder.
    const char *maiuscole[] = { "Ha", "Red", "ha", "Blue", "Lum" };
    ok(first_duplicate_name(maiuscole, 5) == 2,
       "Ha and ha recognised as the same name",
       "index found: " + std::to_string(first_duplicate_name(maiuscole, 5)));

    const char *identici[] = { "Lum", "Lum" };
    ok(first_duplicate_name(identici, 2) == 1, "exact duplicate found");

    const char *one[] = { "Lum" };
    ok(first_duplicate_name(one, 1) == -1, "a single name is not a duplicate");
}

static void test_constants()
{
    std::printf("consistency of the protocol constants\n");

    ok(PROTOCOL_VERSION >= 1, "sensible protocol version");
    ok(FACTORY_SLOTS == 5, "a factory wheel has five positions");
    ok(MAX_SLOTS >= FACTORY_SLOTS, "and the maximum is not below the default");
    ok(FILTER_NAME_MAX == 32, "filter name at most 32");

    // The longest line the firmware can produce is the names one:
    // "ok" + " nN=" plus the name, once per position. If the buffer cannot
    // hold it, the firmware truncates a reply and the driver reads a mangled
    // name. The worst case is a wheel with the maximum of positions, not
    // the reference wheel's: there is one firmware and it must cope with the largest one.
    size_t worst_names = 2 + MAX_SLOTS * (4 + FILTER_NAME_MAX);
    ok(WHEELLY_LINE_MAX > worst_names, "the line buffer holds the reply to 'names'",
       "needs " + std::to_string(worst_names) + ", is " +
       std::to_string(WHEELLY_LINE_MAX));

    // The clash between our names and system macros is not tested here: it is
    // tested at the top of the file, by including <limits.h> BEFORE the
    // protocol. If someone brought back a constant named like a macro, this
    // file would no longer compile. See the comment at the top.

    // No protocol word duplicated: a wrong copy-paste here would show up as a
    // command that runs another one.
    const char *words[] = {
        CMD_VERSION, CMD_STATUS, CMD_GO, CMD_STOP, CMD_ANGLES, CMD_ANGLE,
        CMD_JOG, CMD_NAMES, CMD_NAME, CMD_TEACH, CMD_SAVE,
        CMD_DIRECTION, CMD_TOLERANCE, CMD_MOTOR, CMD_HOLD, CMD_LED,
        CMD_DIAG, CMD_SLOTS
    };
    const size_t n_words = sizeof(words) / sizeof(words[0]);
    int dups = 0;
    for (size_t i = 0; i < n_words; i++)
        for (size_t j = i + 1; j < n_words; j++)
            if (std::strcmp(words[i], words[j]) == 0) dups++;
    ok(dups == 0, "no duplicated command",
       "duplicates: " + std::to_string(dups));

    // Every command must be made only of characters a human can type without
    // thinking, and must not start like a reply line.
    for (size_t i = 0; i < n_words; i++) {
        bool clean = words[i][0] != '\0';
        for (const char *p = words[i]; *p; p++)
            if (!((*p >= 'a' && *p <= 'z') || *p == '-')) clean = false;
        ok(clean, "command in lower case and dashes", words[i]);
    }

    const char *events[] = { EV_ARRIVED, EV_WARNING, EV_FAILED, EV_SENSOR };
    int dup_events = 0;
    for (int i = 0; i < 4; i++)
        for (int j = i + 1; j < 4; j++)
            if (std::strcmp(events[i], events[j]) == 0) dup_events++;
    ok(dup_events == 0, "no duplicated event");

    // The line prefixes must stay distinguishable by their first character:
    // that is how the driver decides it has finished reading.
    ok(PREFIX_OK[0] != PREFIX_ERROR[0], "ok and error are told apart at once");
    ok(PREFIX_COMMENT != PREFIX_EVENT, "comment and event are told apart");
    ok(PREFIX_OK[0] != PREFIX_COMMENT && PREFIX_OK[0] != PREFIX_EVENT,
       "ok is not confused with comment or event");
    ok(PREFIX_ERROR[0] != PREFIX_COMMENT && PREFIX_ERROR[0] != PREFIX_EVENT,
       "error is not confused with comment or event");

    // A valid filter name can never start like a special line, otherwise a
    // name could end up looking like an event.
    char first[2] = { PREFIX_COMMENT, '\0' };
    ok(check_filter_name(first) != NAME_OK, "a name cannot start with #");
    first[0] = PREFIX_EVENT;
    ok(check_filter_name(first) != NAME_OK, "a name cannot start with !");

    // The error codes are translation keys: they must be distinct and
    // non-zero, which means "no error".
    const int codes[] = {
        ERR_UNKNOWN_COMMAND, ERR_BAD_ARGUMENTS, ERR_OUT_OF_RANGE,
        ERR_SENSOR_SILENT, ERR_NO_MAGNET, ERR_DRIVER_SILENT,
        ERR_NOT_NOW, ERR_NVS_WRITE, ERR_BAD_FILTER_NAME
    };
    const size_t n_codes = sizeof(codes) / sizeof(codes[0]);
    int dup_codes = 0;
    for (size_t i = 0; i < n_codes; i++) {
        if (codes[i] == ERR_NONE) dup_codes++;
        for (size_t j = i + 1; j < n_codes; j++)
            if (codes[i] == codes[j]) dup_codes++;
    }
    ok(dup_codes == 0, "error codes distinct and non-zero");
}

// ---------------------------------------------------------------------------

int main()
{
    std::printf("\nTests on wheelly_protocol.h\n");
    std::printf("===========================\n\n");

    test_valid_names();
    test_invalid_names();
    test_sanitise_invariant();
    test_uniqueness();
    test_constants();

    std::printf("\n---------------------------\n");
    std::printf("%d passed, %d failed\n\n", passed, failed);
    return failed == 0 ? 0 : 1;
}
