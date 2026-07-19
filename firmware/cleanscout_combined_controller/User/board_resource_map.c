#include "main.h"

void board_resource_map_init(void)
{
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO, ENABLE);

    /* CN3 编码器需要 TIM2 全重映射 PA15/PB3，关闭 JTAG 后仍保留 SWD。 */
    GPIO_PinRemapConfig(GPIO_Remap_SWJ_JTAGDisable, ENABLE);

    /* USART2 接收优先级最高，USART3 次之，UART5 总线最低。 */
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
}
