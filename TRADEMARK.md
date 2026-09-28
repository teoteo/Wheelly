<!--
SPDX-FileCopyrightText: 2026 Matteo Beretta
SPDX-License-Identifier: CC-BY-4.0
-->

# The Wheelly name and logo

**The design is open. The name is not.** Everything in this repository — the
firmware, the INDI driver, the CAD, the documentation — is released under
permissive licences, and you may build, modify, sell and redistribute it. See
[`LICENSING.md`](LICENSING.md).

What those licences do not give away is the **name "Wheelly" and the logo**.
That is deliberate, and it is the usual arrangement for open hardware: the
licences say what you may do with the *work*, the trademark says who the *maker*
is. MIT, CC-BY-4.0 and CERN-OHL-P-2.0 all leave trademarks out on purpose — none
of them grants any right in a name or a mark.

The point is not to restrict you. It is so that someone who buys, downloads or
reads about a "Wheelly" knows whose machine it is, and who to blame if it does
not work.

## You do not need to ask

- Say that your machine **is** a Wheelly, if you built it from this project
  without changing the design.
- Say that something is **based on**, **derived from**, **compatible with** or
  **works with** Wheelly. Plain, truthful statements of fact are always fine.
- Use the name to write about the project, review it, teach with it, link to it,
  or publish photographs of your own build.
- Redistribute this repository, unmodified, under its own name.

## Please ask first

- Naming a **modified** version Wheelly — a fork with a changed design, a
  changed protocol, or changed firmware.
- Using the name or the logo on a **product you sell**, or in the name of your
  company, project, shop, app, domain or social account.
- Using the logo as your own, or a logo confusingly close to it.
- Anything that suggests this project **endorses** you, or that you speak for it.

## If you fork it, rename it

The rule above is meaningless unless renaming is easy, so it was made easy. The
name reaches the user in one place only — the INDI driver — and it comes from a
build variable:

```sh
cmake -S driver/indi-wheelly -B build -DWHEELLY_DEVICE_NAME="Your Name"
```

That one flag changes the device name Ekos shows, the label in INDI's driver
list and the manufacturer field. The firmware does not announce the name at all.
Everything else that says "wheelly" in the sources is an identifier — file
names, include guards, namespaces — and those you may keep or rename as you
like: nobody sees them.

## Status

The marks are **not registered** at the time of writing, and no registration is
promised. Under Italian and EU law an unregistered mark still enjoys protection
where it is actually used, but a registration would be stronger; the project
will say so here if that changes.

## Getting in touch

Ask by opening an issue on the project's repository. Permission, when given, is
given in writing.
