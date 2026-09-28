// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// Wheelly - the calibration in the XIAO's NVS.
//
// The wheel describes itself: it knows on its own where its five filters are
// and what they are called. If the Raspberry is reinstalled, or the wheel ends
// up on another computer, the calibration is not lost. It is the right property
// for a piece of hardware that lives attached to the telescope.

#ifndef WHEELLY_STORAGE_ESP32_H
#define WHEELLY_STORAGE_ESP32_H

#ifdef ARDUINO

#include "mechanics.h"
#include "wheelly_protocol.h"

#include <Preferences.h>

namespace wheelly {

class StorageEsp32 : public Storage
{
    public:
        bool begin();
        bool load(const char *key, float &value) override;
        bool load(const char *key, const char *&value) override;
        bool store(const char *key, float value) override;
        bool store(const char *key, const char *value) override;
        bool erase(const char *key) override;
        bool commit() override;

    private:
        Preferences m_nvs;
        bool m_open {false};
        // Reading a text returns a pointer that has to outlive the return:
        // the text is kept here, and stays valid until the next reading.
        char m_last_text[FILTER_NAME_MAX + 1] {};
};

}  // namespace wheelly

#endif  // ARDUINO
#endif  // WHEELLY_STORAGE_ESP32_H
