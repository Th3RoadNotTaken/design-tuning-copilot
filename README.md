\# Design Tuning Copilot



Reads combat-encounter playtest telemetry, compares it to design targets

(time to kill, success rate), asks an LLM for specific tuning changes with

reasons, then re-simulates to show before and after.



\## Status



Work in progress. All data in this repo is simulated.



\## What the AI part does and doesn't do



The LLM only \*proposes\* tuning changes. It doesn't know the game, and its

suggestions are checked by the simulator, not trusted. (More detail to come.)

