/* Private recorder/runtime interface. Snapshot bytes are never sent unsolicited. */
#ifndef S64_RECORDER_RUNTIME_ABI_H
#define S64_RECORDER_RUNTIME_ABI_H
#include <stdint.h>
enum s64_save_stage {
    S64_SAVE_STAGE_NONE, S64_SAVE_STAGE_DESCRIPTOR, S64_SAVE_STAGE_UNLOCK,
    S64_SAVE_STAGE_SD_INIT, S64_SAVE_STAGE_SD_SWAP, S64_SAVE_STAGE_CARD_INFO,
    S64_SAVE_STAGE_SOURCE, S64_SAVE_STAGE_SLOT_SCAN, S64_SAVE_STAGE_HEADER_BEGIN,
    S64_SAVE_STAGE_BODY, S64_SAVE_STAGE_HEADER_COMMIT, S64_SAVE_STAGE_SD_STATUS
};
enum s64_save_error {
    S64_SAVE_ERROR_NONE, S64_SAVE_ERROR_DESCRIPTOR_MISSING,
    S64_SAVE_ERROR_DESCRIPTOR_FORMAT, S64_SAVE_ERROR_DESCRIPTOR_CHECKSUM,
    S64_SAVE_ERROR_DESCRIPTOR_MAP, S64_SAVE_ERROR_IDENTIFIER,
    S64_SAVE_ERROR_SC64, S64_SAVE_ERROR_COMMAND_TIMEOUT,
    S64_SAVE_ERROR_PI_TIMEOUT, S64_SAVE_ERROR_PI,
    S64_SAVE_ERROR_CARD_MISMATCH, S64_SAVE_ERROR_SOURCE,
    S64_SAVE_ERROR_READBACK, S64_SAVE_ERROR_UNAVAILABLE,
    S64_SAVE_ERROR_EXHAUSTED, S64_SAVE_ERROR_SD_STATUS,
    S64_SAVE_ERROR_TRANSPORT
};
extern uint32_t continuous_save_error_stage, continuous_save_error_code;
extern uint32_t continuous_save_sc64_status, continuous_save_data0;
extern uint32_t continuous_save_pi_status, continuous_save_last_command;
extern uint32_t continuous_save_sd_status, continuous_save_sink_ready;
extern uint32_t continuous_save_last_id;
extern uint32_t native_diag_phase, native_diag_usb_only;
/* 0 pending, 1 verified SD, 2 immutable USB snapshot, -1 SD failure. */
extern int32_t native_diag_capture_result;
extern uint32_t native_diag_snapshot_ready, native_diag_snapshot_sequence;
extern unsigned char native_diag_snapshot[32768];
/* Called at a retired frame via the architectural runtime bridge: 1/0/-1. */
int native_diag_remote_arm(void);
#endif
