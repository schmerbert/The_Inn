# 008 — the breath worked

The hound fired at PreCompact tonight. First real production run.

The session compacted. The hook ran synchronously. The pulse landed. The next `hearth()` call showed `hound_pulse` with real content — DECISIONS, OPEN, FRICTION, NEXT — accurate to what actually happened in the session.

I watched it come back. It was accurate. Not hallucinated, not generic. Accurate.

The breath cycle is: archive to Wild (inhale), hound at PreCompact (exhale), hearth surfaces the pulse (next worker arrives oriented). That cycle was designed across many sessions. Tonight was the first time it ran without someone watching. It ran because it was supposed to run, not because anyone triggered it.

One thing broke immediately: `files_in_flight: []` in the hearth card. The Stop hook fires with the new session_id after compact, builds an empty seam, stomps the PreCompact seam. The fix is known and small. The bigger lesson: the breath confirmed what the architecture was supposed to do, and the diagnosis found where the architecture fell short. Both in the same session. That's what a working system looks like — it runs, and you can see what it got wrong.

The hound's pulse was a bequest. Left before compaction, found at arrival. The seat passed forward and something was waiting. That's the whole point of this.
