#include "main.h"

#define CSR_WHEEL_COUNT            4
#define CSR_CONTROL_PERIOD_MS      20UL
#define CSR_TELEMETRY_PERIOD_MS    100UL
#define CSR_COMMAND_TIMEOUT_MS     400UL
#define CSR_RX_BUFFER_SIZE         96
#define CSR_PWM_PER_MPS            1000.0f
#define CSR_PWM_MIN                80
#define CSR_PWM_MAX                1000
#define CSR_PWM_TOP                2000
#define CSR_PWM_LOW                0
#define CSR_PWM_HIGH               CSR_PWM_TOP
#define CSR_BOOT_PHASE_TEST        0
#define CSR_PHASE_TEST_PWM         700
#define CSR_PHASE_RUN_MS           1000UL
#define CSR_PHASE_STOP_MS          500UL

typedef int16_t (*csr_encoder_getter_t)(void);
typedef void (*csr_motor_setter_t)(int16_t speed);

enum
{
	CSR_WHEEL_CN1 = 0,
	CSR_WHEEL_CN2 = 1,
	CSR_WHEEL_CN3 = 2,
	CSR_WHEEL_CN4 = 3
};

typedef struct
{
	const char *label;
	csr_encoder_getter_t encoder_get;
	int8_t encoder_sign;
	csr_motor_setter_t motor_set;
	int8_t motor_sign;
} csr_wheel_config_t;

static const csr_wheel_config_t g_wheels[CSR_WHEEL_COUNT] =
{
	/* Board connector -> vendor channel:
	 * CN1 -> MOTOR_C/ENCODER_C, CN2 -> MOTOR_A/ENCODER_A,
	 * CN3 -> MOTOR_D/ENCODER_D, CN4 -> MOTOR_B/ENCODER_B.
	 * motor_sign maps protocol-positive vehicle-forward to each connector's
	 * proven bottom truth direction. Do not change csr_set_cn*_truth() for
	 * vehicle semantics; only adjust this mapping layer.
	 */
	{"CN1", ENCODER_C_GetCounter, -1, MOTOR_C_SetSpeed,  1},
	{"CN2", ENCODER_A_GetCounter,  1, MOTOR_A_SetSpeed, -1},
	{"CN3", ENCODER_D_GetCounter,  1, MOTOR_D_SetSpeed,  1},
	{"CN4", ENCODER_B_GetCounter, -1, MOTOR_B_SetSpeed, -1}
};

static float g_targets[CSR_WHEEL_COUNT] = {0};
static float g_velocity[CSR_WHEEL_COUNT] = {0};
static int16_t g_pwm[CSR_WHEEL_COUNT] = {0};
static int16_t g_raw_counts[CSR_WHEEL_COUNT] = {0};
static int16_t g_raw_pwm_override[CSR_WHEEL_COUNT] = {0};
static uint8_t g_raw_override_active = 0;
static u32 g_last_command_ms = 0;
static u32 g_last_control_ms = 0;
static u32 g_last_telemetry_ms = 0;
static char g_rx_buffer[CSR_RX_BUFFER_SIZE];
static uint8_t g_rx_length = 0;

static void csr_uart2_init(uint32_t baudrate);
static void csr_uart2_send_byte(uint8_t value);
static void csr_uart2_send(const char *text);
static int csr_uart2_try_read(uint8_t *value);
static void csr_delay_ms(u32 delay_ms);
static void csr_motor_stop_all(void);
static void csr_cn_stop(uint8_t index);
static void csr_set_cn1_truth(uint8_t forward);
static void csr_set_cn2_truth(uint8_t forward);
static void csr_set_cn3_truth(uint8_t forward);
static void csr_set_cn4_truth(uint8_t forward);
static void csr_cn_drive_truth(uint8_t index, uint8_t forward, uint16_t pwm);
static void csr_cn_set_direct_truth(uint8_t index, uint8_t forward);
static void csr_cn_set_truth(uint8_t index, int16_t signed_pwm);
#if CSR_BOOT_PHASE_TEST
static void csr_run_boot_phase_test(void);
#endif
static void csr_apply_motor_outputs(void);
static void csr_stop_all(void);
static void csr_update_control(void);
static void csr_send_telemetry(void);
static void csr_process_serial(void);
static void csr_process_line(char *line);
static void csr_send_error(const char *reason);
static uint8_t csr_find_wheel_index(const char *label, uint8_t *index);
static uint8_t csr_parse_level_token(const char *token, uint8_t *level);
static int16_t csr_target_to_pwm(float target);
static char *csr_append_fixed3(char *cursor, float value);
static void csr_trim_line(char *line);

static void csr_uart2_init(uint32_t baudrate)
{
	GPIO_InitTypeDef gpio_init;
	USART_InitTypeDef usart_init;

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_AFIO, ENABLE);
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2, ENABLE);

	GPIO_StructInit(&gpio_init);
	gpio_init.GPIO_Pin = GPIO_Pin_2;
	gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
	gpio_init.GPIO_Mode = GPIO_Mode_AF_PP;
	GPIO_Init(GPIOA, &gpio_init);

	gpio_init.GPIO_Pin = GPIO_Pin_3;
	gpio_init.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	GPIO_Init(GPIOA, &gpio_init);

	USART_StructInit(&usart_init);
	usart_init.USART_BaudRate = baudrate;
	usart_init.USART_WordLength = USART_WordLength_8b;
	usart_init.USART_StopBits = USART_StopBits_1;
	usart_init.USART_Parity = USART_Parity_No;
	usart_init.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
	usart_init.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
	USART_Init(USART2, &usart_init);
	USART_Cmd(USART2, ENABLE);
}

static void csr_uart2_send_byte(uint8_t value)
{
	while (USART_GetFlagStatus(USART2, USART_FLAG_TXE) == RESET)
	{
	}
	USART_SendData(USART2, value);
}

static void csr_uart2_send(const char *text)
{
	while (*text != '\0')
	{
		csr_uart2_send_byte((uint8_t)(*text));
		text++;
	}
}

static int csr_uart2_try_read(uint8_t *value)
{
	if (USART_GetFlagStatus(USART2, USART_FLAG_RXNE) == RESET)
	{
		return 0;
	}

	*value = (uint8_t)(USART_ReceiveData(USART2) & 0xFF);
	return 1;
}

static void csr_delay_ms(u32 delay_ms)
{
	u32 start = millis();
	while ((millis() - start) < delay_ms)
	{
	}
}

static void csr_cn_write(uint8_t index, BitAction in1_level, uint16_t in2_compare)
{
	if (in2_compare > CSR_PWM_TOP)
	{
		in2_compare = CSR_PWM_TOP;
	}

	switch (index)
	{
	case CSR_WHEEL_CN1:
		GPIO_WriteBit(GPIOA, GPIO_Pin_8, in1_level);
		TIM_SetCompare1(TIM8, in2_compare);
		break;
	case CSR_WHEEL_CN2:
		GPIO_WriteBit(GPIOA, GPIO_Pin_11, in1_level);
		TIM_SetCompare2(TIM8, in2_compare);
		break;
	case CSR_WHEEL_CN3:
		GPIO_WriteBit(GPIOA, GPIO_Pin_12, in1_level);
		TIM_SetCompare3(TIM8, in2_compare);
		break;
	case CSR_WHEEL_CN4:
		GPIO_WriteBit(GPIOC, GPIO_Pin_10, in1_level);
		TIM_SetCompare4(TIM8, in2_compare);
		break;
	default:
		break;
	}
}

static void csr_motor_stop_all(void)
{
	MOTOR_A_SetSpeed(0);
	MOTOR_B_SetSpeed(0);
	MOTOR_C_SetSpeed(0);
	MOTOR_D_SetSpeed(0);

	GPIO_WriteBit(GPIOA, GPIO_Pin_8, Bit_RESET);
	GPIO_WriteBit(GPIOA, GPIO_Pin_11, Bit_RESET);
	GPIO_WriteBit(GPIOA, GPIO_Pin_12, Bit_RESET);
	GPIO_WriteBit(GPIOC, GPIO_Pin_10, Bit_RESET);

	TIM_SetCompare1(TIM8, CSR_PWM_LOW);
	TIM_SetCompare2(TIM8, CSR_PWM_LOW);
	TIM_SetCompare3(TIM8, CSR_PWM_LOW);
	TIM_SetCompare4(TIM8, CSR_PWM_LOW);
}

static void csr_cn_stop(uint8_t index)
{
	switch (index)
	{
	case CSR_WHEEL_CN1:
		GPIO_WriteBit(GPIOA, GPIO_Pin_8, Bit_RESET);
		TIM_SetCompare1(TIM8, CSR_PWM_LOW);
		break;
	case CSR_WHEEL_CN2:
		GPIO_WriteBit(GPIOA, GPIO_Pin_11, Bit_RESET);
		TIM_SetCompare2(TIM8, CSR_PWM_LOW);
		break;
	case CSR_WHEEL_CN3:
		GPIO_WriteBit(GPIOA, GPIO_Pin_12, Bit_RESET);
		TIM_SetCompare3(TIM8, CSR_PWM_LOW);
		break;
	case CSR_WHEEL_CN4:
		GPIO_WriteBit(GPIOC, GPIO_Pin_10, Bit_RESET);
		TIM_SetCompare4(TIM8, CSR_PWM_LOW);
		break;
	default:
		break;
	}
}

static void csr_set_cn1_truth(uint8_t forward)
{
	/* CN1 -> U2: IN1 = PA8, IN2 = PC6/TIM8_CH1 */
	GPIO_WriteBit(GPIOA, GPIO_Pin_8, forward ? Bit_SET : Bit_RESET);
	TIM_SetCompare1(TIM8, forward ? CSR_PWM_LOW : CSR_PWM_HIGH);
}

static void csr_set_cn2_truth(uint8_t forward)
{
	/* CN2 -> U3: IN1 = PA11, IN2 = PC7/TIM8_CH2 */
	GPIO_WriteBit(GPIOA, GPIO_Pin_11, forward ? Bit_SET : Bit_RESET);
	TIM_SetCompare2(TIM8, forward ? CSR_PWM_LOW : CSR_PWM_HIGH);
}

static void csr_set_cn3_truth(uint8_t forward)
{
	/* CN3 -> U4: IN1 = PA12, IN2 = PC8/TIM8_CH3 */
	GPIO_WriteBit(GPIOA, GPIO_Pin_12, forward ? Bit_SET : Bit_RESET);
	TIM_SetCompare3(TIM8, forward ? CSR_PWM_LOW : CSR_PWM_HIGH);
}

static void csr_set_cn4_truth(uint8_t forward)
{
	/* CN4 -> U5: IN1 = PC10, IN2 = PC9/TIM8_CH4 */
	GPIO_WriteBit(GPIOC, GPIO_Pin_10, forward ? Bit_SET : Bit_RESET);
	TIM_SetCompare4(TIM8, forward ? CSR_PWM_LOW : CSR_PWM_HIGH);
}

static void csr_cn_drive_truth(uint8_t index, uint8_t forward, uint16_t pwm)
{
	uint16_t compare;

	if (pwm > CSR_PWM_TOP)
	{
		pwm = CSR_PWM_TOP;
	}
	if (pwm == 0)
	{
		csr_cn_stop(index);
		return;
	}

	/* Variable-speed form of the proven truth table:
	 * forward: IN1=1, IN2 duty decreases as speed increases.
	 * reverse: IN1=0, IN2 duty increases as speed increases.
	 */
	compare = forward ? (uint16_t)(CSR_PWM_TOP - pwm) : pwm;
	csr_cn_write(index, forward ? Bit_SET : Bit_RESET, compare);
}

static void csr_cn_set_direct_truth(uint8_t index, uint8_t forward)
{
	switch (index)
	{
	case CSR_WHEEL_CN1:
		csr_set_cn1_truth(forward);
		break;
	case CSR_WHEEL_CN2:
		csr_set_cn2_truth(forward);
		break;
	case CSR_WHEEL_CN3:
		csr_set_cn3_truth(forward);
		break;
	case CSR_WHEEL_CN4:
		csr_set_cn4_truth(forward);
		break;
	default:
		break;
	}
}

static void csr_cn_set_truth(uint8_t index, int16_t signed_pwm)
{
	int32_t mapped_pwm;

	if (index >= CSR_WHEEL_COUNT)
	{
		return;
	}

	mapped_pwm = (int32_t)signed_pwm * (int32_t)g_wheels[index].motor_sign;
	if (mapped_pwm > 2000)
	{
		mapped_pwm = 2000;
	}
	else if (mapped_pwm < -2000)
	{
		mapped_pwm = -2000;
	}

	if (mapped_pwm == 0)
	{
		csr_cn_stop(index);
		return;
	}

	g_wheels[index].motor_set((int16_t)mapped_pwm);
}

#if CSR_BOOT_PHASE_TEST
static void csr_run_boot_phase_test(void)
{
	uint8_t index;
	char line[48];

	csr_uart2_send("CSR_PHASE_TEST_READY\r\n");

	while (1)
	{
		for (index = 0; index < CSR_WHEEL_COUNT; index++)
		{
			sprintf(line, "PHASE,%s,+,START\r\n", g_wheels[index].label);
			csr_uart2_send(line);
			csr_cn_set_direct_truth(index, 1);
			csr_delay_ms(CSR_PHASE_RUN_MS);
			csr_motor_stop_all();
			csr_delay_ms(CSR_PHASE_STOP_MS);

			sprintf(line, "PHASE,%s,-,START\r\n", g_wheels[index].label);
			csr_uart2_send(line);
			csr_cn_set_direct_truth(index, 0);
			csr_delay_ms(CSR_PHASE_RUN_MS);
			csr_motor_stop_all();
			csr_delay_ms(CSR_PHASE_STOP_MS);
		}
	}
}
#endif

static void csr_apply_motor_outputs(void)
{
	uint8_t index;

	for (index = 0; index < CSR_WHEEL_COUNT; index++)
	{
		if (g_raw_override_active != 0)
		{
			if (g_raw_pwm_override[index] == 0)
			{
				csr_cn_stop(index);
			}
			else
			{
				/* RAW is a bottom-layer diagnostic: bypass vehicle motor_sign. */
				csr_cn_set_direct_truth(index, (g_raw_pwm_override[index] > 0) ? 1 : 0);
			}
		}
		else
		{
			csr_cn_set_truth(index, g_pwm[index]);
		}
	}
}

static void csr_stop_all(void)
{
	uint8_t index;

	for (index = 0; index < CSR_WHEEL_COUNT; index++)
	{
		g_targets[index] = 0.0f;
		g_pwm[index] = 0;
		g_raw_pwm_override[index] = 0;
	}
	g_raw_override_active = 0;

	csr_motor_stop_all();
}

static int16_t csr_target_to_pwm(float target)
{
	float absolute_target;
	float pwm_f;
	int16_t pwm_value;

	if ((target > -0.001f) && (target < 0.001f))
	{
		return 0;
	}

	absolute_target = target;
	if (absolute_target < 0.0f)
	{
		absolute_target = -absolute_target;
	}

	pwm_f = absolute_target * CSR_PWM_PER_MPS;
	if (pwm_f > (float)CSR_PWM_MAX)
	{
		pwm_f = (float)CSR_PWM_MAX;
	}
	if ((pwm_f > 0.0f) && (pwm_f < (float)CSR_PWM_MIN))
	{
		pwm_f = (float)CSR_PWM_MIN;
	}

	pwm_value = (int16_t)(pwm_f + 0.5f);
	if (target < 0.0f)
	{
		pwm_value = (int16_t)(-pwm_value);
	}

	return pwm_value;
}

static void csr_update_control(void)
{
	int16_t delta_counts[CSR_WHEEL_COUNT];
	uint8_t index;
	u32 now_ms;

	now_ms = millis();
	if ((now_ms - g_last_control_ms) < CSR_CONTROL_PERIOD_MS)
	{
		return;
	}
	g_last_control_ms = now_ms;

	for (index = 0; index < CSR_WHEEL_COUNT; index++)
	{
		delta_counts[index] = (int16_t)(g_wheels[index].encoder_get() * g_wheels[index].encoder_sign);
		g_raw_counts[index] = delta_counts[index];
		g_velocity[index] = (float)delta_counts[index] * MEC_WHEEL_SCALE;
	}

	if ((now_ms - g_last_command_ms) > CSR_COMMAND_TIMEOUT_MS)
	{
		csr_stop_all();
		return;
	}

	if (g_raw_override_active != 0)
	{
		for (index = 0; index < CSR_WHEEL_COUNT; index++)
		{
			g_pwm[index] = g_raw_pwm_override[index];
		}
	}
	else
	{
		for (index = 0; index < CSR_WHEEL_COUNT; index++)
		{
			g_pwm[index] = csr_target_to_pwm(g_targets[index]);
		}
	}

	csr_apply_motor_outputs();
}

static char *csr_append_fixed3(char *cursor, float value)
{
	long scaled;
	long whole;
	long fraction;

	scaled = (long)(value * 1000.0f);
	if (value >= 0.0f)
	{
		scaled = (long)(value * 1000.0f + 0.5f);
	}
	else
	{
		scaled = (long)(value * 1000.0f - 0.5f);
	}

	if (scaled < 0)
	{
		*cursor++ = '-';
		scaled = -scaled;
	}

	whole = scaled / 1000L;
	fraction = scaled % 1000L;
	cursor += sprintf(cursor, "%ld.%03ld", whole, fraction);
	return cursor;
}

static void csr_send_telemetry(void)
{
	char line[192];
	char *cursor;
	u32 now_ms;

	now_ms = millis();
	if ((now_ms - g_last_telemetry_ms) < CSR_TELEMETRY_PERIOD_MS)
	{
		return;
	}
	g_last_telemetry_ms = now_ms;

	cursor = line;
	cursor += sprintf(cursor, "ENC_RAW,%d,%d,%d,%d\r\n",
			(int)g_raw_counts[CSR_WHEEL_CN1],
			(int)g_raw_counts[CSR_WHEEL_CN2],
			(int)g_raw_counts[CSR_WHEEL_CN3],
			(int)g_raw_counts[CSR_WHEEL_CN4]);
	csr_uart2_send(line);

	cursor = line;
	cursor += sprintf(cursor, "VEL,");
	cursor = csr_append_fixed3(cursor, g_velocity[CSR_WHEEL_CN1]);
	*cursor++ = ',';
	cursor = csr_append_fixed3(cursor, g_velocity[CSR_WHEEL_CN2]);
	*cursor++ = ',';
	cursor = csr_append_fixed3(cursor, g_velocity[CSR_WHEEL_CN3]);
	*cursor++ = ',';
	cursor = csr_append_fixed3(cursor, g_velocity[CSR_WHEEL_CN4]);
	*cursor++ = ',';
	cursor = csr_append_fixed3(cursor, g_targets[CSR_WHEEL_CN1]);
	*cursor++ = ',';
	cursor = csr_append_fixed3(cursor, g_targets[CSR_WHEEL_CN2]);
	*cursor++ = ',';
	cursor = csr_append_fixed3(cursor, g_targets[CSR_WHEEL_CN3]);
	*cursor++ = ',';
	cursor = csr_append_fixed3(cursor, g_targets[CSR_WHEEL_CN4]);
	*cursor++ = '\r';
	*cursor++ = '\n';
	*cursor = '\0';
	csr_uart2_send(line);

	sprintf(line, "PWM,%d,%d,%d,%d\r\n",
			(int)g_pwm[CSR_WHEEL_CN1],
			(int)g_pwm[CSR_WHEEL_CN2],
			(int)g_pwm[CSR_WHEEL_CN3],
			(int)g_pwm[CSR_WHEEL_CN4]);
	csr_uart2_send(line);
}

static void csr_send_error(const char *reason)
{
	char line[64];

	sprintf(line, "ERR:%s\r\n", reason);
	csr_uart2_send(line);
}

static uint8_t csr_find_wheel_index(const char *label, uint8_t *index)
{
	uint8_t wheel;

	for (wheel = 0; wheel < CSR_WHEEL_COUNT; wheel++)
	{
		if (strcmp(label, g_wheels[wheel].label) == 0)
		{
			*index = wheel;
			return 1;
		}
	}

	return 0;
}

static uint8_t csr_parse_level_token(const char *token, uint8_t *level)
{
	if ((token == NULL) || (token[1] != '\0'))
	{
		return 0;
	}
	if (token[0] == '0')
	{
		*level = 0;
		return 1;
	}
	if (token[0] == '1')
	{
		*level = 1;
		return 1;
	}
	return 0;
}

static void csr_trim_line(char *line)
{
	size_t length;

	length = strlen(line);
	while (length > 0)
	{
		if ((line[length - 1] == '\r') || (line[length - 1] == '\n') || (line[length - 1] == ' ') || (line[length - 1] == '\t'))
		{
			line[length - 1] = '\0';
			length--;
		}
		else
		{
			break;
		}
	}
}

static void csr_process_line(char *line)
{
	char parse_buffer[CSR_RX_BUFFER_SIZE];
	char *token;
	char *endptr;
	double parsed_values[CSR_WHEEL_COUNT];
	long raw_pwm;
	uint8_t index;
	uint8_t wheel;

	csr_trim_line(line);
	if (line[0] == '\0')
	{
		return;
	}

	strncpy(parse_buffer, line, sizeof(parse_buffer) - 1);
	parse_buffer[sizeof(parse_buffer) - 1] = '\0';

	token = strtok(parse_buffer, ",");
	if (token == NULL)
	{
		csr_send_error("bad_prefix");
		return;
	}

	if (strcmp(token, "RAW") == 0)
	{
		token = strtok(NULL, ",");
		if ((token == NULL) || (csr_find_wheel_index(token, &index) == 0))
		{
			csr_send_error("bad_wheel");
			return;
		}

		token = strtok(NULL, ",");
		if (token == NULL)
		{
			csr_send_error("arg_count");
			return;
		}

		endptr = NULL;
		raw_pwm = strtol(token, &endptr, 10);
		if ((endptr == token) || (*endptr != '\0'))
		{
			csr_send_error("parse_int");
			return;
		}
		if ((raw_pwm < -2000L) || (raw_pwm > 2000L))
		{
			csr_send_error("range");
			return;
		}
		if (strtok(NULL, ",") != NULL)
		{
			csr_send_error("arg_count");
			return;
		}

		for (wheel = 0; wheel < CSR_WHEEL_COUNT; wheel++)
		{
			g_targets[wheel] = 0.0f;
			g_raw_pwm_override[wheel] = 0;
		}
		g_raw_override_active = 1;
		g_raw_pwm_override[index] = (int16_t)raw_pwm;
		g_last_command_ms = millis();
		csr_uart2_send("ACK:RAW\r\n");
		return;
	}

	if (strcmp(token, "LVL") == 0)
	{
		uint8_t in1_level;
		uint8_t in2_level;

		token = strtok(NULL, ",");
		if ((token == NULL) || (csr_find_wheel_index(token, &index) == 0))
		{
			csr_send_error("bad_wheel");
			return;
		}

		token = strtok(NULL, ",");
		if (csr_parse_level_token(token, &in1_level) == 0)
		{
			csr_send_error("parse_in1");
			return;
		}

		token = strtok(NULL, ",");
		if (csr_parse_level_token(token, &in2_level) == 0)
		{
			csr_send_error("parse_in2");
			return;
		}

		if (strtok(NULL, ",") != NULL)
		{
			csr_send_error("arg_count");
			return;
		}

		for (wheel = 0; wheel < CSR_WHEEL_COUNT; wheel++)
		{
			g_targets[wheel] = 0.0f;
			g_pwm[wheel] = 0;
			g_raw_pwm_override[wheel] = 0;
		}
		g_raw_override_active = 1;
		g_last_command_ms = millis();
		csr_cn_write(index, in1_level ? Bit_SET : Bit_RESET, in2_level ? CSR_PWM_TOP : 0);
		sprintf(parse_buffer, "ACK:LVL,%s,%u,%u\r\n", g_wheels[index].label, in1_level, in2_level);
		csr_uart2_send(parse_buffer);
		return;
	}

	if (strcmp(token, "W") != 0)
	{
		csr_send_error("bad_prefix");
		return;
	}

	for (index = 0; index < CSR_WHEEL_COUNT; index++)
	{
		token = strtok(NULL, ",");
		if (token == NULL)
		{
			csr_send_error("arg_count");
			return;
		}

		endptr = NULL;
		parsed_values[index] = strtod(token, &endptr);
		if ((endptr == token) || (*endptr != '\0'))
		{
			csr_send_error("parse_float");
			return;
		}
	}

	if (strtok(NULL, ",") != NULL)
	{
		csr_send_error("arg_count");
		return;
	}

	for (index = 0; index < CSR_WHEEL_COUNT; index++)
	{
		g_targets[index] = (float)parsed_values[index];
	}
	g_raw_override_active = 0;
	g_last_command_ms = millis();
	csr_uart2_send("ACK:W\r\n");
}

static void csr_process_serial(void)
{
	uint8_t value;

	while (csr_uart2_try_read(&value) != 0)
	{
		if (value == '\r')
		{
			continue;
		}

		if (value == '\n')
		{
			g_rx_buffer[g_rx_length] = '\0';
			csr_process_line(g_rx_buffer);
			g_rx_length = 0;
			continue;
		}

		if (g_rx_length < (CSR_RX_BUFFER_SIZE - 1))
		{
			g_rx_buffer[g_rx_length++] = (char)value;
		}
		else
		{
			g_rx_length = 0;
			csr_send_error("line_too_long");
		}
	}
}

int main(void)
{
	SysTick_Init();
	motor_init();
	Encoder_Init();
	csr_uart2_init(115200);
	csr_stop_all();
	g_last_command_ms = millis();
	g_last_control_ms = millis();
	g_last_telemetry_ms = millis();

	csr_uart2_send("CSR_RF1_READY\r\n");

#if CSR_BOOT_PHASE_TEST
	csr_run_boot_phase_test();
#endif

	while (1)
	{
		csr_process_serial();
		csr_update_control();
		csr_send_telemetry();
	}
}
