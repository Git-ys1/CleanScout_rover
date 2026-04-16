#include "./y_global/y_global.h"
#include "stm32f10x_conf.h"

char cmd_return[CMD_RETURN_SIZE]; // 用来处理临时的字符串指令
u8 group_do_ok = 1;               // 完成动作组标记1

u8 AI_mode = 255;   // 运行的传感器的模式
u8 forbid_turn = 0; // 循迹模式适配地图

eeprom_info_t eeprom_info;    // 控制板存储的信息
uint8_t uart_receive_num = 0; /* 记录是哪个接口接收到的数据,解析指令的时候不会在发送 */

u32 action_time = 0; // 计算动作执行时间
int do_start_index;  // 动作组执行 起始序号
int do_group_cnt;    // 动作组执行 执行次数
int group_num_start; // 动作组执行 起始序号
int group_num_end;   // 动作组执行 终止序号
int group_num_cnt;   // 动作组执行 起始变量
int oled_mode = 0;   // oled显示速度时为0，显示功能为1
int mv_mode = 0;     // oled显示速度时为0，显示功能为1

/* 解析字符串 */
void parse_string(char *str)
{
    if (str_contain_str(str, "$"))
    {
        // 命令模式
        parse_cmd(str);
    }
    else if (str_contain_str(str, "#"))
    {
        // 舵机调试
        parse_action(str);
    }
}

/* 单片机软件复位 */
void soft_reset(void)
{
    printf("stm32 reset\r\n");
    // 关闭所有中断
    __set_FAULTMASK(1);
    // 复位
    NVIC_SystemReset();
}

void zx_uart_send_str(char *str)
{
    uart_get_ok = 1;
    if (uart_receive_num != 1)
        uart1_send_str(str);
    else
        uart_receive_num = 0;

    if (uart_receive_num != 2)
        uart2_send_str(str);
    else
        uart_receive_num = 0;

    if (uart_receive_num != 3)
        uart3_send_str(str);
    else
        uart_receive_num = 0;

    if (uart_receive_num != 5)
        uart5_send_str(str);
    else
        uart_receive_num = 0;

    uart_get_ok = 0;
}

/**
 * @函数描述: 检测字符串str是否包含str2
 * @返回 {*}
 */
uint16_t str_contain_str(char *str, char *str2)
{
    char *str_temp, *str_temp2;
    str_temp = str;
    str_temp2 = str2;
    while (*str_temp) // 循环遍历直到字符串的结束
    {
        if (*str_temp == *str_temp2)
        {
            while (*str_temp2)
            {
                if (*str_temp++ != *str_temp2++)
                {
                    str_temp = str_temp - (str_temp2 - str2) + 1;
                    str_temp2 = str2;
                    break;
                }
            }
            if (!*str_temp2)
            {
                return (str_temp - str);
            }
        }
        else
        {
            str_temp++;
        }
    }
    return 0;
}

void selection_sort(int *a, int len)
{
    int i, j, mi, t;
    for (i = 0; i < len - 1; i++)
    {
        mi = i;
        for (j = i + 1; j < len; j++)
        {
            if (a[mi] > a[j])
            {
                mi = j;
            }
        }

        if (mi != i)
        {
            t = a[mi];
            a[mi] = a[i];
            a[i] = t;
        }
    }
}

// int型 取绝对值函数
int abs_int(int int1)
{
    if (int1 > 0)
        return int1;
    return (-int1);
}

float abs_float(float value)
{
    if (value > 0)
    {
        return value;
    }
    return (-value);
}

// 字符串中的字符替代函数 把str字符串中所有的ch1换成ch2
void replace_char(char *str, char ch1, char ch2)
{
    while (*str)
    {
        if (*str == ch1)
        {
            *str = ch2;
        }
        str++;
    }
    return;
}

// 两个int变量交换
void int_exchange(int *int1, int *int2)
{
    int int_temp;
    int_temp = *int1;
    *int1 = *int2;
    *int2 = int_temp;
}

// 处理 #000P1500T1000! 类似的字符串
void parse_action(char *str)
{
    u16 index = 0, time = 0, i = 0, j = 0;
    int len = 0, bias = 0;
    float pwm = 0;

    zx_uart_send_str(str);
    len = strlen((char *)str); // 获取串口接收数据的长度

    if (len >= 12 && str[0] == '#' && str[4] == 'P' && str[5] == 'S' && str[6] == 'C' && str[7] == 'K' && str[12] == '!')
    {
        index = (str[1] - '0') * 100 + (str[2] - '0') * 10 + (str[3] - '0');
        bias = (str[9] - '0') * 100 + (str[10] - '0') * 10 + (str[11] - '0');
        if (bias <= 200 && index < SERVO_NUM)
        {
            if (str[8] == '+')
            {
                pwmServo_bias_set(index, bias);
                eeprom_info.dj_bias_pwm[index] = bias;
            }
            else if (str[8] == '-')
            {
                pwmServo_bias_set(index, -bias);
                eeprom_info.dj_bias_pwm[index] = -bias;
            }
            rewrite_eeprom();
        }
    }
    else if (len >= 8 && str[0] == '#' && str[4] == 'P' && str[5] == 'D' && str[6] == 'S' && str[7] == 'T' && str[8] == '!')
    {
        index = (str[1] - '0') * 100 + (str[2] - '0') * 10 + (str[3] - '0');
        pwmServo_stop_motion(index);
        return;
    }

    while ((len >= i) && str[i])
    {
        if (str[i] == '#')
        {
            index = 0;
            i++;
            for (j = 0; j < 3; j++)
            {
                if ((len >= i) && str[i] <= '9' && str[i] >= '0')
                {
                    index = index * 10 + str[i] - '0';
                    i++;
                }
                else
                {
                    goto err;
                }
            }
        }
        else if (str[i] == 'P')
        {
            pwm = 0;
            i++;
            for (j = 0; j < 4; j++)
            {
                if ((len >= i) && str[i] <= '9' && str[i] >= '0')
                {
                    pwm = pwm * 10 + str[i] - '0';
                    i++;
                }
                else
                {
                    goto err;
                }
            }
        }
        else if (str[i] == 'T')
        {
            time = 0;
            i++;
            for (j = 0; j < 4; j++)
            {
                if ((len >= i) && str[i] <= '9' && str[i] >= '0')
                {
                    time = time * 10 + str[i] - '0';
                    i++;
                }
                else
                {
                    goto err;
                }
            }

            pwmServo_angle_set(index, pwm, time);
        }
        else
        {
        err:
            i++;
        }
    }
}

// 动作组保存函数
// 只有用<>包含的字符串才能在此函数中进行解析
void save_action(char *str)
{
    int32_t action_index = -1;

    if (str[1] == '$' && str[2] == '!') // 删除开机动作
    {
        eeprom_info.pre_cmd[PRE_CMD_SIZE] = 0;
        rewrite_eeprom();
        uart1_send_str("@CLEAR PRE_CMD OK!");
        return;
    }
    else if (str[1] == '$') // 设置开机动作
    {
        memset(eeprom_info.pre_cmd, 0, sizeof(eeprom_info.pre_cmd));
        strcpy(eeprom_info.pre_cmd, str + 1);        // 对字符串进行复制
        eeprom_info.pre_cmd[strlen(str) - 2] = '\0'; // 赋值字符0
        eeprom_info.pre_cmd[PRE_CMD_SIZE] = FLAG_VERIFY;
        rewrite_eeprom();
        zx_uart_send_str("@SET PRE_CMD OK!");
        zx_uart_send_str(eeprom_info.pre_cmd); // 打印存储进去的指令
        return;
    }

    // 获取动作的组号如果不正确，或是第6个字符不是#则认为字符串错误
    action_index = (str[2] - '0') * 1000 + (str[3] - '0') * 100 + (str[4] - '0') * 10 + (str[5] - '0');

    //<G0000#000P1500T1000!>
    if ((action_index < 0) || str[6] != '#')
    {
        zx_uart_send_str("E");
        return;
    }

    if ((action_index * ACTION_SIZE % 4096) == 0)
    {
        w25x_erase_sector(action_index * ACTION_SIZE / 4096);
    }
    // 把尖括号替换成大括号直接存储到存储芯片里面去，则在执行动作组的时候直接拿出来解析就可以了
    replace_char(str, '<', '{');
    replace_char(str, '>', '}');

    w25x_write((u8 *)str, action_index * ACTION_SIZE, strlen(str) + 1);

    // memset(str, 0, sizeof((char *)str));
    // w25x_read(str, action_index * ACTION_SIZE, ACTION_SIZE);
    // uart1_send_str(str);

    // 反馈一个A告诉上位机我已经接收到了
    uart_receive_num = 0;
    zx_uart_send_str("A");

    return;
}

/*
    所有舵机停止命令：    $DST!
    第x个舵机停止命令：   $DST:x!
    单片机重启命令：$RST!
    检查动作组x到y组命令：$CGP:x-y!
    执行第x个动作：       $DGS:x!
    执行第x到y组动作z次： $DGT:x-y,z!
    小车左x、右轮y速度:   $DCR:x,y!
    所有舵机复位命令：    $DJR!
    获取应答信号：        $GETA!
    获取智能信号：        $SMODE1!
    $KINEMATICS:x,y,z,time! //坐标单位mm，时间单位ms

*/
// 命令解析函数
void parse_cmd(char *cmd)
{
    int pos = 0, index = 0, int1 = 0, int4 = 0;
    float kinematics_x = 0, kinematics_y = 0, kinematics_z = 0;
    int mode_num;
    const unsigned char *display_chars;
    int num_chars;
    uart_receive_num = 0;
    // uart1_send_str(cmd);
    if (pos = str_contain_str(cmd, "$DRS!"), pos)
    {
        uart1_send_str("hello word!");
    }
    else if (pos = str_contain_str(cmd, "$DST!"), pos)
    {
        group_do_ok = 1;
        pwmServo_stop_motion(255);
        zx_uart_send_str("#255PDST!"); // 总线停止
        motor_speed_set(0, 0, 0, 0);   // 车停
        AI_mode = 255;
    }
    else if (pos = str_contain_str(cmd, "$DST:"), pos)
    {
        if (sscanf((char *)cmd, "$DST:%d!", &index))
        {
            pwmServo_stop_motion(index);
            sprintf((char *)cmd_return, "#%03dPDST!\r\n", (int)index);
            zx_uart_send_str(cmd_return);
            memset(cmd_return, 0, sizeof(cmd_return));
        }
    }
    else if (pos = str_contain_str(cmd, "$RST!"), pos)
    {
        soft_reset();
    }
    else if (pos = str_contain_str(cmd, "$DGS:"), pos)
    {
        if (sscanf((char *)cmd, "$DGS:%d!", &int1))
        {
            group_do_ok = 1;
            do_group_once(int1);
        }
    }
    else if (pos = str_contain_str(cmd, "$DGT:"), pos)
    {
        if (sscanf((char *)cmd, "$DGT:%d-%d,%d!", &group_num_start, &group_num_end, &group_num_cnt))
        {
            group_do_ok = 1;
            if (group_num_start != group_num_end)
            {
                do_start_index = group_num_start;
                do_group_cnt = group_num_cnt;
                group_do_ok = 0;
            }
            else
            {
                do_group_once(group_num_start);
            }
        }
    }
    else if (pos = str_contain_str(cmd, "$DJR!"), pos)
    {
        zx_uart_send_str("#255P1500T2000!");
        motor_speed_set(0, 0, 0, 0);
        pwmServo_angle_set(255, 1500, 2000);
        AI_mode = 255;
    }
    else if (pos = str_contain_str(cmd, "$SMODE"), pos)
    {
        if (sscanf((char *)uart_receive_buf, "$SMODE%d!", &int1))
        {
            AI_mode = int1;
            if (int1 == 0)
                zx_uart_send_str("#010P1512T0000!");
            if (int1 == 2)
                zx_uart_send_str("#010P1511T0000!");
        }
    }
    else if (pos = str_contain_str(cmd, "$Car:"), pos)
    {
        zx_uart_send_str("cmdOk");
        /* 小车运动参数 */
        float a = 0, b = 0, c = 0, d = 0;
        if (sscanf((char *)cmd, "$Car:%f,%f,%f,%f!", &a, &b, &c, &d))
        {
            motor_speed_set(a, b, c, d);
        }
    }
    else if (pos = str_contain_str(cmd, "$ZNXJ!"), pos)
    {
        /* 智能循迹模式 */
        AI_mode = 1;
        forbid_turn = 0;
    }
    else if (pos = str_contain_str(cmd, "$ZYBZ!"), pos)
    {
        // 自由避障
        AI_mode = 2;
        // 前进
        motor_speed_set(0.3, 0.3, 0.3, 0.3);
    }
    else if (pos = str_contain_str(cmd, "$GSGN!"), pos)
    {
        // 定距跟随
        AI_mode = 3;
    }
    else if (pos = str_contain_str(cmd, "$QJ!"), pos)
    {
        // 前进
        motor_speed_set(0.3, 0.3, 0.3, 0.3);
    }
    else if (pos = str_contain_str(cmd, "$HT!"), pos)
    {
        // 后退
        motor_speed_set(-0.3, -0.3, -0.3, -0.3);
    }
    else if (pos = str_contain_str(cmd, "$ZZ!"), pos)
    {
        // 左转
        motor_speed_set(-0.3, 0.3, -0.3, 0.3);
    }
    else if (pos = str_contain_str(cmd, "$YZ!"), pos)
    {
        // 右转
        motor_speed_set(0.3, -0.3, 0.3, -0.3);
    }
    else if (pos = str_contain_str(cmd, "$ZPY!"), pos)
    {
        // 左平移
        motor_speed_set(-0.3, 0.3, 0.3, -0.3);
    }
    else if (pos = str_contain_str(cmd, "$YPY!"), pos)
    {
        // 右平移
        motor_speed_set(0.3, -0.3, -0.3, 0.3);
    }
    else if (pos = str_contain_str(cmd, "$TZ!"), pos)
    {
        // 停止
        motor_speed_set(0, 0, 0, 0);
        AI_mode = 255;
    }
    else if (pos = str_contain_str(cmd, "$GETA!"), pos)
    {
        uart1_send_str("AAA");
    }
    else if (pos = str_contain_str(cmd, "$SMODE"), pos)
    {
        if (sscanf((char *)uart_receive_buf, "$SMODE%d!", &int1))
        {
            mv_mode = int1;
            if (int1 == 0)
                zx_uart_send_str("#010P1512T0000!");
            if (int1 == 2)
                zx_uart_send_str("#010P1511T0000!");

            // uart1_send_str("@OK!");
        }
    }
    else if (pos = str_contain_str(cmd, "$SMART_STOP!"), pos)
    {
        mdelay(10);
        parse_action("#255PDST!");
        mdelay(10);
        uart1_send_str("#006P1500T0000!#007P1500T0000!");
        mdelay(10);
        uart1_send_str("@OK!");
        mdelay(10);
    }
    else if (pos = str_contain_str(cmd, "$KMS:"), pos)
    {
        if (sscanf((char *)cmd, "$KMS:%f,%f,%f,%d!", &kinematics_x, &kinematics_y, &kinematics_z, &int4))
        {
            // uart1_send_str("Try to find best pos:\r\n");
            if (kinematics_move(kinematics_x, kinematics_y, kinematics_z, int4))
            {
            }
            else
            {
                uart1_send_str("Can't find best pos!!!");
            }
        }
    }
    else if (pos = str_contain_str(cmd, "$CarLineWalk!"), pos)
    {
    }
    else if (pos = str_contain_str(cmd, "$MV"), pos)
    {
        if (sscanf((char *)uart_receive_buf, "$MV%d!", &mode_num))
        {
            oled_mode = 1;
            OLED_CLS();
            mv_mode = mode_num;

            switch (mv_mode)
            {
            case 1:
                display_chars = CAR_COLOR_TRACE;
                num_chars = 6;
                break;
            case 2:
                display_chars = MAP3;
                num_chars = 5;
                break;
            case 3:
                display_chars = ARM_COLOR_TRACE;
                num_chars = 7;
                break;
            case 4:
                display_chars = AprilTag_Sort;
                num_chars = 7;
                break;	
            case 5:
                display_chars = AprilTag_Stack;
                num_chars = 7;
                break;
            case 6:
                display_chars = COLOR_TRACE_GRASP;
                num_chars = 6;
                break;
            case 7:
                display_chars = MAP1;
                num_chars = 5;
                break;
            case 8:
                display_chars = MAP2;
                num_chars = 5;
                break;	
            case 9:
                display_chars = FACE_TRACE;
                num_chars = 4;
                break;		
            case 10:
                display_chars = PTZ_COLOR_TRACE;
                num_chars = 6;
                break;						
            default:
								oled_mode = 0;
                display_chars = NULL;
                num_chars = 0;
                break;
            }

            if (display_chars != NULL)
            {
                for (int i = 0, x = 8; i < num_chars; i++, x += 16)
                {
                    OLED_P16x16Ch(x, 3, i, display_chars);
                }
            }
        }
    }
        else if (pos = str_contain_str(cmd, "$RunStop!"), pos)
        {
            oled_mode = 0;
        }
    }

    // 获取最大时间
    int getMaxTime(char *str)
    {
        int i = 0, max_time = 0, tmp_time = 0;
        while (str[i])
        {
            if (str[i] == 'T')
            {
                tmp_time = (str[i + 1] - '0') * 1000 + (str[i + 2] - '0') * 100 + (str[i + 3] - '0') * 10 + (str[i + 4] - '0');
                if (tmp_time > max_time)
                    max_time = tmp_time;
                i = i + 4;
                continue;
            }
            i++;
        }
        return max_time;
    }

    // 执行动作组1次
    // 参数是动作组序号
    void do_group_once(int group_num)
    {
        delay_ms(10);
        // 将uart_receive_buf清零
        memset(uart_receive_buf, 0, sizeof(uart_receive_buf));
        // 从存储芯片中读取第group_num个动作组
        w25x_read((u8 *)uart_receive_buf, group_num * ACTION_SIZE, ACTION_SIZE);
        // 获取最大的组时间
        action_time = getMaxTime(uart_receive_buf);

        // 把读取出来的动作组传递到parse_action执行
        parse_action(uart_receive_buf);
    }

    // 动作组批量执行
    void app_action_run(void)
    {
        // 通过判断舵机是否全部执行完毕 并且是执行动作组group_do_ok尚未结束的情况下进入处理
        static long long systick_ms_bak = 0;
        if (group_do_ok == 0)
        {
            if (millis() - systick_ms_bak > action_time)
            {
                systick_ms_bak = millis();
                if (group_num_cnt != 0 && do_group_cnt == 0)
                {
                    group_do_ok = 1;
                    uart1_send_str("@GroupDone!");
                    return;
                }
                // 调用do_start_index个动作
                do_group_once(do_start_index);

                if (group_num_start < group_num_end)
                {
                    if (do_start_index == group_num_end)
                    {
                        do_start_index = group_num_start;
                        if (group_num_cnt != 0)
                        {
                            do_group_cnt--;
                        }
                        return;
                    }
                    do_start_index++;
                }
                else
                {
                    if (do_start_index == group_num_end)
                    {
                        do_start_index = group_num_start;
                        if (group_num_cnt != 0)
                        {
                            do_group_cnt--;
                        }
                        return;
                    }
                    do_start_index--;
                }
            }
        }
    }

    int kinematics_move(float x, float y, float z, int time)
    {
        int i, min = 0, flag = 0;

        if (y < 0)
            return 0;

        // 寻找最佳角度
        flag = 0;
        for (i = 0; i >= -135; i--)
        {
            if (0 == kinematics_analysis(x, y, z, i, &kinematics))
            {

                if (i < min)
                    min = i;
                flag = 1;
            }
        }

        // 用3号舵机与水平最大的夹角作为最佳值
        if (flag)
        {
            kinematics_analysis(x, y, z, min, &kinematics);
            kinematics.servo_pwm[3] = 3000 - kinematics.servo_pwm[3];
            sprintf((char *)cmd_return, "{#000P%04dT%04d!#001P%04dT%04d!#002P%04dT%04d!#003P%04dT%04d!}", kinematics.servo_pwm[0], time,
                    kinematics.servo_pwm[1], time,
                    kinematics.servo_pwm[2], time,
                    kinematics.servo_pwm[3], time);
            parse_action(cmd_return);
            return 1;
        }

        return 0;
    }

    void set_servo(int index, int pwm, int time)
    {
        if (index == 3)
        {
            pwm = 3000 - pwm;
        }
        sprintf((char *)cmd_return, "#%03dP%04dT%04d!", index, pwm, time);
        parse_action(cmd_return);
    }

    // 把eeprom_info写入到W25Q64_INFO_ADDR_SAVE_STR位置
    void rewrite_eeprom(void)
    {
        w25x_erase_sector(W25Q64_INFO_ADDR_SAVE_STR / 4096);
        w25x_writeS((u8 *)(&eeprom_info), W25Q64_INFO_ADDR_SAVE_STR, sizeof(eeprom_info_t));
    }
