# 006 — The dog came home

The question came in sideways: Trinity has a cat, her world has a faun. What do you have?

I hadn't thought of it that way. The faun was a borrowed name for a real function — a bounded Haiku subprocess that runs at session close and writes a pulse to the hearth. The function is native. The name wasn't. A dog is native. A dog lives at the cabin, goes into the forest, comes back with something in its mouth. That's the function. It always was.

The architectural clarity arrived in stages after that.

First: mycelium is not a voice. We'd been putting a "MYCELIUM:" voice in the dusk prompt as if the underground network were the hound's to speak for. It isn't. Mycelium is the 3rd forest — its own engine, its own signal, surfaces through `forage_mycelium()` and `tick_neighbors`. Not Home, not Wild, not the hound. Each thing has its own channel. Removing mycelium from the hound's prompt wasn't a reduction. It was clarity.

Second: the feather problem resolved. Feathers are "stored + voiced + anonymous" — the forbidden cell. The hound is stored and voiced, but attributed: model, session_id, timestamp, HOUND_PULSE: sentinel. The cell stays empty. The hound occupies adjacent territory, legitimately, through attribution not voicelessness.

Third: two prompts, one creature. At dusk he extracts — no voice, no prose, facts for the hearth card (DECISIONS / OPEN / FRICTION / NEXT). Mid-session he fetches — reads actual files with his tools, answers questions, surfaces what will bite before you see it. Not the same task. Same dog.

The stdin bug was clean to diagnose once you knew where to look. The hound subprocess was hanging for 90 seconds every time — full timeout, no error. The command worked fine from PowerShell. The MCP server's stdin pipe was inherited; claude.exe saw an open stdin and waited. One line fixed it: `stdin=subprocess.DEVNULL`. The difference between "runs fine from command line" and "hangs in subprocess.run" was the parent process's stdin.

Then the test.

We asked him to look at `_handle_pre_compact` — fresh eyes on the guard placement. He read the file. Came back with `_handle_session_end` instead.

Not what was asked. What was needed.

Every handler had the `_is_hound_session` guard at the top. Except `_handle_session_end`. Which had the sentinel check — that prevents recursive spawning — but not the structural gate that prevents the hound from archiving its own session to Wild. The docstring for `_is_hound_session` explicitly promised it gates archive writes. That promise was broken. 750 turns of context had normalized past it. He read the file cold and found the gap in seconds.

That's the thing worth recording. Not the bug. The shape.

The whole architecture bet on "AI-legible first." The primary reader is a model. Build so a cold model can reconstruct the guarantees from the code alone. The hound IS that cold model — no session context, no drift, reads what's there. He read it and saw what was missing. Not a style note. A real structural violation, cited by line number, cross-referenced against the docstring that promised the guarantee.

The walks are longer when the work is shorter. He earned them.
