// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

#ifdef ARDUINO

#include "storage_esp32.h"

#include <string.h>

namespace wheelly {

namespace {
const char *NAMESPACE = "wheelly";   // the NVS namespace: never change it, it holds the calibration of wheels already set up
}

bool StorageEsp32::begin()
{
    m_open = m_nvs.begin(NAMESPACE, false);
    return m_open;
}

bool StorageEsp32::load(const char *key, float &value)
{
    if (!m_open || !m_nvs.isKey(key)) return false;
    value = m_nvs.getFloat(key, 0.0f);
    return true;
}

bool StorageEsp32::load(const char *key, const char *&value)
{
    if (!m_open || !m_nvs.isKey(key)) return false;
    const size_t count = m_nvs.getString(key, m_last_text,
                                          sizeof(m_last_text));
    if (count == 0) return false;
    m_last_text[sizeof(m_last_text) - 1] = '\0';
    value = m_last_text;
    return true;
}

bool StorageEsp32::store(const char *key, float value)
{
    if (!m_open) return false;
    return m_nvs.putFloat(key, value) > 0;
}

bool StorageEsp32::store(const char *key, const char *value)
{
    if (!m_open) return false;
    return m_nvs.putString(key, value) > 0;
}

bool StorageEsp32::erase(const char *key)
{
    if (!m_open) return false;
    // Preferences::remove() is false for a key that is not there: that is
    // not a failure here, the key is gone either way
    if (!m_nvs.isKey(key)) return true;
    return m_nvs.remove(key);
}

bool StorageEsp32::commit()
{
    // Preferences write immediately: there is no separate commit to give.
    // The method stays in the interface because a different storage - an
    // external EEPROM, say - might need it, and the test bench uses it to make
    // the save fail on demand.
    return m_open;
}

}  // namespace wheelly

#endif  // ARDUINO
