# R35 timer experiment - implemented, unmeasured, deferred

The new2026-10-12 goal prioritizes material native frame-budget deficits and
short discriminating hardware tests before expanded validation. This pending
experiment is preserved separately and is not a validated speedup.

DSP_TIMER_FAST defaults0 and requires the exact dry mixer. It computes timer
remainders with a bit mask for power-of-two periods, returns the numerator if
below the period, and uses raw unsigned DIV only for the remaining legal
positive cases. It does not alter guest clocks, envelope values, rates or
next deadlines. HI/LO remain handler scratch, not claimed identical.

Local evidence:983040 legal timer/rate pairs,9216 linked paired callbacks,
nine voice/noise owners, all32 rate/offset words, three negative mutations,
stereo/unrelated GPR64/CP0 owners pass. Actual DIV executions9216->5346, but
executed scalar instructions274587->289059.2048 actual paired DSP scheduler
calls retain PCM/state/672-cycle debit, all64 BRR range/filter pairs, both AI
halves, nine field offsets and three pointer mutations. Six linked HI/LO
writers/unsafe-master mutation pass. No native timing follows from these counts.

The first attempt to count DIV using the VM injection hook failed because the
old DIV is in a branch delay slot; a passive fetch counter fixes observation
without changing the shared VM or interpreted instructions. This was not a
hardware failure.

Source is archived on experiment/dsp-timer-r35-unmeasured. It has not run on
N64 and is not merged into the active work branch or master. No full CI is
requested for an unmeasured marginal candidate. Revisit only if a measured
scenario makes timer division a material recoverable cost. Current priority
is the demonstrated ALttP renderer/RSP deficit; preserve all prior native
improvements and use the R34 primary DSP as an oracle rather than a slow
direct replacement.

[Curated local evidence](evidence/dsp-timer-r35-deferred.json).
