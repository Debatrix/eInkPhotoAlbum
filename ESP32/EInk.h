/******************************************************************************
Hardware underlying interface
******************************************************************************/
#ifndef _DEV_CONFIG_H_
#define _DEV_CONFIG_H_

#include <Arduino.h>
#include <stdint.h>
#include <stdio.h>

/**
 * data
 **/
#define UBYTE uint8_t
#define UWORD uint16_t
#define UDOUBLE uint32_t

/**
 * GPIO config
 **/
#define EPD_SCK_PIN 13
#define EPD_MOSI_PIN 14
#define EPD_CS_PIN 15
#define EPD_RST_PIN 26
#define EPD_DC_PIN 27
#define EPD_BUSY_PIN 25

#define GPIO_PIN_SET 1
#define GPIO_PIN_RESET 0

/**
 * GPIO read and write
 **/
#define DEV_Digital_Write(_pin, _value) digitalWrite(_pin, _value == 0 ? LOW : HIGH)
#define DEV_Digital_Read(_pin) digitalRead(_pin)

/**
 * delay x ms
 **/
#define DEV_Delay_ms(__xms) delay(__xms)
/*---------------------------------------------------------------------------*/
UBYTE DEV_Module_Init(void);
void DEV_SPI_WriteByte(UBYTE data);

#endif

/******************************************************************************
5.65inch e-paper
******************************************************************************/

#ifndef __EPD_5IN65F_H__
#define __EPD_5IN65F_H__

// Color Index
#define EPD_5IN65F_BLACK 0x0  /// 000
#define EPD_5IN65F_WHITE 0x1  ///	001
#define EPD_5IN65F_GREEN 0x2  ///	010
#define EPD_5IN65F_BLUE 0x3   ///	011
#define EPD_5IN65F_RED 0x4    ///	100
#define EPD_5IN65F_YELLOW 0x5 ///	101
#define EPD_5IN65F_ORANGE 0x6 ///	110
#define EPD_5IN65F_CLEAN 0x7  ///	111   unavailable  Afterimage

// Resolution
#define EPD_5IN65F_WIDTH 600
#define EPD_5IN65F_HEIGHT 448

// Functions
void EPD_5IN65F_Init(void);
void EPD_5IN65F_Clear(UBYTE color);
void EPD_5IN65F_Display(UBYTE *image);
void EPD_5IN65F_Display_begin(void);
void EPD_5IN65F_SendData(UBYTE Data);
void EPD_5IN65F_Display_end(void);
void EPD_5IN65F_Sleep(void);

#endif