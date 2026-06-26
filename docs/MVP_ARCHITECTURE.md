# WH AI Sales Assistant – MVP Architecture

## Project Goal

Build a universal AI Construction Agent that can operate commercial window software in the same way as an experienced salesperson.

The agent does **not** replace the salesperson.

The salesperson makes business decisions.

The agent performs repetitive work.

---

# Responsibilities

## Salesperson

* receives customer inquiry
* talks to customer
* chooses customer
* creates new offer
* selects offer preferences
* opens construction configurator
* verifies final offer
* generates PDF
* sends offer

---

## Agent

* reads customer materials
* reads salesperson instructions
* builds construction plan
* learns current GUI layout
* creates construction inside configurator
* accepts standard valuation
* creates next position
* finishes mission

---

# Universal Architecture

Customer Materials

↓

Construction Planner

↓

Construction Mission

↓

Mission Executor

↓

Program Adapter

↓

Vision Discovery

↓

GUI Mapper

↓

Commercial Software

---

# Design Rules

1. The salesperson always has higher priority than AI.

2. The agent never blocks the process because of missing information.

3. Unknown elements become assumptions or empty positions.

4. The agent never relies on fixed screen coordinates.

5. Every program is learned dynamically.

6. WH is only the first supported adapter.

7. Every sprint must end with a working demo.

---

# MVP Scope

The first MVP starts after the salesperson opens the construction configurator.

Everything before that remains under salesperson control.

The first responsibility of the agent is creating construction positions.

Nothing more.
