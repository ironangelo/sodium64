/* Private REMOTE counters. These words are within the exact-8-MiB
 * boot-cleared arena, after USB/RDP state and below its upper canary. */
#define DSP_RSP_LAUNCHES        0x80441cb0
#define DSP_REG_READS           0x80441cb4
#define DSP_VOLATILE_READS      0x80441cb8
#define DSP_READ_JOBS           0x80441cbc
#define DSP_READ_COUNT          0x80441cc0
#define DSP_READ_STATE          0x80441cc4
#define DSP_READ_WAIT_PEAK      0x80441cc8
#define DSP_READ_WAIT_250US     0x80441ccc
#define DSP_READ_WAIT_1MS       0x80441cd0

#define DSP_GUEST_EPOCH_BIAS   0x80441cd4
#define DSP_GUEST_PAIR_OPEN    0x80441cd8
#define DSP_GUEST_PAIR_TIME    0x80441cdc
#define DSP_GUEST_PAIR_COUNT   0x80441ce0
#define DSP_GUEST_PAIR_EXACT   0x80441ce4
#define DSP_GUEST_PAIR_SHORT   0x80441ce8
#define DSP_GUEST_ECHO_READ    0x80441cec
#define DSP_GUEST_ECHO_ENTRY   0x80441cf0

#define DSP_WAIT_250US 11719
#define DSP_WAIT_1MS   46875
