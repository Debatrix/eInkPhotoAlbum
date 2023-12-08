#include "EInk.h"

/******************************************************************************
functions:	Hardware underlying interface
******************************************************************************/

void GPIO_Config(void)
{
    pinMode(EPD_BUSY_PIN, INPUT);
    pinMode(EPD_RST_PIN, OUTPUT);
    pinMode(EPD_DC_PIN, OUTPUT);

    pinMode(EPD_SCK_PIN, OUTPUT);
    pinMode(EPD_MOSI_PIN, OUTPUT);
    pinMode(EPD_CS_PIN, OUTPUT);

    digitalWrite(EPD_CS_PIN, HIGH);
    digitalWrite(EPD_SCK_PIN, LOW);
}

/** Module Initialize, the BCM2835 library and initialize the pins, SPI protocol**/
UBYTE DEV_Module_Init(void)
{
    // gpio
    GPIO_Config();

    // serial printf
    Serial.begin(115200);

    // spi
    // SPI.setDataMode(SPI_MODE0);
    // SPI.setBitOrder(MSBFIRST);
    // SPI.setClockDivider(SPI_CLOCK_DIV4);
    // SPI.begin();

    return 0;
}

/** SPI read and write**/
void DEV_SPI_WriteByte(UBYTE data)
{
    // SPI.beginTransaction(spi_settings);
    digitalWrite(EPD_CS_PIN, GPIO_PIN_RESET);

    for (int i = 0; i < 8; i++)
    {
        if ((data & 0x80) == 0)
            digitalWrite(EPD_MOSI_PIN, GPIO_PIN_RESET);
        else
            digitalWrite(EPD_MOSI_PIN, GPIO_PIN_SET);

        data <<= 1;
        digitalWrite(EPD_SCK_PIN, GPIO_PIN_SET);
        digitalWrite(EPD_SCK_PIN, GPIO_PIN_RESET);
    }

    // SPI.transfer(data);
    digitalWrite(EPD_CS_PIN, GPIO_PIN_SET);
    // SPI.endTransaction();
}

/******************************************************************************
functions:	5.65inch e-paper
******************************************************************************/

/** Software reset **/
static void EPD_5IN65F_Reset(void)
{
    DEV_Digital_Write(EPD_RST_PIN, 1);
    DEV_Delay_ms(200);
    DEV_Digital_Write(EPD_RST_PIN, 0);
    DEV_Delay_ms(1);
    DEV_Digital_Write(EPD_RST_PIN, 1);
    DEV_Delay_ms(200);
}

/** Send Command **/
static void EPD_5IN65F_SendCommand(UBYTE Reg)
{
    DEV_Digital_Write(EPD_DC_PIN, 0);
    DEV_Digital_Write(EPD_CS_PIN, 0);
    DEV_SPI_WriteByte(Reg);
    DEV_Digital_Write(EPD_CS_PIN, 1);
}

/** Send Data **/
void EPD_5IN65F_SendData(UBYTE Data)
{
    DEV_Digital_Write(EPD_DC_PIN, 1);
    DEV_Digital_Write(EPD_CS_PIN, 0);
    DEV_SPI_WriteByte(Data);
    DEV_Digital_Write(EPD_CS_PIN, 1);
}

static void EPD_5IN65F_BusyHigh(void) // If BUSYN=0 then waiting
{
    while (!(DEV_Digital_Read(EPD_BUSY_PIN)))
        ;
}

static void EPD_5IN65F_BusyLow(void) // If BUSYN=1 then waiting
{
    while (DEV_Digital_Read(EPD_BUSY_PIN))
        ;
}

/** Initialize the e-Paper register **/
void EPD_5IN65F_Init(void)
{
    EPD_5IN65F_Reset();
    EPD_5IN65F_BusyHigh();
    EPD_5IN65F_SendCommand(0x00);
    EPD_5IN65F_SendData(0xEF);
    EPD_5IN65F_SendData(0x08);
    EPD_5IN65F_SendCommand(0x01);
    EPD_5IN65F_SendData(0x37);
    EPD_5IN65F_SendData(0x00);
    EPD_5IN65F_SendData(0x23);
    EPD_5IN65F_SendData(0x23);
    EPD_5IN65F_SendCommand(0x03);
    EPD_5IN65F_SendData(0x00);
    EPD_5IN65F_SendCommand(0x06);
    EPD_5IN65F_SendData(0xC7);
    EPD_5IN65F_SendData(0xC7);
    EPD_5IN65F_SendData(0x1D);
    EPD_5IN65F_SendCommand(0x30);
    EPD_5IN65F_SendData(0x3C);
    EPD_5IN65F_SendCommand(0x41);
    EPD_5IN65F_SendData(0x00);
    EPD_5IN65F_SendCommand(0x50);
    EPD_5IN65F_SendData(0x37);
    EPD_5IN65F_SendCommand(0x60);
    EPD_5IN65F_SendData(0x22);
    EPD_5IN65F_SendCommand(0x61);
    EPD_5IN65F_SendData(0x02);
    EPD_5IN65F_SendData(0x58);
    EPD_5IN65F_SendData(0x01);
    EPD_5IN65F_SendData(0xC0);
    EPD_5IN65F_SendCommand(0xE3);
    EPD_5IN65F_SendData(0xAA);

    DEV_Delay_ms(100);
    EPD_5IN65F_SendCommand(0x50);
    EPD_5IN65F_SendData(0x37);
}

/** Clear screen **/
void EPD_5IN65F_Clear(UBYTE color)
{
    EPD_5IN65F_SendCommand(0x61); // Set Resolution setting
    EPD_5IN65F_SendData(0x02);
    EPD_5IN65F_SendData(0x58);
    EPD_5IN65F_SendData(0x01);
    EPD_5IN65F_SendData(0xC0);
    EPD_5IN65F_SendCommand(0x10);
    for (int i = 0; i < EPD_5IN65F_HEIGHT; i++)
    {
        for (int j = 0; j < EPD_5IN65F_WIDTH / 2; j++)
            EPD_5IN65F_SendData((color << 4) | color);
    }
    EPD_5IN65F_SendCommand(0x04); // 0x04
    EPD_5IN65F_BusyHigh();
    EPD_5IN65F_SendCommand(0x12); // 0x12
    EPD_5IN65F_BusyHigh();
    EPD_5IN65F_SendCommand(0x02); // 0x02
    EPD_5IN65F_BusyLow();
    DEV_Delay_ms(500);
}

/** Sends the image buffer in RAM to e-Paper and displays **/
void EPD_5IN65F_Display(UBYTE *image)
{
    UWORD i, j;
    EPD_5IN65F_SendCommand(0x61); // Set Resolution setting
    EPD_5IN65F_SendData(0x02);
    EPD_5IN65F_SendData(0x58);
    EPD_5IN65F_SendData(0x01);
    EPD_5IN65F_SendData(0xC0);
    EPD_5IN65F_SendCommand(0x10);
    for (i = 0; i < EPD_5IN65F_HEIGHT; i++)
    {
        for (j = 0; j < EPD_5IN65F_WIDTH / 2; j++)
        {
            EPD_5IN65F_SendData(image[i * EPD_5IN65F_WIDTH / 2 + j]);
        }
    }
    EPD_5IN65F_SendCommand(0x04); // 0x04
    EPD_5IN65F_BusyHigh();
    EPD_5IN65F_SendCommand(0x12); // 0x12
    EPD_5IN65F_BusyHigh();
    EPD_5IN65F_SendCommand(0x02); // 0x02
    EPD_5IN65F_BusyLow();
    DEV_Delay_ms(200);
}

void EPD_5IN65F_Display_begin()
{
    UWORD i, j;
    EPD_5IN65F_SendCommand(0x61); // Set Resolution setting
    EPD_5IN65F_SendData(0x02);
    EPD_5IN65F_SendData(0x58);
    EPD_5IN65F_SendData(0x01);
    EPD_5IN65F_SendData(0xC0);
    EPD_5IN65F_SendCommand(0x10);
    DEV_Delay_ms(200);
}

void EPD_5IN65F_Display_end()
{
    EPD_5IN65F_SendCommand(0x04); // 0x04
    EPD_5IN65F_BusyHigh();
    EPD_5IN65F_SendCommand(0x12); // 0x12
    EPD_5IN65F_BusyHigh();
    EPD_5IN65F_SendCommand(0x02); // 0x02
    EPD_5IN65F_BusyLow();
    DEV_Delay_ms(200);
}

/** Enter sleep mode **/
void EPD_5IN65F_Sleep(void)
{
    DEV_Delay_ms(100);
    EPD_5IN65F_SendCommand(0x07);
    EPD_5IN65F_SendData(0xA5);
    DEV_Delay_ms(100);
    DEV_Digital_Write(EPD_RST_PIN, 0); // Reset
}